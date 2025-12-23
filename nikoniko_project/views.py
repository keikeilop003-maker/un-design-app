from flask import Blueprint, render_template, request, redirect, url_for, session
from collections import defaultdict

# Blueprintの定義
bp = Blueprint('un_design', __name__, url_prefix='/un_design')

# --- ダミーデータモデル（データベースの代わり） ---
# ※サーバーを再起動するとリセットされます

class Proposal:
    def __init__(self, id, title, author, target, problem, details, effect, c1, c2, c3, creator_id=None, category=None):
        self.id = id
        self.title = title
        self.author = author
        self.target = target
        self.problem = problem
        self.details = details
        self.effect = effect
        self.cost_pt_1 = int(c1) if c1 else 0
        self.cost_pt_2 = int(c2) if c2 else 0
        self.cost_pt_3 = int(c3) if c3 else 0
        self.votes = defaultdict(int) # グループごとの投票ポイント
        self.target_cost = 1000 # 目標コスト（仮）
        self.creator_id = creator_id # 作成者のID
        self.category = category # 事業カテゴリ
    
    @property
    def costs(self):
        return [
            ("設計・開発", self.cost_pt_1),
            ("運用・維持", self.cost_pt_2),
            ("精神的・肉体的", self.cost_pt_3)
        ]

    @property
    def total_points(self):
        return sum(self.votes.values())

    @property
    def author_group(self):
        # プロジェクトのグループは、作成者のIDから決定する
        return get_group_from_id(self.creator_id)
class Report:
    def __init__(self, id, r_type, env, details):
        self.id = id
        self.report_type = r_type
        self.env_value = env
        self.details = details
        self.status = 'unread' # unread, archived

# 初期データ（サンプル）
proposals_db = [
    Proposal(1, "あえて階段しかない公園", "官公庁", "都市住民", "便利すぎて足腰が弱る", "エレベーターなし、階段のみの立体公園", "運動不足解消と頂上の達成感", 300, 200, 500, '1101', '建設・不動産業'),
    Proposal(2, "全自動ではない家電", "製造業の開発担当", "若者", "愛着がわかない", "手入れが必要なトースター", "道具への愛着と丁寧な暮らし", 200, 300, 100, '1201', '製造業（軽工業）')
]
reports_db = [
    Report(1, "bug", 1200, "ログイン画面の表示が崩れることがあります。"),
    Report(2, "idea", 1350, "わざとロード時間を長くして、期待感を煽るUIはどうでしょう？")
]

# --- ヘルパー関数 ---
def get_group_from_id(voter_id):
    if not voter_id or not voter_id.isdigit(): return None
    vid = int(voter_id)
    if 1100 <= vid <= 1150: return "1組"
    if 1200 <= vid <= 1250: return "2組"
    if 1300 <= vid <= 1350: return "3組"
    if 1400 <= vid <= 1450: return "4組"
    return None

# --- ルーティング ---

@bp.route('/', methods=['GET', 'POST'])
def gate():
    """ログインゲート（ポータル）"""
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        voter_id = request.form.get('voter_id')

        # パスワード設定（本来は環境変数などで管理）
        ADMIN_PASSWORD = "930522"
        USER_PASSWORD = "2525land"

        print(f"Login Attempt: password='{password}', voter_id='{voter_id}'") # デバッグ用ログ

        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            session['voter_id'] = 'ADMIN'
            return redirect(url_for('un_design.admin_feedback'))
        
        elif password == USER_PASSWORD:
            # ID範囲チェック (1101-1440)
            if voter_id and voter_id.isdigit() and 1101 <= int(voter_id) <= 1440:
                session['is_admin'] = False
                session['voter_id'] = voter_id
                session['group'] = get_group_from_id(voter_id)
                return redirect(url_for('un_design.menu'))
            else:
                error = "ID MUST BE BETWEEN 1101 AND 1440"
        
        else:
            error = "ACCESS CODE IS INVALID"

    return render_template('un_design/gate.html', error=error)

@bp.route('/menu')
def menu():
    """メニュー画面"""
    if 'voter_id' not in session:
        return redirect(url_for('un_design.gate'))
    return render_template('un_design/menu.html')

@bp.route('/add', methods=['GET', 'POST'])
def add():
    """新規企画登録"""
    if 'voter_id' not in session:
        return redirect(url_for('un_design.gate'))

    if request.method == 'POST':
        new_id = len(proposals_db) + 1
        title = request.form.get('title')
        # フォームからauthorを取得
        author = request.form.get('author')
        target = request.form.get('target')
        category = request.form.get('category')
        problem = request.form.get('problem')
        details = request.form.get('details')
        effect = request.form.get('effect')
        c1 = request.form.get('cost_pt_1')
        c2 = request.form.get('cost_pt_2')
        c3 = request.form.get('cost_pt_3')
        creator_id = session.get('voter_id')

        new_proposal = Proposal(new_id, title, author, target, problem, details, effect, c1, c2, c3, creator_id, category)
        proposals_db.append(new_proposal)
        
        return redirect(url_for('un_design.index'))

    return render_template('un_design/add.html')

@bp.route('/index')
def index():
    """企画一覧・投票画面"""
    if 'voter_id' not in session:
        return redirect(url_for('un_design.gate'))
    
    has_voted = session.get('has_voted', False)
    
    # 自分のグループが作成した企画のみフィルタリング
    user_group = session.get('group')
    filtered_proposals = [p for p in proposals_db if p.author_group == user_group]

    # コスト合計値の降順でソート
    sorted_proposals = sorted(filtered_proposals, key=lambda p: (p.cost_pt_1 + p.cost_pt_2 + p.cost_pt_3), reverse=True)
    
    return render_template('un_design/index.html', proposals=sorted_proposals, has_voted=has_voted)

@bp.route('/vote_all', methods=['POST'])
def vote_all():
    """一括投票処理"""
    user_group = session.get('group')
    current_user_id = session.get('voter_id')
    
    for p in proposals_db:
        # 自分の企画には投票できない
        if str(p.creator_id) == str(current_user_id):
            continue
            
        points = request.form.get(f'points_{p.id}')
        if points and user_group:
            p.votes[user_group] += int(points)
    
    session['has_voted'] = True
    return redirect(url_for('un_design.result'))

@bp.route('/result')
def result():
    """統計結果画面"""
    if 'voter_id' not in session:
        return redirect(url_for('un_design.gate'))

    user_group = session.get('group')
    
    # 自分のグループが作成した企画のみフィルタリング
    group_proposals = [p for p in proposals_db if p.author_group == user_group]

    # 達成済み企画があるかどうか
    has_achieved = any(p.total_points >= 1000 for p in group_proposals)

    return render_template('un_design/result.html', proposals=group_proposals, has_achieved=has_achieved)

@bp.route('/logout')
def logout():
    """ログアウト"""
    session.clear()
    return redirect(url_for('un_design.gate'))

# --- 管理者・デバッグ用ルート ---

@bp.route('/admin/feedback')
def admin_feedback():
    """管理者用フィードバック画面"""
    if not session.get('is_admin'):
        return redirect(url_for('un_design.gate'))

    # --- 統計データの計算 ---
    # グループごとの投稿数
    posts_by_group = defaultdict(int)
    for p in proposals_db:
        if p.author_group:
            posts_by_group[p.author_group] += 1

    # カテゴリごとの投稿数
    posts_by_category = defaultdict(int)
    for p in proposals_db:
        if p.category:
            posts_by_category[p.category] += 1

    # 目標達成状況
    achieved_count = sum(1 for p in proposals_db if p.total_points >= 1000)
    not_achieved_count = len(proposals_db) - achieved_count
    achievement_status = {'achieved': achieved_count, 'not_achieved': not_achieved_count}

    return render_template('un_design/feedback_admin.html', reports=reports_db, proposals=proposals_db, posts_by_group=posts_by_group, posts_by_category=posts_by_category, achievement_status=achievement_status)

@bp.route('/debug_report', methods=['POST'])
def debug_report():
    """バグ報告・アイデア投稿"""
    r_type = request.form.get('type')
    env = request.form.get('env')
    details = request.form.get('details')
    new_id = len(reports_db) + 1
    reports_db.append(Report(new_id, r_type, env, details))
    return redirect(url_for('un_design.gate'))

@bp.route('/edit_proposal/<int:id>', methods=['GET', 'POST'])
def edit_proposal(id):
    """企画編集（管理者または作成者）"""
    target_p = next((p for p in proposals_db if p.id == id), None)
    if not target_p: # 企画が見つからない場合
        return redirect(url_for('un_design.menu'))

    is_admin = session.get('is_admin')
    current_user_id = session.get('voter_id')

    # 権限チェック: 管理者 または 作成者本人
    if not is_admin and str(target_p.creator_id) != str(current_user_id):
        return redirect(url_for('un_design.gate'))

    if request.method == 'POST':
        target_p.title = request.form.get('title')
        target_p.author = request.form.get('author')
        target_p.target = request.form.get('target')
        target_p.category = request.form.get('category')
        target_p.problem = request.form.get('problem')
        target_p.details = request.form.get('details')
        target_p.effect = request.form.get('effect')
        target_p.cost_pt_1 = int(request.form.get('cost_pt_1', 0))
        target_p.cost_pt_2 = int(request.form.get('cost_pt_2', 0))
        target_p.cost_pt_3 = int(request.form.get('cost_pt_3', 0))
        
        if is_admin:
            return redirect(url_for('un_design.admin_feedback'))
        else:
            return redirect(url_for('un_design.index'))

    return render_template('un_design/edit_proposal.html', p=target_p)

@bp.route('/delete_proposal/<int:id>')
def delete_proposal(id):
    """企画削除（管理者のみ）"""
    if not session.get('is_admin'):
        return redirect(url_for('un_design.gate'))
    
    global proposals_db
    proposals_db = [p for p in proposals_db if p.id != id]
    return redirect(url_for('un_design.admin_feedback'))

@bp.route('/archive_report/<int:id>')
def archive_report(id):
    """レポートのアーカイブ（管理者のみ）"""
    if not session.get('is_admin'):
        return redirect(url_for('un_design.gate'))
    
    target_r = next((r for r in reports_db if r.id == id), None)
    if target_r:
        target_r.status = 'archived'
    return redirect(url_for('un_design.admin_feedback'))

@bp.route('/export_csv/<target>')
def export_csv(target):
    """CSVエクスポート（ダミー）"""
    return redirect(url_for('un_design.admin_feedback'))