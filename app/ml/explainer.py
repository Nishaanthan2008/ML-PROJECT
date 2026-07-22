import numpy as np
import pandas as pd
import shap
from app.ml.pipeline import FEATURE_COLUMNS

class AIExplainer:
    """Generates SHAP feature importances and natural language AI narrative explanations for social profile assessments."""

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
        'profile_completeness': 'Profile Completeness Index'
    }

    def __init__(self, model, pipeline):
        self.model = model
        self.pipeline = pipeline

    def explain_profile(self, profile_dict):
        """
        Computes feature contribution values and builds visual SHAP structure + AI narrative paragraph.
        """
        df = pd.DataFrame([profile_dict])
        scaled_df = self.pipeline.transform(df)

        # Compute SHAP values or feature importance approximations
        shap_contributions = []
        
        try:
            explainer = shap.Explainer(self.model, scaled_df)
            shap_vals = explainer(scaled_df)
            
            # Handle binary classification outputs
            if len(shap_vals.values.shape) == 3:
                # [sample, features, output_class] -> pick class 1 (bot/inorganic risk)
                raw_shap = shap_vals.values[0, :, 1]
            elif len(shap_vals.values.shape) == 2:
                raw_shap = shap_vals.values[0, :]
            else:
                raw_shap = shap_vals.values[0]

            for i, col in enumerate(FEATURE_COLUMNS):
                val = float(raw_shap[i])
                shap_contributions.append({
                    'feature': col,
                    'display_name': self.FEATURE_HUMAN_NAMES.get(col, col),
                    'importance': round(val, 4),
                    'abs_importance': round(abs(val), 4),
                    'impact': 'increases_risk' if val > 0 else 'increases_trust'
                })

        except Exception as e:
            # Fallback heuristic feature importance calculation if SHAP tree explainer encounters edge case
            for col in FEATURE_COLUMNS:
                val = 0.0
                if col == 'follower_following_ratio' and profile_dict.get('following_count', 0) > profile_dict.get('followers_count', 0) * 3:
                    val = 0.45
                elif col == 'profile_completeness' and profile_dict.get('profile_completeness', 1.0) < 0.5:
                    val = 0.35
                elif col == 'username_digits_count' and profile_dict.get('username_digits_count', 0) >= 4:
                    val = 0.30
                elif col == 'account_age_days' and profile_dict.get('account_age_days', 0) < 30:
                    val = 0.25
                elif col == 'engagement_rate' and profile_dict.get('engagement_rate', 0.0) < 0.005:
                    val = 0.20

                shap_contributions.append({
                    'feature': col,
                    'display_name': self.FEATURE_HUMAN_NAMES.get(col, col),
                    'importance': round(val, 4),
                    'abs_importance': round(abs(val), 4),
                    'impact': 'increases_risk' if val > 0 else 'increases_trust'
                })

        # Sort contributions by absolute impact magnitude
        shap_contributions = sorted(shap_contributions, key=lambda x: x['abs_importance'], reverse=True)

        # Generate Natural Language AI Explanation Paragraph
        narrative_sentences = []

        followers = profile_dict.get('followers_count', 0)
        following = profile_dict.get('following_count', 0)
        account_age = profile_dict.get('account_age_days', 0)
        posts = profile_dict.get('posts_count', 0)
        has_pic = profile_dict.get('has_profile_pic', 1)
        has_bio = profile_dict.get('has_bio', 1)
        posting_freq = profile_dict.get('posting_frequency_per_day', 0.0)
        digits = profile_dict.get('username_digits_count', 0)
        eng_rate = profile_dict.get('engagement_rate', 0.0)
        completeness = profile_dict.get('profile_completeness', 0.0)

        # Follower/Following narrative
        if following > followers * 3 and following > 500:
            narrative_sentences.append(f"This profile follows {following:,} accounts while only having {followers:,} followers, presenting an inverted follow ratio characteristic of automated follow-unfollow scripts.")
        elif followers > following * 5 and followers > 2000:
            narrative_sentences.append(f"High follower-to-following ratio ({followers:,} vs {following:,}) indicates established organic reach and audience authority.")

        # Engagement narrative
        if eng_rate < 0.005 and followers > 1000:
            narrative_sentences.append("Extremely low engagement rate relative to follower count suggests inorganic or inactive audience accumulation.")
        elif eng_rate > 0.03:
            narrative_sentences.append("Healthy engagement rate across recent posts demonstrates active audience interaction.")

        # Account Completeness & Identity
        if not has_pic or not has_bio or completeness < 0.50:
            narrative_sentences.append(f"Profile completeness is low at {int(completeness*100)}%, missing essential identity signals such as bio description or customized avatar.")
        else:
            narrative_sentences.append(f"High profile completeness ({int(completeness*100)}%) with customized avatar and bio details enhances authenticity.")

        # Posting activity
        if posting_freq > 30.0:
            narrative_sentences.append(f"Abnormally high posting rate ({posting_freq:.1f} posts/day) exceeds human daily capacity, signaling automated bot syndication.")
        elif posting_freq < 0.05 and posts < 5:
            narrative_sentences.append("Low overall posting volume and infrequent activity suggest a dormant or placeholder profile.")

        # Username pattern
        if digits >= 4:
            narrative_sentences.append(f"Username contains {digits} numeric digits, a frequent signature in mass-generated automated accounts.")

        if not narrative_sentences:
            narrative_sentences.append("Profile behavioral metrics align with standard genuine account usage patterns.")

        ai_narrative = " ".join(narrative_sentences)

        return {
            'shap_importance': shap_contributions,
            'narrative': ai_narrative
        }
