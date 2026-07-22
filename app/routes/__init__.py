from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.analysis import analysis_bp
from app.routes.batch import batch_bp
from app.routes.compare import compare_bp
from app.routes.admin import admin_bp
from app.routes.reports import reports_bp
from app.routes.api import api_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'analysis_bp',
    'batch_bp',
    'compare_bp',
    'admin_bp',
    'reports_bp',
    'api_bp'
]
