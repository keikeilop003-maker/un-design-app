from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Proposal

# Blueprintの定義
un_design_bp = Blueprint('un_design', __name__, template_folder='templates')

# 1. ゲート画面（ログイン処理の修正）
@un_design_bp.route('/gate', methods=['GET', 'POST'])
def gate():
    if request.method == 'POST':
        password = request.form.get('password')
        voter_id = request.form.get('voter_id')
        
        # 管理者パスワードの場合：IDが空でもログイン可能にする
        if password == "inconvenience":
            session['voter_id'] = voter_id if voter_id else "ADMIN_VOTER"
            return redirect(url_for('un_design.menu'))
        
        # 通常のアクセス（ID必須を想定する場合）
        elif password and voter_id:
            session['voter_id'] = voter_id
            return redirect(url_for('un_design.menu'))
            
        else:
            flash("Invalid Access Code or Missing ID.")
            
    return render_template('un_design/gate.html')

# 2. メニュー画面
@un_design_bp.route('/menu')
def menu():
    if 'voter_id' not in session:
        return redirect(url_for('un_design.gate'))
    return render_template('un_design/menu.html')

# 3. 企画投稿画面
@un_design_bp.route('/add', methods=['GET', 'POST'])
def add():
    if 'voter_id' not in session:
        return redirect(url_for('un_design.gate'))
        
    if request.method == 'POST':
        c1 = int(request.form.get('cost_pt_1', 0))
        c2 = int(request.form.get('cost_pt_2', 0))
        c3 = int(request.form.get('cost_pt_3', 0))
        
        new_proposal = Proposal(
            title=request.form.get('title'),
            author=request.form.get('author'),
            target=request.form.get('target'),
            problem=request.form.get('problem'),
            details=request.form.get('details'),
            effect=request.form.get('effect'),
            total_points=(c1 + c2 + c3)
        )
        db.session.add(new_proposal)
        db.session.commit()
        return redirect(url_for('un_design.index'))
    
    return render_template('un_design/add.html')

# 4. 統計結果画面
@un_design_bp.route('/result')
def result():
    proposals = Proposal.query.order_by(Proposal.total_points.desc()).all()
    return render_template('un_design/result.html', proposals=proposals)

# 5. 企画一覧画面
@un_design_bp.route('/index')
def index():
    proposals = Proposal.query.all()
    return render_template('un_design/index.html', proposals=proposals)

# 6. デバッグレポート（BuildError対策）
@un_design_bp.route('/debug_report', methods=['POST'])
def debug_report():
    # 簡易的な受付のみ行いゲートへ戻す
    flash("Report received.")
    return redirect(url_for('un_design.gate'))