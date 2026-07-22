import os
from app import create_app, db
from seed import seed_database

app = create_app('development')

if __name__ == '__main__':
    # Auto-seed database if db file or saved models don't exist
    db_file = os.path.join(app.root_path, '..', 'instance', 'profile_shield.db')
    model_file = os.path.join(app.config['MODEL_FOLDER'], 'best_profile_shield_model.joblib')

    if not os.path.exists(db_file) or not os.path.exists(model_file):
        print("--> Auto-initializing database and ML models for first-time startup...")
        seed_database()

    print("==================================================================")
    print("  PROFILE SHIELD AI - Next Generation Social Profile Trust Platform")
    print("  Server running at: http://127.0.0.1:5050/")
    print("  Admin Credentials: admin@profileshield.ai / Admin123!")
    print("==================================================================")
    
    app.run(host='0.0.0.0', port=5050, debug=True)
