from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import os
import pandas as pd
from werkzeug.utils import secure_filename

from app import db
from app.models.profile_analysis import ProfileAnalysis
from app.ml.pipeline import FeaturePipeline
from app.ml.explainer import AIExplainer
from app.ml.trust_engine import TrustEngine
from app.utils.helpers import allowed_file
from app.config import Config
import joblib

batch_bp = Blueprint('batch', __name__, url_prefix='/batch')

@batch_bp.route('/', methods=['GET', 'POST'])
@login_required
def upload_csv():
    """CSV File Upload for automated batch profile trust analysis."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file attached to upload request.', 'danger')
            return redirect(url_for('batch.upload_csv'))

        file = request.files['file']
        if file.filename == '':
            flash('No CSV file selected.', 'warning')
            return redirect(url_for('batch.upload_csv'))

        if file and allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            file.save(upload_path)

            # Process CSV Batch
            try:
                df = pd.read_csv(upload_path)
                model_dir = Config.MODEL_FOLDER
                best_model_path = os.path.join(model_dir, 'best_profile_shield_model.joblib')
                pipeline_path = os.path.join(model_dir, 'feature_pipeline.joblib')

                pipeline = FeaturePipeline()
                pipeline.load(pipeline_path)
                model = joblib.load(best_model_path)['model'] if os.path.exists(best_model_path) else None

                processed_count = 0

                for idx, row in df.iterrows():
                    username = str(row.get('username', f"batch_user_{idx+1}")).replace('@', '')
                    display_name = str(row.get('display_name', username))
                    
                    profile_input = {
                        'username': username,
                        'display_name': display_name,
                        'platform': str(row.get('platform', 'Twitter/X')),
                        'account_age_days': int(row.get('account_age_days', 100)),
                        'followers_count': int(row.get('followers_count', 500)),
                        'following_count': int(row.get('following_count', 400)),
                        'posts_count': int(row.get('posts_count', 200)),
                        'has_profile_pic': int(row.get('has_profile_pic', 1)),
                        'has_bio': int(row.get('has_bio', 1)),
                        'is_verified': int(row.get('is_verified', 0)),
                        'has_url': int(row.get('has_url', 0)),
                        'avg_likes_per_post': float(row.get('avg_likes_per_post', 10.0)),
                        'avg_retweets_per_post': float(row.get('avg_retweets_per_post', 2.0)),
                        'posting_frequency_per_day': float(row.get('posting_frequency_per_day', 1.5)),
                        'bio_length': int(row.get('bio_length', 45)),
                        'username_digits_count': sum(c.isdigit() for c in username)
                    }

                    if model is not None:
                        df_in = pd.DataFrame([profile_input])
                        X_scaled = pipeline.transform(df_in)
                        bot_prob = float(model.predict_proba(X_scaled)[0, 1]) if hasattr(model, 'predict_proba') else 0.5
                    else:
                        bot_prob = 0.5

                    metrics = TrustEngine.calculate_trust_metrics(profile_input, bot_prob)
                    explainer = AIExplainer(model, pipeline)
                    explanation_data = explainer.explain_profile(profile_input)

                    analysis = ProfileAnalysis(
                        username=username,
                        display_name=display_name,
                        platform=profile_input['platform'],
                        user_id=current_user.id,
                        account_age_days=profile_input['account_age_days'],
                        followers_count=profile_input['followers_count'],
                        following_count=profile_input['following_count'],
                        posts_count=profile_input['posts_count'],
                        has_profile_pic=bool(profile_input['has_profile_pic']),
                        has_bio=bool(profile_input['has_bio']),
                        is_verified=bool(profile_input['is_verified']),
                        has_url=bool(profile_input['has_url']),
                        avg_likes_per_post=profile_input['avg_likes_per_post'],
                        avg_retweets_per_post=profile_input['avg_retweets_per_post'],
                        posting_frequency_per_day=profile_input['posting_frequency_per_day'],
                        trust_score=metrics['trust_score'],
                        confidence=metrics['confidence'],
                        risk_level=metrics['risk_level'],
                        recommendation=metrics['recommendation'],
                        health_meter=metrics['health_meter'],
                        behaviour_cluster=metrics['behaviour_cluster'],
                        digital_dna=metrics['digital_dna'],
                        sub_scores=metrics['sub_scores'],
                        trust_radar=metrics['trust_radar'],
                        timeline=metrics['timeline'],
                        heatmap=metrics['heatmap'],
                        shap_importance=explanation_data['shap_importance'],
                        ai_explanation_narrative=explanation_data['narrative']
                    )
                    db.session.add(analysis)
                    processed_count += 1

                db.session.commit()
                flash(f'Batch processing completed successfully! Processed {processed_count} profiles.', 'success')
                return redirect(url_for('batch.history'))

            except Exception as e:
                flash(f'Error processing CSV batch file: {str(e)}', 'danger')
                return redirect(url_for('batch.upload_csv'))

    return render_template('analysis/batch.html')

@batch_bp.route('/history')
@login_required
def history():
    """Displays searchable, filterable, paginated history of all profile scans."""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str).strip()
    risk_filter = request.args.get('risk', '', type=str).strip()
    cluster_filter = request.args.get('cluster', '', type=str).strip()

    query = ProfileAnalysis.query

    if search_query:
        query = query.filter(
            (ProfileAnalysis.username.ilike(f"%{search_query}%")) | 
            (ProfileAnalysis.digital_dna.ilike(f"%{search_query}%"))
        )

    if risk_filter:
        query = query.filter_by(risk_level=risk_filter)

    if cluster_filter:
        query = query.filter_by(behaviour_cluster=cluster_filter)

    pagination = query.order_by(ProfileAnalysis.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template(
        'analysis/history.html',
        pagination=pagination,
        analyses=pagination.items,
        search_query=search_query,
        risk_filter=risk_filter,
        cluster_filter=cluster_filter
    )
