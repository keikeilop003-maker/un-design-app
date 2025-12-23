import os
from flask import Flask, redirect, url_for, request
from models import db
from views import bp as un_design_bp

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = 'un-design-secret'
    
    # 修正ポイント：環境変数 DATABASE_URL があれば使い、なければローカルの SQLite を使う
    # Render環境では自動的に PostgreSQL に繋がります
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        # SQLAlchemyの仕様変更対応（postgres:// を postgresql:// に変換）
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///pavilion.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # --- Blueprintの登録 ---
    app.register_blueprint(un_design_bp)

    # 修正：最初に開くページをポータルサイトに設定
    @app.route('/')
    def root():
        # ポータルサイト（ゲート）へリダイレクト
        return redirect(url_for('un_design.gate'))

    # 救済措置: /gate へのアクセスを /un_design/ へリダイレクト
    # (古いHTMLキャッシュなどが原因で POST /gate が発生した場合の対策)
    @app.route('/gate', methods=['GET', 'POST'])
    def redirect_gate():
        return redirect(url_for('un_design.gate'), code=307)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Renderなどの環境変数PORTがある場合はそれを使用し、なければ5000を使用
    port = int(os.environ.get('PORT', 5000))

    # 外部アクセス用のIPアドレスを取得して表示
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"\n * External Access URL: http://{ip}:{port}\n")
    except:
        pass

    # ネットワーク内の他デバイスからも見れるように 0.0.0.0 を指定
    # デプロイ時はdebug=Falseにします
    app.run(debug=False, host='0.0.0.0', port=port)