from flask import Flask, render_template, request, redirect, url_for, flash, g
import os
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-change-if-needed'  # Flashメッセージ用

DB_PATH = Path(app.root_path) / 'memo.db'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):  # noqa: D401
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


@app.route('/')
def index():
    db = get_db()
    rows = db.execute("SELECT id, body, created_at, updated_at FROM notes ORDER BY id DESC").fetchall()
    return render_template('index.html', notes=rows)


@app.route('/add', methods=['POST'])
def add():
    body = request.form.get('body', '').strip()
    if not body:
        flash('内容を入力してください。', 'error')
    else:
        db = get_db()
        db.execute("INSERT INTO notes(body) VALUES(?)", (body,))
        db.commit()
        flash('メモを追加しました。', 'ok')
    return redirect(url_for('index'))


@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit(note_id: int):
    db = get_db()
    if request.method == 'POST':
        body = request.form.get('body', '').strip()
        if not body:
            flash('内容を入力してください。', 'error')
        else:
            db.execute("UPDATE notes SET body = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (body, note_id))
            db.commit()
            flash('更新しました。', 'ok')
            return redirect(url_for('index'))
    note = db.execute("SELECT id, body FROM notes WHERE id = ?", (note_id,)).fetchone()
    if note is None:
        flash('指定されたメモが存在しません。', 'error')
        return redirect(url_for('index'))
    return render_template('edit.html', note=note)


@app.route('/delete/<int:note_id>', methods=['POST'])
def delete(note_id: int):
    db = get_db()
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    flash('削除しました。', 'ok')
    return redirect(url_for('index'))


@app.cli.command('init-db')
def init_db_command():
    """DB初期化 (テーブル作成)"""
    init_db()
    print('Initialized the database.')


@app.context_processor
def inject_memo_name():
    name = os.environ.get('MEMO_NAME', '').strip()
    # テンプレート側で {{ memo_name }} として利用 (空なら空文字)
    return {'memo_name': name}


if __name__ == '__main__':
    if not DB_PATH.exists():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # Azure App Service (gunicorn など) でインポートされた際にも
    # 初回デプロイ直後にテーブルが無い状態を自動で補うための初期化
    if not DB_PATH.exists():
        try:
            init_db()
        except Exception:
            # 失敗してもアプリ起動自体は継続 (ログはプラットフォーム側で確認)
            pass
