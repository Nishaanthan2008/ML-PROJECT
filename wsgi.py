import os
from app import create_app, db
from seed import seed_database

env = os.environ.get('FLASK_ENV', os.environ.get('FLASK_CONFIG', 'development'))
app = create_app(env)

if __name__ == '__main__':
    model_file = os.path.join(app.config['MODEL_FOLDER'], 'best_profile_shield_model.joblib')

    with app.app_context():
        try:
            from app.models.user import User
            if User.query.first() is None or not os.path.exists(model_file):
                print("--> Auto-initializing database and ML models for first-time startup...")
                seed_database()
        except Exception as e:
            print(f"--> Notice: Startup database check: {e}")

    print("==================================================================")
    print("  PROFILE SHIELD AI - Next Generation Social Profile Trust Platform")
    print("  Server running at: http://127.0.0.1:5050/")
    print("  Admin Credentials: admin@profileshield.ai / Admin123!")
    print("==================================================================")
    
    app.run(host='0.0.0.0', port=5050, debug=True)
