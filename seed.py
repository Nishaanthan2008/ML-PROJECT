import os
import sys
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.profile_analysis import ProfileAnalysis
from app.models.dataset import Dataset
from app.models.ml_model import MLModelRegistry

from app.ml.dataset_generator import generate_synthetic_profile_dataset
from app.ml.trainer import ModelTrainer
from app.ml.explainer import AIExplainer
from app.ml.trust_engine import TrustEngine
import pandas as pd

def seed_database():
    app = create_app('development')
    
    with app.app_context():
        print("--> Initializing Database Tables...")
        db.drop_all()
        db.create_all()

        print("--> Creating Default Users...")
        admin = User(username='admin', email='admin@profileshield.ai', role='admin')
        admin.set_password('Admin123!')
        
        analyst = User(username='analyst', email='analyst@profileshield.ai', role='user')
        analyst.set_password('Analyst123!')

        db.session.add(admin)
        db.session.add(analyst)
        db.session.commit()
        print("    Admin user: admin@profileshield.ai / Admin123!")
        print("    Analyst user: analyst@profileshield.ai / Analyst123!")

        print("--> Generating Synthetic Profile Dataset (1,200 samples)...")
        df = generate_synthetic_profile_dataset(num_samples=1200)
        dataset_path = os.path.join(app.config['DATASET_FOLDER'], 'synthetic_corpus_v1.csv')
        df.to_csv(dataset_path, index=False)

        ds_record = Dataset(
            filename='synthetic_corpus_v1.csv',
            filepath=dataset_path,
            description='Initial Synthetic Social Profile Corpus (1200 records)',
            num_rows=len(df),
            num_features=len(df.columns),
            uploaded_by=admin.id
        )
        db.session.add(ds_record)
        db.session.commit()

        print("--> Training ML Model Suite (RF, XGBoost, Logistic Regression, SVM)...")
        trainer = ModelTrainer(model_dir=app.config['MODEL_FOLDER'])
        eval_output = trainer.train_and_evaluate_all(df)

        best_name = eval_output['best_model_name']
        best_metrics = eval_output['best_metrics']
        all_evals = eval_output['all_models']

        print(f"    Best model trained: {best_name} (F1 Score: {best_metrics['f1_score']:.4f}, ROC AUC: {best_metrics['roc_auc']:.4f})")

        model_registry = MLModelRegistry(
            model_name=best_name,
            version='v1.0.0',
            filepath=os.path.join(app.config['MODEL_FOLDER'], 'best_profile_shield_model.joblib'),
            is_active=True,
            accuracy=best_metrics['accuracy'],
            precision=best_metrics['precision'],
            recall=best_metrics['recall'],
            f1_score=best_metrics['f1_score'],
            roc_auc=best_metrics['roc_auc'],
            confusion_matrix=best_metrics['confusion_matrix'],
            all_models_comparison=all_evals
        )
        db.session.add(model_registry)
        db.session.commit()

        print("--> Seeding Initial Sample Profile Assessments...")
        sample_profiles = [
            {
                'username': 'tech_lead_sarah',
                'display_name': 'Sarah Jenkins | AI Architect',
                'platform': 'Twitter/X',
                'account_age_days': 1650,
                'followers_count': 52100,
                'following_count': 780,
                'posts_count': 4100,
                'has_profile_pic': 1,
                'has_bio': 1,
                'is_verified': 1,
                'has_url': 1,
                'avg_likes_per_post': 340.0,
                'avg_retweets_per_post': 45.0,
                'posting_frequency_per_day': 2.8,
                'bio_length': 140,
                'username_digits_count': 0,
                'bot_prob': 0.03
            },
            {
                'username': 'crypto_bot_98241',
                'display_name': 'Crypto Wealth Bot 98241',
                'platform': 'Twitter/X',
                'account_age_days': 14,
                'followers_count': 85,
                'following_count': 4920,
                'posts_count': 2400,
                'has_profile_pic': 0,
                'has_bio': 1,
                'is_verified': 0,
                'has_url': 1,
                'avg_likes_per_post': 0.1,
                'avg_retweets_per_post': 0.02,
                'posting_frequency_per_day': 95.0,
                'bio_length': 20,
                'username_digits_count': 5,
                'bot_prob': 0.98
            },
            {
                'username': 'inorganic_growth_daily',
                'display_name': 'Viral Daily Memes',
                'platform': 'Instagram',
                'account_age_days': 35,
                'followers_count': 32400,
                'following_count': 4800,
                'posts_count': 12,
                'has_profile_pic': 1,
                'has_bio': 0,
                'is_verified': 0,
                'has_url': 0,
                'avg_likes_per_post': 2.4,
                'avg_retweets_per_post': 0.2,
                'posting_frequency_per_day': 0.3,
                'bio_length': 0,
                'username_digits_count': 0,
                'bot_prob': 0.72
            },
            {
                'username': 'abandoned_ghost_331',
                'display_name': 'User 331',
                'platform': 'Twitter/X',
                'account_age_days': 410,
                'followers_count': 2,
                'following_count': 640,
                'posts_count': 1,
                'has_profile_pic': 0,
                'has_bio': 0,
                'is_verified': 0,
                'has_url': 0,
                'avg_likes_per_post': 0.0,
                'avg_retweets_per_post': 0.0,
                'posting_frequency_per_day': 0.0,
                'bio_length': 0,
                'username_digits_count': 3,
                'bot_prob': 0.88
            }
        ]

        explainer = AIExplainer(trainer.best_model, trainer.pipeline)

        for p_in in sample_profiles:
            bot_prob = p_in.pop('bot_prob')
            metrics = TrustEngine.calculate_trust_metrics(p_in, bot_prob)
            exp_data = explainer.explain_profile(p_in)

            analysis = ProfileAnalysis(
                username=p_in['username'],
                display_name=p_in['display_name'],
                platform=p_in['platform'],
                user_id=admin.id,
                account_age_days=p_in['account_age_days'],
                followers_count=p_in['followers_count'],
                following_count=p_in['following_count'],
                posts_count=p_in['posts_count'],
                has_profile_pic=bool(p_in['has_profile_pic']),
                has_bio=bool(p_in['has_bio']),
                is_verified=bool(p_in['is_verified']),
                has_url=bool(p_in['has_url']),
                avg_likes_per_post=p_in['avg_likes_per_post'],
                avg_retweets_per_post=p_in['avg_retweets_per_post'],
                posting_frequency_per_day=p_in['posting_frequency_per_day'],
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
                shap_importance=exp_data['shap_importance'],
                ai_explanation_narrative=exp_data['narrative']
            )
            db.session.add(analysis)

        db.session.commit()
        print("--> Database Seeding Complete!")

if __name__ == '__main__':
    seed_database()
