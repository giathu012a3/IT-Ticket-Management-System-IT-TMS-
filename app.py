from flask import Flask
from config import Config
from extensions import db, login_manager
from models import User, Notification
from flask_login import current_user

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Context Processor for Notifications (Global)
    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated:
            notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            return dict(notifications=notifications, unread_count=unread_count)
        return dict(notifications=[], unread_count=0)

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.leader import leader_bp
    from routes.staff import staff_bp
    from routes.admin import admin_bp
    from routes.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(leader_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
