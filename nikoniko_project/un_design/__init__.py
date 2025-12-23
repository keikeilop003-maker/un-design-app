# core/__init__.py

# routes.py で定義した Blueprint インスタンスをインポートします
from .routes import un_design_bp

# 他のモジュールから core を参照したときに、
# un_design_bp が直接見えるようにします