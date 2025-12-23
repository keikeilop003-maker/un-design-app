from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 企画データ
class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    # 3つの観点でのコスト（ポイント）
    cost_pt_1 = db.Column(db.Integer, default=0) # 身体的手間
    cost_pt_2 = db.Column(db.Integer, default=0) # 思考の余白
    cost_pt_3 = db.Column(db.Integer, default=0) # 愛着の醸成
    total_points = db.Column(db.Integer, default=0)

# フィードバック（旧 feedback.db の役割を統合）
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20)) # bug, ui, idea
    env_id = db.Column(db.Integer)  # 1100-1450
    details = db.Column(db.Text)