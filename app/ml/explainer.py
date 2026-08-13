import numpy as np
import pandas as pd
from app.ml.pipeline import FEATURE_COLUMNS

class AIExplainer:
    """
    Generates feature importance scores (via model.feature_importances_ or coef_)
    and natural-language AI narrative explanations for social profile assessments.
    SHAP has been removed to keep deployment size under 500 MB.
    """

    FEATURE_HUMAN_NAMES = {
        'account_age_days': 'Account Age (Days)',
        'followers_count': 'Followers Count',
        'following_count': 'Following Count',
        'posts_count': 'Total Posts',
        'has_profile_pic': 'Profile Picture Present',
        'has_bio': 'Bio Description Present',
        'is_verified': 'Verification Status',
        'has_url': 'External URL Link',
        'avg_likes_per_post': 'Average Likes / Post',
        'avg_retweets_per_post': 'Average Retweets / Post',
        'posting_frequency_per_day': 'Daily Posting Frequency',
        'bio_length': 'Bio Length',
        'username_digits_count': 'Digits in Handle',
        'follower_following_ratio': 'Follower/Following Ratio',
        'engagement_rate': 'Audience Engagement Rate',
        'profile_completeness': 'Profile Completeness Index',
    }

    def __init__(self, model, pipeline):
        self.model = model
        self.pipeline = pipeline

    # ------------------------------------------------------------------
    # Feature importance extraction
    # ------------------------------------------------------------------
    def _get_feature_importances(self):
        """
        Extract normalised feature importance values from the model.
        Works with tree-based models (feature_importances_) and linear
        models (coef_).  Falls back to equal weights if neither exists.
        """
        if self.model is None:
            return [1.0 / len(FEATURE_COLUMNS)] * len(FEATURE_COLUMNS)

        try:
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
            elif hasattr(self.model, 'coef_'):
                coef = self.model.coef_
                importances = np.abs(coef[0] if coef.ndim > 1 else coef)
            else:
                importances = np.ones(len(FEATURE_COLUMNS))

            # Normalise to [0, 1]
            total = importances.sum()
            if total > 0:
                importances = importances / total
            return importances.tolist()
        except Exception:
            return [1.0 / len(FEATURE_COLUMNS)] * len(FEATURE_COLUMNS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def explain_profile(self, profile_dict):
        """
        Returns feature contribution list and AI narrative paragraph.
        """
        importances = self._get_feature_importances()

        # Map importance values to signed direction using heuristics
        following = profile_dict.get('following_count', 0)
        followers = profile_dict.get('followers_count', 0)
        posting_freq = profile_dict.get('posting_frequency_per_day', 0.0)
        digits = profile_dict.get('username_digits_count', 0)
        account_age = profile_dict.get('account_age_days', 0)
        posts = profile_dict.get('posts_count', 0)
        has_pic = profile_dict.get('has_profile_pic', 1)
        has_bio = profile_dict.get('has_bio', 1)

        # Heuristic: signs based on known risk indicators
        risk_signals = {
            'follower_following_ratio': -1 if following > followers else 1,
            'posting_frequency_per_day': -1 if posting_freq > 20 else 1,
            'username_digits_count': -1 if digits >= 4 else 1,
            'account_age_days': -1 if account_age < 30 else 1,
            'engagement_rate': 1,
            'profile_completeness': 1 if (has_pic and has_bio) else -1,
        }

        feature_contributions = []
        for i, col in enumerate(FEATURE_COLUMNS):
            raw_val = importances[i] if i < len(importances) else 0.0
            sign = risk_signals.get(col, 1)
            signed_val = raw_val * sign

            feature_contributions.append({
                'feature': col,
                'display_name': self.FEATURE_HUMAN_NAMES.get(col, col),
                'importance': round(signed_val, 4),
                'abs_importance': round(raw_val, 4),
                'impact': 'increases_risk' if sign < 0 else 'increases_trust',
            })

        feature_contributions.sort(key=lambda x: x['abs_importance'], reverse=True)

        # ------------------------------------------------------------------
        # Natural language narrative
        # ------------------------------------------------------------------
        narrative_sentences = []

        if following > followers * 3 and following > 500:
            narrative_sentences.append(
                f"This profile follows {following:,} accounts while only having "
                f"{followers:,} followers — an inverted ratio characteristic of "
                "automated follow-unfollow scripts."
            )
        elif followers > following * 5 and followers > 2000:
            narrative_sentences.append(
                f"High follower-to-following ratio ({followers:,} vs {following:,}) "
                "indicates established organic reach and audience authority."
            )

        eng_rate = profile_dict.get('engagement_rate', 0.0)
        if eng_rate < 0.005 and followers > 1000:
            narrative_sentences.append(
                "Extremely low engagement rate relative to follower count suggests "
                "inorganic or inactive audience accumulation."
            )
        elif eng_rate > 0.03:
            narrative_sentences.append(
                "Healthy engagement rate across recent posts demonstrates active "
                "audience interaction."
            )

        completeness = profile_dict.get('profile_completeness', 0.0)
        if not has_pic or not has_bio:
            narrative_sentences.append(
                f"Profile completeness is low at {int(completeness * 100)}%, missing "
                "essential identity signals such as bio or avatar."
            )
        else:
            narrative_sentences.append(
                f"Profile completeness score of {int(completeness * 100)}% with "
                "avatar and bio enhances authenticity."
            )

        if posting_freq > 30.0:
            narrative_sentences.append(
                f"Abnormally high posting rate ({posting_freq:.1f} posts/day) "
                "exceeds human daily capacity, signaling automated bot syndication."
            )
        elif posting_freq < 0.05 and posts < 5:
            narrative_sentences.append(
                "Low overall posting volume and infrequent activity suggest a "
                "dormant or placeholder profile."
            )

        if digits >= 4:
            narrative_sentences.append(
                f"Username contains {digits} numeric digits — a frequent signature "
                "in mass-generated automated accounts."
            )

        if not narrative_sentences:
            narrative_sentences.append(
                "Profile behavioral metrics align with standard genuine account usage patterns."
            )

        return {
            'shap_importance': feature_contributions,   # kept same key for template compat
            'narrative': " ".join(narrative_sentences),
        }
