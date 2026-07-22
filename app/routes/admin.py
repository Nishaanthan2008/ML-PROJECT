from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import os
import pandas as pd
from datetime import datetime

from app import db
from app.models.dataset import Dataset
from app.models.ml_model import MLModelRegistry
from app.models.user import User
from app.ml.dataset_generator import generate_synthetic_profile_dataset
from app.ml.trainer import ModelTrainer
from app.utils.decorators import admin_required
from app.config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/datasets', methods=['GET', 'POST'])
@login_required
@admin_required
def datasets():
    """Dataset Manager: Upload new datasets or view existing training data."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No dataset file provided.', 'danger')
            return redirect(url_for('admin.datasets'))

        file = request.files['file']
        if file.filename == '' or not file.filename.endswith('.csv'):
            flash('Please upload a valid CSV file.', 'warning')
            return redirect(url_for('admin.datasets'))

        filename = f"dataset_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(Config.DATASET_FOLDER, filename)
        os.makedirs(Config.DATASET_FOLDER, exist_ok=True)
        file.save(filepath)

        df = pd.read_csv(filepath)
        ds = Dataset(
            filename=filename,
            filepath=filepath,
            description=request.form.get('description', 'Uploaded training dataset'),
            num_rows=len(df),
            num_features=len(df.columns),
            uploaded_by=current_user.id
        )
        db.session.add(ds)
        db.session.commit()

        flash(f'Dataset {filename} uploaded successfully ({len(df)} records).', 'success')
        return redirect(url_for('admin.datasets'))

    all_datasets = Dataset.query.order_by(Dataset.created_at.desc()).all()
    return render_template('admin/dataset_manager.html', datasets=all_datasets)

@admin_bp.route('/models', methods=['GET'])
@login_required
@admin_required
def model_trainer():
    """Model Benchmark & Retraining Dashboard."""
    active_model = MLModelRegistry.query.filter_by(is_active=True).first()
    all_models = MLModelRegistry.query.order_by(MLModelRegistry.created_at.desc()).all()

    return render_template(
        'admin/model_trainer.html',
        active_model=active_model,
        all_models=all_models
    )

@admin_bp.route('/models/retrain', methods=['POST'])
@login_required
@admin_required
def retrain_model():
    """Triggers ML training pipeline across RF, XGB, LR, SVM and auto-selects best model."""
    try:
        # Load latest dataset or generate synthetic
        latest_dataset = Dataset.query.order_by(Dataset.created_at.desc()).first()
        if latest_dataset and os.path.exists(latest_dataset.filepath):
            df = pd.read_csv(latest_dataset.filepath)
        else:
            df = generate_synthetic_profile_dataset(num_samples=1200)

        trainer = ModelTrainer(model_dir=Config.MODEL_FOLDER)
        evaluation_results = trainer.train_and_evaluate_all(df)

        best_name = evaluation_results['best_model_name']
        best_metrics = evaluation_results['best_metrics']
        all_models_eval = evaluation_results['all_models']

        # Deactivate previous active models
        MLModelRegistry.query.update({MLModelRegistry.is_active: False})

        # Save new active model registry record
        new_registry = MLModelRegistry(
            model_name=best_name,
            version=datetime.utcnow().strftime('v%Y%m%d_%H%M'),
            filepath=os.path.join(Config.MODEL_FOLDER, 'best_profile_shield_model.joblib'),
            is_active=True,
            accuracy=best_metrics['accuracy'],
            precision=best_metrics['precision'],
            recall=best_metrics['recall'],
            f1_score=best_metrics['f1_score'],
            roc_auc=best_metrics['roc_auc'],
            confusion_matrix=best_metrics['confusion_matrix'],
            all_models_comparison=all_models_eval
        )

        db.session.add(new_registry)
        db.session.commit()

        flash(f'Model Retraining Complete! Auto-selected best model: {best_name} (F1 Score: {best_metrics["f1_score"]:.4f})', 'success')
    except Exception as e:
        flash(f'Error during model retraining: {str(e)}', 'danger')

    return redirect(url_for('admin.model_trainer'))

@admin_bp.route('/users')
@login_required
@admin_required
def user_manager():
    """Admin User Management page."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/toggle_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_role(user_id):
    """Toggle user role between User and Admin."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own admin role.', 'warning')
        return redirect(url_for('admin.user_manager'))

    user.role = 'user' if user.role == 'admin' else 'admin'
    db.session.commit()
    flash(f'Updated role for {user.username} to {user.role.upper()}.', 'success')
    return redirect(url_for('admin.user_manager'))
