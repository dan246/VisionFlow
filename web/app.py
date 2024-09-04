from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_cors import CORS

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)  # Enabling CORS for cross-origin requests

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

# Serve the index page
@app.route('/')
def index():
    return render_template('index.html')

# Serve the snapshot UI page
@app.route('/snapshot_ui/<camera_id>')
def snapshot_ui(camera_id):
    return render_template('snapshot_ui.html', camera_id=camera_id)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
