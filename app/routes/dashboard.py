from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models.profile_analysis import ProfileAnalysis
from app.models.ml_model import MLModelRegistry
from app.models.user import User

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main analytics dashboard.

    Regular users see only their own data.
    Admins see global aggregates.
    """
    if current_user.is_admin():
        # ── Admin view: global analytics ──────────────────────────────
        total_analyses = ProfileAnalysis.query.count()
        recent_analyses = (
            ProfileAnalysis.query
            .order_by(ProfileAnalysis.created_at.desc())
            .limit(8).all()
        )
        low_risk      = ProfileAnalysis.query.filter_by(risk_level='Low').count()
        moderate_risk = ProfileAnalysis.query.filter_by(risk_level='Moderate').count()
        high_risk     = ProfileAnalysis.query.filter_by(risk_level='High').count()
        critical_risk = ProfileAnalysis.query.filter_by(risk_level='Critical').count()

        all_scores    = [a.trust_score for a in ProfileAnalysis.query.all()]
        total_users   = User.query.count()

    else:
        # ── Regular user view: own data only ──────────────────────────
        user_q = ProfileAnalysis.query.filter_by(user_id=current_user.id)

        total_analyses = user_q.count()
        recent_analyses = (
            user_q.order_by(ProfileAnalysis.created_at.desc()).limit(8).all()
        )
        low_risk      = user_q.filter_by(risk_level='Low').count()
        moderate_risk = user_q.filter_by(risk_level='Moderate').count()
        high_risk     = user_q.filter_by(risk_level='High').count()
        critical_risk = user_q.filter_by(risk_level='Critical').count()

        all_scores  = [a.trust_score for a in user_q.all()]
        total_users = None   # not shown to regular users

    avg_trust_score = (
        round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0
    )

    active_model = MLModelRegistry.query.filter_by(is_active=True).order_by(MLModelRegistry.created_at.desc()).first()

    return render_template(
        'dashboard/index.html',
        total_analyses=total_analyses,
        recent_analyses=recent_analyses,
        low_risk=low_risk,
        moderate_risk=moderate_risk,
        high_risk=high_risk,
        critical_risk=critical_risk,
        avg_trust_score=avg_trust_score,
        active_model=active_model,
        total_users=total_users,
    )
