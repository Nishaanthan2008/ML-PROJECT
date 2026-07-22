import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import os

FEATURE_COLUMNS = [
    'account_age_days',
    'followers_count',
    'following_count',
    'posts_count',
    'has_profile_pic',
    'has_bio',
    'is_verified',
    'has_url',
    'avg_likes_per_post',
    'avg_retweets_per_post',
    'posting_frequency_per_day',
    'bio_length',
    'username_digits_count',
    'follower_following_ratio',
    'engagement_rate',
    'profile_completeness'
]

class FeaturePipeline:
    """Preprocesses raw profile data, performs feature engineering, and applies standard scaling."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.is_fitted = False

    def engineer_features(self, df):
        """Calculates derived features for dataframe or single record dict."""
        df = df.copy()
        
        # Ensure numerical types
        num_cols = ['account_age_days', 'followers_count', 'following_count', 'posts_count', 
                    'avg_likes_per_post', 'avg_retweets_per_post', 'posting_frequency_per_day',
                    'bio_length', 'username_digits_count']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Derived features
        df['follower_following_ratio'] = df['followers_count'] / (df['following_count'] + 1)
        total_eng = (df['avg_likes_per_post'] + df['avg_retweets_per_post'] * 2) * df['posts_count']
        df['engagement_rate'] = total_eng / (df['followers_count'] + 1)
        
        # Completeness
        pic = df['has_profile_pic'].astype(int) if 'has_profile_pic' in df.columns else 0
        bio = df['has_bio'].astype(int) if 'has_bio' in df.columns else 0
        url = df['has_url'].astype(int) if 'has_url' in df.columns else 0
        bio_len_bonus = (df['bio_length'] > 30).astype(int) * 0.2
        
        df['profile_completeness'] = (pic * 0.3 + bio * 0.3 + url * 0.2 + bio_len_bonus).clip(0.0, 1.0)

        # Re-order and retain feature columns
        for col in FEATURE_COLUMNS:
            if col not in df.columns:
                df[col] = 0.0

        return df[FEATURE_COLUMNS]

    def fit_transform(self, df):
        """Fit scaler on training data and transform features."""
        X_engineered = self.engineer_features(df)
        X_scaled = self.scaler.fit_transform(X_engineered)
        self.is_fitted = True
        return pd.DataFrame(X_scaled, columns=FEATURE_COLUMNS)

    def transform(self, df):
        """Transform single instance or dataset using fitted scaler."""
        X_engineered = self.engineer_features(df)
        if self.is_fitted:
            X_scaled = self.scaler.transform(X_engineered)
            return pd.DataFrame(X_scaled, columns=FEATURE_COLUMNS)
        return X_engineered

    def save(self, filepath):
        """Persist scaler state to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({'scaler': self.scaler, 'is_fitted': self.is_fitted}, filepath)

    def load(self, filepath):
        """Load scaler state from disk."""
        if os.path.exists(filepath):
            data = joblib.load(filepath)
            self.scaler = data['scaler']
            self.is_fitted = data['is_fitted']
            return True
        return False
