import os
from pathlib import Path

# Base Directory of the application
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Base Configuration Class for Profile Shield AI."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'profile_shield_ai_secret_key_prod_2026_xyz'
    
    # SQLite Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{BASE_DIR / 'instance' / 'profile_shield.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Storage Paths
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads')
    DATASET_FOLDER = os.path.join(BASE_DIR, 'data')
    MODEL_FOLDER = os.path.join(BASE_DIR, 'saved_models')
    
    # MAX CONTENT LENGTH (16 MB for CSV uploads)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Allowed File Extensions
    ALLOWED_EXTENSIONS = {'csv'}

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
