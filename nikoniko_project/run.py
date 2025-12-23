import os
from app_factory import create_app

app = create_app()

if __name__ == '__main__':
    # Renderなどの環境変数PORTがある場合はそれを使用し、なければ5000を使用
    port = int(os.environ.get('PORT', 5000))
    
    # ローカル開発時は debug=True、Renderなどの本番環境では debug=False になるよう自動切替
    is_debug = os.environ.get('RENDER') is None

    # ネットワーク内の他デバイスからも見れるように 0.0.0.0 を指定
    app.run(debug=is_debug, host='0.0.0.0', port=port)