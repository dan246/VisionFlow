from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import and register blueprints
from routes.auth_routes import auth_bp
from routes.camera_routes import camera_bp
from routes.notification_routes import notification_bp
from routes.line_token_routes import line_token_bp
from routes.email_recipient_routes import email_recipient_bp

app.register_blueprint(auth_bp)
app.register_blueprint(camera_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(line_token_bp)
app.register_blueprint(email_recipient_bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
