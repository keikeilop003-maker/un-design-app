from flask import Blueprint, render_template, request, redirect, url_for, session, make_response
from collections import defaultdict
import csv
import io

# Blueprintの定義
bp = Blueprint('un_design', __name__, url_prefix='/un_design')

def safe_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0

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
        self.cost_pt_1 = max(0, safe_int(c1))
        self.cost_pt_2 = max(0, safe_int(c2))
        self.cost_pt_3 = max(0, safe_int(c3))
        self.votes = {} # user_id: points
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
        # 登録者以外のユーザーによるポイントの合計
        return sum(pt for uid, pt in self.votes.items() if str(uid) != str(self.creator_id))

    @property
    def target_cost(self):
        return self.cost_pt_1 + self.cost_pt_2 + self.cost_pt_3

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

# 投票済みユーザーIDを管理（サーバー再起動でリセット）
voted_user_ids = set()

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
        title = request.form.get('title')
        creator_id = session.get('voter_id')

        # 二重送信防止：同じユーザーが同じタイトルの企画を持っていたらスキップ
        if any(p.title == title and str(p.creator_id) == str(creator_id) for p in proposals_db):
            return redirect(url_for('un_design.index'))

        # ID生成：削除機能に対応するため、現在の最大ID+1を使用
        new_id = (max(p.id for p in proposals_db) if proposals_db else 0) + 1

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

        new_proposal = Proposal(new_id, title, author, target, problem, details, effect, c1, c2, c3, creator_id, category)
        proposals_db.append(new_proposal)
        
        return redirect(url_for('un_design.index'))

    return render_template('un_design/add.html')

@bp.route('/index')
def index():
    """企画一覧・投票画面"""
    if 'voter_id' not in session:
        return redirect(url_for('un_design.gate'))
    
    current_user_id = session.get('voter_id')
    has_voted = session.get('has_voted', False) or (current_user_id in voted_user_ids)
    
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
    
    # 重複投票防止
    if current_user_id in voted_user_ids:
        return redirect(url_for('un_design.result'))

    # 投票内容の一時保存と合計チェック
    vote_updates = []
    total_vote_points = 0

    for p in proposals_db:
        # 自分の企画には投票できない
        if str(p.creator_id) == str(current_user_id):
            continue
            
        points = request.form.get(f'points_{p.id}')
        if points and user_group:
            pt = safe_int(points)
            if pt > 0:
                vote_updates.append((p, pt))
                total_vote_points += pt
    
    # 合計が1000を超えていないか確認（不正リクエスト対策）
    if total_vote_points <= 1000:
        for p, pt in vote_updates:
            p.votes[current_user_id] = pt
    
    voted_user_ids.add(current_user_id)
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
    has_achieved = any(p.total_points >= p.target_cost for p in group_proposals)

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

    # グループごとの投票数
    votes_by_group = defaultdict(int)
    for p in proposals_db:
        for uid, points in p.votes.items():
            grp = get_group_from_id(str(uid))
            if grp:
                votes_by_group[grp] += points

    # 目標達成状況
    achieved_count = sum(1 for p in proposals_db if p.total_points >= p.target_cost)
    not_achieved_count = len(proposals_db) - achieved_count
    achievement_status = {'achieved': achieved_count, 'not_achieved': not_achieved_count}

    return render_template('un_design/feedback_admin.html', reports=reports_db, proposals=proposals_db, posts_by_group=posts_by_group, posts_by_category=posts_by_category, votes_by_group=votes_by_group, achievement_status=achievement_status)

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
        target_p.cost_pt_1 = max(0, safe_int(request.form.get('cost_pt_1')))
        target_p.cost_pt_2 = max(0, safe_int(request.form.get('cost_pt_2')))
        target_p.cost_pt_3 = max(0, safe_int(request.form.get('cost_pt_3')))
        
        if is_admin:
            return redirect(url_for('un_design.admin_feedback'))
        else:
            return redirect(url_for('un_design.index'))

    return render_template('un_design/edit_proposal.html', p=target_p)

@bp.route('/delete_proposal/<int:id>')
def delete_proposal(id):
    """企画削除（管理者または作成者本人）"""
    global proposals_db
    target_p = next((p for p in proposals_db if p.id == id), None)
    if not target_p:
        return redirect(url_for('un_design.index'))

    is_admin = session.get('is_admin')
    current_user_id = session.get('voter_id')

    # 権限チェック: 管理者 または 作成者本人
    if not is_admin and str(target_p.creator_id) != str(current_user_id):
        return redirect(url_for('un_design.gate'))
    
    proposals_db = [p for p in proposals_db if p.id != id]
    
    if is_admin:
        return redirect(url_for('un_design.admin_feedback'))
    else:
        return redirect(url_for('un_design.index'))

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
    """CSVエクスポート"""
    if not session.get('is_admin'):
        return redirect(url_for('un_design.gate'))

    si = io.StringIO()
    writer = csv.writer(si)

    if target == 'proposals':
        filename = 'proposals.csv'
        writer.writerow(['ID', 'Title', 'Author', 'Target', 'Category', 'Problem', 'Details', 'Effect', 'Cost_Dev', 'Cost_Ops', 'Cost_Health', 'Total_Points', 'Creator_ID'])
        for p in proposals_db:
            writer.writerow([
                p.id, p.title, p.author, p.target, p.category, 
                p.problem, p.details, p.effect, 
                p.cost_pt_1, p.cost_pt_2, p.cost_pt_3, 
                p.total_points, p.creator_id
            ])
    elif target == 'reports':
        filename = 'reports.csv'
        writer.writerow(['ID', 'Type', 'Env', 'Details', 'Status'])
        for r in reports_db:
            writer.writerow([r.id, r.report_type, r.env_value, r.details, r.status])
    else:
        return redirect(url_for('un_design.admin_feedback'))

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output