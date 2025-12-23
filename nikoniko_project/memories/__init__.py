# memories/__init__.py

# memories/routes.py で定義されている memories_bp をインポートします
from .routes import memories_bp

# これにより、外部（app_factory.py）から 
# 「from memories import memories_bp」と書くだけで呼び出せるようになります