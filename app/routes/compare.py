from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models.profile_analysis import ProfileAnalysis

compare_bp = Blueprint('compare', __name__, url_prefix='/compare')

@compare_bp.route('/', methods=['GET', 'POST'])
@login_required
def compare_profiles():
    """Side-by-side Profile Trust Intelligence Comparison Tool."""
    p1_id = request.args.get('p1', type=int)
    p2_id = request.args.get('p2', type=int)

    all_profiles = ProfileAnalysis.query.order_by(ProfileAnalysis.created_at.desc()).all()

    profile1 = ProfileAnalysis.query.get(p1_id) if p1_id else (all_profiles[0] if len(all_profiles) > 0 else None)
    profile2 = ProfileAnalysis.query.get(p2_id) if p2_id else (all_profiles[1] if len(all_profiles) > 1 else None)

    return render_template(
        'analysis/compare.html',
        all_profiles=all_profiles,
        profile1=profile1,
        profile2=profile2
    )
