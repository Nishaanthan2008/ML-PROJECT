import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from app.config import config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

def create_app(config_name='default'):
    """Application Factory Function."""
    app = Flask(__name__)
    
    # Resolve config_name if 'default' or invalid string is passed
    if config_name not in config:
        config_name = os.environ.get('FLASK_ENV', os.environ.get('FLASK_CONFIG', 'development'))
    if config_name not in config:
        config_name = 'development'
        
    app.config.from_object(config[config_name])

    # Ensure Instance & Data Folders Exist (safe for read-only serverless environments)
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['DATASET_FOLDER'], exist_ok=True)
        os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)
        os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)
    except Exception as e:
        app.logger.warning(f"Could not create local storage directories: {e}")

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register User Loader for Flask-Login
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.analysis import analysis_bp
    from app.routes.batch import batch_bp
    from app.routes.compare import compare_bp
    from app.routes.admin import admin_bp
    from app.routes.reports import reports_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(batch_bp)
    app.register_blueprint(compare_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    # Register Jinja Context Utilities
    from app.utils.helpers import format_number
    @app.template_filter('format_num')
    def format_num_filter(val):
        return format_number(val)

    with app.app_context():
        db.create_all()
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'ml_models' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('ml_models')]
                if 'algorithm_key' not in columns:
                    db.session.execute(text("ALTER TABLE ml_models ADD COLUMN algorithm_key VARCHAR(50)"))
                    db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"Schema update check skipped: {e}")

    return app
