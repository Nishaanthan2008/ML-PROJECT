from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import joblib
import os
import pandas as pd

from app import db
from app.models.profile_analysis import ProfileAnalysis
from app.ml.pipeline import FeaturePipeline
from app.ml.explainer import AIExplainer
from app.ml.trust_engine import TrustEngine
from app.config import Config

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

PRESET_PROFILES = {
    'genuine_influencer': {
        'username': 'tech_visionary_jane',
        'display_name': 'Jane Doe | Tech Founder',
        'platform': 'Twitter/X',
        'account_age_days': 1450,
        'followers_count': 48500,
        'following_count': 620,
        'posts_count': 3200,
        'has_profile_pic': True,
        'has_bio': True,
        'is_verified': True,
        'has_url': True,
        'avg_likes_per_post': 450.0,
        'avg_retweets_per_post': 85.0,
        'posting_frequency_per_day': 3.5,
        'bio_length': 120,
        'username_digits_count': 0
    },
    'bot_network': {
        'username': 'crypto_wealth_874921',
        'display_name': 'Crypto Wealth Bot',
        'platform': 'Twitter/X',
        'account_age_days': 22,
        'followers_count': 140,
        'following_count': 4890,
        'posts_count': 1850,
        'has_profile_pic': False,
        'has_bio': True,
        'is_verified': False,
        'has_url': True,
        'avg_likes_per_post': 0.2,
        'avg_retweets_per_post': 0.05,
        'posting_frequency_per_day': 84.0,
        'bio_length': 25,
        'username_digits_count': 6
    },
    'inorganic_growth': {
        'username': 'viral_trends_daily99',
        'display_name': 'Daily Viral Content',
        'platform': 'Twitter/X',
        'account_age_days': 45,
        'followers_count': 28900,
        'following_count': 4950,
        'posts_count': 18,
        'has_profile_pic': True,
        'has_bio': False,
        'is_verified': False,
        'has_url': False,
        'avg_likes_per_post': 1.5,
        'avg_retweets_per_post': 0.1,
        'posting_frequency_per_day': 0.4,
        'bio_length': 0,
        'username_digits_count': 2
    },
    'dormant_suspicious': {
        'username': 'shadow_user_7714',
        'display_name': 'User 7714',
        'platform': 'Twitter/X',
        'account_age_days': 380,
        'followers_count': 5,
        'following_count': 850,
        'posts_count': 1,
        'has_profile_pic': False,
        'has_bio': False,
        'is_verified': False,
        'has_url': False,
        'avg_likes_per_post': 0.0,
        'avg_retweets_per_post': 0.0,
        'posting_frequency_per_day': 0.0,
        'bio_length': 0,
        'username_digits_count': 4
    }
}

def load_ml_model_and_pipeline():
    """Helper to load persistent joblib ML model and feature scaling pipeline."""
    model_dir = Config.MODEL_FOLDER
    best_model_path = os.path.join(model_dir, 'best_profile_shield_model.joblib')
    pipeline_path = os.path.join(model_dir, 'feature_pipeline.joblib')

    pipeline = FeaturePipeline()
    pipeline.load(pipeline_path)

    if os.path.exists(best_model_path):
        data = joblib.load(best_model_path)
        model = data['model']
        return model, pipeline
    return None, pipeline

@analysis_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_analysis():
    """Renders profile form and handles single AI trust analysis."""
    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username', 'anonymous_user').strip().replace('@', '')
        display_name = request.form.get('display_name', username).strip()
        platform = request.form.get('platform', 'Twitter/X')

        account_age_days = int(request.form.get('account_age_days', 0))
        followers_count = int(request.form.get('followers_count', 0))
        following_count = int(request.form.get('following_count', 0))
        posts_count = int(request.form.get('posts_count', 0))
        
        has_profile_pic = True if request.form.get('has_profile_pic') == '1' else False
        has_bio = True if request.form.get('has_bio') == '1' else False
        is_verified = True if request.form.get('is_verified') == '1' else False
        has_url = True if request.form.get('has_url') == '1' else False
        
        avg_likes_per_post = float(request.form.get('avg_likes_per_post', 0.0))
        avg_retweets_per_post = float(request.form.get('avg_retweets_per_post', 0.0))
        posting_frequency_per_day = float(request.form.get('posting_frequency_per_day', 0.0))
        bio_length = int(request.form.get('bio_length', 50)) if has_bio else 0
        username_digits_count = sum(c.isdigit() for c in username)

        profile_input = {
            'username': username,
            'display_name': display_name,
            'platform': platform,
            'account_age_days': account_age_days,
            'followers_count': followers_count,
            'following_count': following_count,
            'posts_count': posts_count,
            'has_profile_pic': 1 if has_profile_pic else 0,
            'has_bio': 1 if has_bio else 0,
            'is_verified': 1 if is_verified else 0,
            'has_url': 1 if has_url else 0,
            'avg_likes_per_post': avg_likes_per_post,
            'avg_retweets_per_post': avg_retweets_per_post,
            'posting_frequency_per_day': posting_frequency_per_day,
            'bio_length': bio_length,
            'username_digits_count': username_digits_count
        }

        # Predict with trained ML model
        model, pipeline = load_ml_model_and_pipeline()
        
        if model is not None:
            df_in = pd.DataFrame([profile_input])
            X_scaled = pipeline.transform(df_in)
            if hasattr(model, 'predict_proba'):
                bot_prob = float(model.predict_proba(X_scaled)[0, 1])
            else:
                bot_prob = float(model.predict(X_scaled)[0])
        else:
            # Fallback heuristic calculation if model not yet trained
            bot_prob = 0.85 if following_count > followers_count * 3 else 0.15

        # Run Trust Intelligence Engine
        trust_metrics = TrustEngine.calculate_trust_metrics(profile_input, bot_prob)
        
        # Run AI Explainer
        explainer = AIExplainer(model, pipeline)
        explanation_data = explainer.explain_profile(profile_input)

        # Save Analysis to DB
        analysis = ProfileAnalysis(
            username=username,
            display_name=display_name,
            platform=platform,
            user_id=current_user.id,
            account_age_days=account_age_days,
            followers_count=followers_count,
            following_count=following_count,
            posts_count=posts_count,
            has_profile_pic=has_profile_pic,
            has_bio=has_bio,
            is_verified=is_verified,
            has_url=has_url,
            avg_likes_per_post=avg_likes_per_post,
            avg_retweets_per_post=avg_retweets_per_post,
            posting_frequency_per_day=posting_frequency_per_day,
            trust_score=trust_metrics['trust_score'],
            confidence=trust_metrics['confidence'],
            risk_level=trust_metrics['risk_level'],
            recommendation=trust_metrics['recommendation'],
            health_meter=trust_metrics['health_meter'],
            behaviour_cluster=trust_metrics['behaviour_cluster'],
            digital_dna=trust_metrics['digital_dna'],
            sub_scores=trust_metrics['sub_scores'],
            trust_radar=trust_metrics['trust_radar'],
            timeline=trust_metrics['timeline'],
            heatmap=trust_metrics['heatmap'],
            shap_importance=explanation_data['shap_importance'],
            ai_explanation_narrative=explanation_data['narrative']
        )

        db.session.add(analysis)
        db.session.commit()

        flash(f'Trust Intelligence Report generated for @{username}!', 'success')
        return redirect(url_for('analysis.view_report', analysis_id=analysis.id))

    return render_template('analysis/new.html', presets=PRESET_PROFILES)

@analysis_bp.route('/report/<int:analysis_id>')
@login_required
def view_report(analysis_id):
    """Renders complete Trust Intelligence Report view."""
    analysis = ProfileAnalysis.query.get_or_404(analysis_id)
    return render_template('analysis/result.html', analysis=analysis)
