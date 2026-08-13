import os
import sys
import joblib
from datetime import datetime

# Set up project root in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import create_app, db
from app.models.user import User
from app.models.ml_model import MLModelRegistry
from app.ml.trainer import ModelTrainer, SUPPORTED_MODELS
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

def test_model_selection_flow():
    app = create_app('development')
    with app.app_context():
        print("==================================================================")
        print("   STARTING AUTOMATED VERIFICATION FOR MODEL SELECTION FLOW")
        print("==================================================================")

        client = app.test_client()

        # Login as admin user
        login_res = client.post('/auth/login', data={
            'email': 'admin@profileshield.ai',
            'password': 'Admin123!'
        }, follow_redirects=True)
        assert login_res.status_code == 200, "Admin login failed"
        print("✅ Admin authenticated successfully.")

        # Test 1: Train Gradient Boosting & Set as Production
        print("\n--- TEST 1: Training Gradient Boosting ---")
        gb_res = client.post('/admin/models/train', data={
            'model_type': 'gradient_boosting',
            'set_as_production': '1'
        }, follow_redirects=True)
        assert gb_res.status_code == 200

        db.session.expire_all()
        all_reg = MLModelRegistry.query.all()
        print("DEBUG REGISTRY ROWS:", [(r.id, r.model_name, r.is_active, r.created_at) for r in all_reg])
        active_models = MLModelRegistry.query.filter_by(is_active=True).all()
        print("DEBUG ACTIVE MODELS:", [(r.id, r.model_name, r.is_active, r.created_at) for r in active_models])
        active_model = MLModelRegistry.query.filter_by(is_active=True).order_by(MLModelRegistry.created_at.desc()).first()
        assert active_model is not None, "No active model found"
        assert active_model.model_name == 'Gradient Boosting', f"Expected Gradient Boosting, got {active_model.model_name}"
        
        # Verify joblib file on disk
        model_path = os.path.join(app.config['MODEL_FOLDER'], 'best_profile_shield_model.joblib')
        assert os.path.exists(model_path), "best_profile_shield_model.joblib not found"
        loaded_data = joblib.load(model_path)
        assert loaded_data['model_name'] == 'Gradient Boosting', f"Joblib model name mismatch: {loaded_data['model_name']}"
        assert isinstance(loaded_data['model'], GradientBoostingClassifier), "Loaded model is not GradientBoostingClassifier"
        print(f"✅ Gradient Boosting trained and verified as active production model! ({loaded_data['model']})")

        # Test 2: Train Logistic Regression & Set as Production
        print("\n--- TEST 2: Training Logistic Regression ---")
        lr_res = client.post('/admin/models/train', data={
            'model_type': 'logistic_regression',
            'set_as_production': '1'
        }, follow_redirects=True)
        assert lr_res.status_code == 200

        db.session.expire_all()
        active_model = MLModelRegistry.query.filter_by(is_active=True).order_by(MLModelRegistry.created_at.desc()).first()
        assert active_model.model_name == 'Logistic Regression', f"Expected Logistic Regression, got {active_model.model_name}"
        
        loaded_data = joblib.load(model_path)
        assert loaded_data['model_name'] == 'Logistic Regression'
        assert isinstance(loaded_data['model'], LogisticRegression)
        print(f"✅ Logistic Regression trained and verified as active production model! ({loaded_data['model']})")

        # Test 3: Train XGBoost & Set as Production
        print("\n--- TEST 3: Training XGBoost ---")
        xgb_res = client.post('/admin/models/train', data={
            'model_type': 'xgboost',
            'set_as_production': '1'
        }, follow_redirects=True)
        assert xgb_res.status_code == 200

        db.session.expire_all()
        active_model = MLModelRegistry.query.filter_by(is_active=True).order_by(MLModelRegistry.created_at.desc()).first()
        expected_xgb_name = SUPPORTED_MODELS['xgboost']['name']
        assert active_model.model_name == expected_xgb_name, f"Expected {expected_xgb_name}, got {active_model.model_name}"
        
        loaded_data = joblib.load(model_path)
        assert loaded_data['model_name'] == expected_xgb_name
        print(f"✅ XGBoost trained and verified as active production model! ({loaded_data['model']})")

        # Test 4: Train Random Forest WITHOUT setting as production
        print("\n--- TEST 4: Training Random Forest without auto-activation ---")
        rf_res = client.post('/admin/models/train', data={
            'model_type': 'random_forest',
            'set_as_production': '0'
        }, follow_redirects=True)
        assert rf_res.status_code == 200

        # Verify active model is still XGBoost (or XGBoost fallback)
        db.session.expire_all()
        active_model = MLModelRegistry.query.filter_by(is_active=True).order_by(MLModelRegistry.created_at.desc()).first()
        assert active_model.model_name == expected_xgb_name, f"Active model changed unexpectedly to {active_model.model_name}"

        # Find the newly added Random Forest model record
        rf_record = MLModelRegistry.query.filter_by(model_name='Random Forest').order_by(MLModelRegistry.created_at.desc()).first()
        assert rf_record is not None
        assert not rf_record.is_active
        print("✅ Random Forest trained and saved to registry as archived model (not active).")

        # Test 5: Explicitly Set Random Forest model record as production
        print("\n--- TEST 5: Explicitly setting Random Forest record as production ---")
        set_active_res = client.post(f'/admin/models/set_active/{rf_record.id}', follow_redirects=True)
        assert set_active_res.status_code == 200

        db.session.expire_all()
        active_model = MLModelRegistry.query.filter_by(is_active=True).order_by(MLModelRegistry.created_at.desc()).first()
        assert active_model.id == rf_record.id
        assert active_model.model_name == 'Random Forest'
        
        loaded_data = joblib.load(model_path)
        assert loaded_data['model_name'] == 'Random Forest'
        assert isinstance(loaded_data['model'], RandomForestClassifier)
        print("✅ Random Forest record successfully activated and synced to best_profile_shield_model.joblib!")

        # Test 6: Single Profile Scan End-to-End Prediction
        print("\n--- TEST 6: Testing Prediction Route with active production model ---")
        scan_res = client.post('/analysis/new', data={
            'username': 'test_user_ai',
            'display_name': 'Test AI Profile',
            'platform': 'Twitter/X',
            'account_age_days': '500',
            'followers_count': '15000',
            'following_count': '200',
            'posts_count': '1200',
            'has_profile_pic': '1',
            'has_bio': '1',
            'is_verified': '1',
            'has_url': '1',
            'avg_likes_per_post': '120.0',
            'avg_retweets_per_post': '25.0',
            'posting_frequency_per_day': '2.0',
            'bio_length': '110'
        }, follow_redirects=True)
        assert scan_res.status_code == 200
        assert b"Trust Intelligence Report" in scan_res.data
        print("✅ End-to-end Single Profile Scan executed successfully!")

        # Test 7: Verify Admin GET /admin/models page renders active model dynamically
        print("\n--- TEST 7: Verifying Admin UI rendering ---")
        models_page = client.get('/admin/models')
        assert models_page.status_code == 200
        assert b"Production Algorithm" in models_page.data
        assert b"Random Forest" in models_page.data
        print("✅ Admin page dynamically renders active Production Algorithm!")

        # Test 8: Invalid model selection error handling
        print("\n--- TEST 8: Verifying invalid model selection handling ---")
        invalid_res = client.post('/admin/models/train', data={
            'model_type': 'invalid_model_abc'
        }, follow_redirects=True)
        assert invalid_res.status_code == 200
        assert b"Invalid algorithm selection" in invalid_res.data
        print("✅ Invalid model selection correctly rejected with error message!")

        print("\n==================================================================")
        print("   ALL 8 MODEL SELECTION VERIFICATION TESTS PASSED SUCCESSFULLY!  ")
        print("==================================================================")

if __name__ == '__main__':
    test_model_selection_flow()
