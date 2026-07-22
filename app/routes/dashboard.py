from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models.profile_analysis import ProfileAnalysis
from app.models.ml_model import MLModelRegistry

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main modern analytics dashboard overview."""
    total_analyses = ProfileAnalysis.query.count()
    recent_analyses = ProfileAnalysis.query.order_by(ProfileAnalysis.created_at.desc()).limit(8).all()
    
    # Calculate Risk Distributions
    low_risk = ProfileAnalysis.query.filter_by(risk_level='Low').count()
    moderate_risk = ProfileAnalysis.query.filter_by(risk_level='Moderate').count()
    high_risk = ProfileAnalysis.query.filter_by(risk_level='High').count()
    critical_risk = ProfileAnalysis.query.filter_by(risk_level='Critical').count()

    # Average Trust Score
    all_scores = [a.trust_score for a in ProfileAnalysis.query.all()]
    avg_trust_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

    # Active Model Metrics
    active_model = MLModelRegistry.query.filter_by(is_active=True).first()

    return render_template(
        'dashboard/index.html',
        total_analyses=total_analyses,
        recent_analyses=recent_analyses,
        low_risk=low_risk,
        moderate_risk=moderate_risk,
        high_risk=high_risk,
        critical_risk=critical_risk,
        avg_trust_score=avg_trust_score,
        active_model=active_model
    )
