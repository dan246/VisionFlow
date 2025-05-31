# filepath: VisionFlow/web/extensions.py

"""
extensions.py
集中管理與初始化 Flask 擴充套件 (Extension)，
包含 SQLAlchemy、Flask-Migrate、Flask-Login 等物件實例化。
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# -------------------------------------------------------------------
# 1. 建立 SQLAlchemy, Migrate, LoginManager 等擴充套件物件
#    這裡不傳入 app，改由 create_app() 中呼叫 init_app() 進行初始化
# -------------------------------------------------------------------

# 建立 SQLAlchemy 實例，用於 ORM 與資料庫操作
db = SQLAlchemy()

# 建立 Migrate 實例，用於資料庫遷移 (使用 Flask-Migrate)
migrate = Migrate()

# 建立 LoginManager 實例，用於使用者登入管理 (使用 Flask-Login)
login_manager = LoginManager()
# 可依需求設定一些參數 (可選)
# 例如：login_manager.login_view = 'auth.login'
#       login_manager.login_message = '請先登入才能存取此頁面'
