from app import app as application  # Azure App Service が参照する WSGI 変数名

if __name__ == "__main__":
	# ローカルテスト用 (任意)
	application.run(host="0.0.0.0", port=5000)
