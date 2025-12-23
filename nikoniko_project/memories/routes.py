from flask import Blueprint, render_template

# Blueprintの定義
# 名前を 'memories' に設定し、app_factory.py で登録された prefix (/memories) を使用します
memories_bp = Blueprint('memories', __name__)

@memories_bp.route('/')
def index():
    # templates/memories/index.html を表示します
    # ここに作品の解説や、クジャクヤママユの画像データなどを渡すことも可能です
    return render_template('memories/index.html')

# 今後、感想投稿機能などを追加する場合は、ここに @memories_bp.route('/comment') などを作ります