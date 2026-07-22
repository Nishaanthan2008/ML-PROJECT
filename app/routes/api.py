from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.models.profile_analysis import ProfileAnalysis
from app.models.ml_model import MLModelRegistry

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/stats/overview')
@login_required
def stats_overview():
    """Returns overview statistics for dashboard charts."""
    total = ProfileAnalysis.query.count()
    low = ProfileAnalysis.query.filter_by(risk_level='Low').count()
    moderate = ProfileAnalysis.query.filter_by(risk_level='Moderate').count()
    high = ProfileAnalysis.query.filter_by(risk_level='High').count()
    critical = ProfileAnalysis.query.filter_by(risk_level='Critical').count()

    clusters = {}
    for c in ['Natural', 'Influencer', 'Business', 'Bot-like', 'Spam', 'Inactive', 'Growing']:
        clusters[c] = ProfileAnalysis.query.filter_by(behaviour_cluster=c).count()

    return jsonify({
        'total': total,
        'risk_distribution': {
            'Low': low,
            'Moderate': moderate,
            'High': high,
            'Critical': critical
        },
        'cluster_distribution': clusters
    })

@api_bp.route('/model/comparison')
@login_required
def model_comparison():
    """Returns comparative metrics for RF, XGB, LR, SVM."""
    active_model = MLModelRegistry.query.filter_by(is_active=True).first()
    if active_model and active_model.all_models_comparison:
        return jsonify(active_model.all_models_comparison)
    return jsonify({})
