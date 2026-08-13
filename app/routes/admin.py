from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
import os
import pandas as pd
from datetime import datetime

from app import db
from app.models.dataset import Dataset
from app.models.ml_model import MLModelRegistry
from app.models.user import User
from app.models.profile_analysis import ProfileAnalysis
from app.ml.dataset_generator import generate_synthetic_profile_dataset
from app.ml.trainer import ModelTrainer
from app.services.csv_validator import validate_profile_csv
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _dataset_folder():
    return current_app.config['DATASET_FOLDER']


def _model_folder():
    return current_app.config['MODEL_FOLDER']


# ── Dataset Manager ────────────────────────────────────────────────────────

@admin_bp.route('/datasets', methods=['GET', 'POST'])
@login_required
@admin_required
def datasets():
    """Dataset Manager: Upload new CSV datasets or view existing ones."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No dataset file provided.', 'danger')
            return redirect(url_for('admin.datasets'))

        file = request.files['file']
        if file.filename == '' or not file.filename.lower().endswith('.csv'):
            flash('Please upload a valid CSV file.', 'warning')
            return redirect(url_for('admin.datasets'))

        try:
            dataset_dir = _dataset_folder()
            os.makedirs(dataset_dir, exist_ok=True)

            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            safe_name = f"dataset_{timestamp}_{file.filename}"
            filepath  = os.path.join(dataset_dir, safe_name)
            file.save(filepath)

            df = pd.read_csv(filepath)

            # ── CSV Validation ────────────────────────────────────────
            errors = validate_profile_csv(df)
            if errors:
                os.remove(filepath)   # discard the invalid file
                for err in errors:
                    flash(err, 'danger')
                return redirect(url_for('admin.datasets'))

            ds = Dataset(
                filename=safe_name,
                filepath=filepath,
                description=request.form.get('description', 'Uploaded training dataset'),
                num_rows=len(df),
                num_features=len(df.columns),
                uploaded_by=current_user.id,
            )
            db.session.add(ds)
            db.session.commit()

            flash(
                f'Dataset "{safe_name}" uploaded successfully ({len(df):,} rows).',
                'success',
            )

        except Exception as exc:
            db.session.rollback()
            flash(f'Dataset upload failed: {str(exc)}', 'danger')

        return redirect(url_for('admin.datasets'))

    all_datasets = Dataset.query.order_by(Dataset.created_at.desc()).all()
    return render_template('admin/dataset_manager.html', datasets=all_datasets)


from app.ml.trainer import ModelTrainer, SUPPORTED_MODELS, HAS_XGBOOST
import joblib

# ── Model Trainer ──────────────────────────────────────────────────────────

@admin_bp.route('/models', methods=['GET'])
@login_required
@admin_required
def model_trainer():
    """ML Model Benchmark & Retraining Dashboard."""
    active_model = MLModelRegistry.query.filter_by(is_active=True).order_by(MLModelRegistry.created_at.desc()).first()
    all_models   = MLModelRegistry.query.order_by(MLModelRegistry.created_at.desc()).all()
    total_scans  = ProfileAnalysis.query.count()
    total_users  = User.query.count()

    return render_template(
        'admin/model_trainer.html',
        active_model=active_model,
        all_models=all_models,
        total_scans=total_scans,
        total_users=total_users,
        supported_models=SUPPORTED_MODELS,
        has_xgboost=HAS_XGBOOST,
    )


@admin_bp.route('/models/train', methods=['POST'])
@login_required
@admin_required
def train_model():
    """Train a specific selected algorithm."""
    model_type = request.form.get('model_type') or request.form.get('algorithm') or request.form.get('model')
    set_as_prod = request.form.get('set_as_production', '1') == '1'

    if not model_type or model_type not in SUPPORTED_MODELS:
        flash(
            f'Invalid algorithm selection "{model_type}". Supported algorithms: Random Forest, Gradient Boosting, Logistic Regression, XGBoost.',
            'danger',
        )
        return redirect(url_for('admin.model_trainer'))

    try:
        model_dir = _model_folder()
        os.makedirs(model_dir, exist_ok=True)

        latest_dataset = Dataset.query.order_by(Dataset.created_at.desc()).first()
        if latest_dataset and os.path.exists(latest_dataset.filepath):
            df = pd.read_csv(latest_dataset.filepath)
            errors = validate_profile_csv(df)
            if errors:
                for err in errors:
                    flash(err, 'danger')
                return redirect(url_for('admin.model_trainer'))
        else:
            flash(
                'No uploaded dataset found. Generating synthetic training data (1,200 samples).',
                'info',
            )
            df = generate_synthetic_profile_dataset(num_samples=1200)

        trainer = ModelTrainer(model_dir=model_dir)
        res = trainer.train_single_model(df, model_type)

        is_active = set_as_prod
        if is_active:
            MLModelRegistry.query.update({MLModelRegistry.is_active: False}, synchronize_session='fetch')
            db.session.expire_all()
            trainer.save_as_production_model(
                res['model'],
                res['model_name'],
                res['metrics']
            )

        new_registry = MLModelRegistry(
            model_name=res['model_name'],
            algorithm_key=res['algorithm_key'],
            version=datetime.utcnow().strftime('v%Y%m%d_%H%M'),
            filepath=res['filepath'],
            is_active=is_active,
            accuracy=res['metrics'].get('accuracy', 0.0),
            precision=res['metrics'].get('precision', 0.0),
            recall=res['metrics'].get('recall', 0.0),
            f1_score=res['metrics'].get('f1_score', 0.0),
            roc_auc=res['metrics'].get('roc_auc', 0.0),
            confusion_matrix=res['metrics'].get('confusion_matrix', []),
            all_models_comparison={res['model_name']: res['metrics']},
        )
        db.session.add(new_registry)
        db.session.commit()

        status_msg = "Set as Production Model!" if is_active else "Saved to registry."
        flash(
            f'✅ Successfully trained {res["model_name"]}! '
            f'(Accuracy: {res["metrics"]["accuracy"]:.4f}, F1: {res["metrics"]["f1_score"]:.4f}) — {status_msg}',
            'success',
        )

    except Exception as exc:
        db.session.rollback()
        flash(f'Model training failed: {str(exc)}', 'danger')

    return redirect(url_for('admin.model_trainer'))


@admin_bp.route('/models/retrain', methods=['POST'])
@login_required
@admin_required
def retrain_model():
    """Trigger ML training pipeline across RF, XGBoost, GradientBoosting, LR."""
    try:
        model_dir = _model_folder()
        os.makedirs(model_dir, exist_ok=True)

        latest_dataset = Dataset.query.order_by(Dataset.created_at.desc()).first()
        if latest_dataset and os.path.exists(latest_dataset.filepath):
            df = pd.read_csv(latest_dataset.filepath)
            errors = validate_profile_csv(df)
            if errors:
                for err in errors:
                    flash(err, 'danger')
                return redirect(url_for('admin.model_trainer'))
        else:
            flash(
                'No uploaded dataset found. Generating synthetic training data (1,200 samples).',
                'info',
            )
            df = generate_synthetic_profile_dataset(num_samples=1200)

        trainer = ModelTrainer(model_dir=model_dir)
        evaluation_results = trainer.train_and_evaluate_all(df)

        best_name    = evaluation_results['best_model_name']
        best_metrics = evaluation_results['best_metrics']
        all_evals    = evaluation_results['all_models']

        MLModelRegistry.query.update({MLModelRegistry.is_active: False}, synchronize_session='fetch')
        db.session.expire_all()

        new_registry = MLModelRegistry(
            model_name=best_name,
            algorithm_key=best_name.lower().replace(' ', '_'),
            version=datetime.utcnow().strftime('v%Y%m%d_%H%M'),
            filepath=os.path.join(model_dir, 'best_profile_shield_model.joblib'),
            is_active=True,
            accuracy=best_metrics.get('accuracy', 0.0),
            precision=best_metrics.get('precision', 0.0),
            recall=best_metrics.get('recall', 0.0),
            f1_score=best_metrics.get('f1_score', 0.0),
            roc_auc=best_metrics.get('roc_auc', 0.0),
            confusion_matrix=best_metrics.get('confusion_matrix', []),
            all_models_comparison=all_evals,
        )
        db.session.add(new_registry)
        db.session.commit()

        flash(
            f'✅ Benchmark complete! Best model: {best_name} '
            f'(Accuracy: {best_metrics["accuracy"]:.4f}, '
            f'F1: {best_metrics["f1_score"]:.4f})',
            'success',
        )

    except Exception as exc:
        db.session.rollback()
        flash(f'Model retraining failed: {str(exc)}', 'danger')

    return redirect(url_for('admin.model_trainer'))


@admin_bp.route('/models/set_active/<int:model_id>', methods=['POST'])
@login_required
@admin_required
def set_active_model(model_id):
    """Set a specific trained model as active production model."""
    try:
        model_record = MLModelRegistry.query.get_or_404(model_id)
        model_dir = _model_folder()

        model_obj = None
        metrics = {
            'accuracy': model_record.accuracy,
            'precision': model_record.precision,
            'recall': model_record.recall,
            'f1_score': model_record.f1_score,
            'roc_auc': model_record.roc_auc,
            'confusion_matrix': model_record.confusion_matrix,
        }

        if os.path.exists(model_record.filepath):
            loaded = joblib.load(model_record.filepath)
            if isinstance(loaded, dict) and 'model' in loaded:
                model_obj = loaded['model']
            else:
                model_obj = loaded

        if model_obj is None:
            flash(f'Failed to load model file at {model_record.filepath}', 'danger')
            return redirect(url_for('admin.model_trainer'))

        MLModelRegistry.query.update({MLModelRegistry.is_active: False}, synchronize_session='fetch')
        db.session.expire_all()
        model_record.is_active = True

        trainer = ModelTrainer(model_dir=model_dir)
        trainer.save_as_production_model(
            model_obj,
            model_record.model_name,
            metrics,
            all_results=model_record.all_models_comparison
        )

        db.session.commit()
        print(f"[DEBUG] Production model changed to: {model_record.model_name}")

        flash(
            f'✅ Active production model updated to: {model_record.model_name} ({model_record.version})!',
            'success',
        )

    except Exception as exc:
        db.session.rollback()
        flash(f'Failed to set active model: {str(exc)}', 'danger')

    return redirect(url_for('admin.model_trainer'))



# ── User Manager ───────────────────────────────────────────────────────────

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
    """Toggle user role between user and admin."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('admin.user_manager'))

    try:
        user.role = 'user' if user.role == 'admin' else 'admin'
        db.session.commit()
        flash(f'Updated role for {user.username} → {user.role.upper()}.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Role update failed: {str(exc)}', 'danger')

    return redirect(url_for('admin.user_manager'))


# ── Global Analytics (admin dashboard API) ─────────────────────────────────

@admin_bp.route('/analytics')
@login_required
@admin_required
def global_analytics():
    """Returns global analytics JSON for admin dashboard widgets."""
    total_scans   = ProfileAnalysis.query.count()
    total_users   = User.query.count()
    low_risk      = ProfileAnalysis.query.filter_by(risk_level='Low').count()
    moderate_risk = ProfileAnalysis.query.filter_by(risk_level='Moderate').count()
    high_risk     = ProfileAnalysis.query.filter_by(risk_level='High').count()
    critical_risk = ProfileAnalysis.query.filter_by(risk_level='Critical').count()

    all_scores = [a.trust_score for a in ProfileAnalysis.query.all()]
    avg_score  = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

    return jsonify({
        'total_scans':   total_scans,
        'total_users':   total_users,
        'avg_trust':     avg_score,
        'risk_distribution': {
            'low':      low_risk,
            'moderate': moderate_risk,
            'high':     high_risk,
            'critical': critical_risk,
        },
    })
