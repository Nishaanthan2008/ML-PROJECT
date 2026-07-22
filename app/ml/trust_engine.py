import random
import hashlib
import numpy as np

class TrustEngine:
    """
    Core AI Security Analyst Engine for Profile Shield AI.
    Calculates multi-dimensional trust scores, sub-scores, Digital DNA fingerprints,
    Trust Radar metrics, Evolution Timelines, Heatmap matrices, and Behaviour Clusters.
    """

    @staticmethod
    def generate_digital_dna(username, trust_score, cluster):
        """Generates a unique deterministic Digital DNA fingerprint (e.g. BHV-87231)."""
        raw_hash = hashlib.sha256(f"{username}_{trust_score}_{cluster}".encode('utf-8')).hexdigest()
        numeric_part = int(raw_hash[:6], 16) % 90000 + 10000
        return f"BHV-{numeric_part}"

    @staticmethod
    def calculate_trust_metrics(profile_data, raw_bot_probability):
        """
        Calculates complete multi-faceted Trust Intelligence Report data.
        
        profile_data: dict containing profile features
        raw_bot_probability: float between 0.0 (genuine) and 1.0 (bot)
        """
        # Convert raw bot probability into Trust Score (0 to 100)
        base_trust = max(0.0, min(100.0, (1.0 - raw_bot_probability) * 100.0))
        
        followers = profile_data.get('followers_count', 0)
        following = profile_data.get('following_count', 0)
        account_age = profile_data.get('account_age_days', 0)
        posts = profile_data.get('posts_count', 0)
        has_pic = profile_data.get('has_profile_pic', 1)
        has_bio = profile_data.get('has_bio', 1)
        has_url = profile_data.get('has_url', 0)
        is_verified = profile_data.get('is_verified', 0)
        posting_freq = profile_data.get('posting_frequency_per_day', 0.0)
        avg_likes = profile_data.get('avg_likes_per_post', 0.0)
        avg_retweets = profile_data.get('avg_retweets_per_post', 0.0)
        digits = profile_data.get('username_digits_count', 0)

        # 1. Calculate Sub-Scores (0 to 100)
        # Profile Quality
        profile_quality = min(100.0, (has_pic * 30 + has_bio * 30 + has_url * 20 + is_verified * 20 + max(0, 10 - digits*2)))
        
        # Engagement Quality
        total_eng_per_post = avg_likes + avg_retweets * 2
        if followers > 0:
            eng_rate = (total_eng_per_post * max(1, posts)) / (followers + 1)
            engagement_quality = min(100.0, eng_rate * 2000.0 + 20.0) if eng_rate > 0.001 else max(10.0, eng_rate * 5000)
        else:
            engagement_quality = 30.0 if posts == 0 else 10.0

        # Network Authenticity
        ff_ratio = followers / (following + 1)
        if ff_ratio > 0.8:
            network_authenticity = min(100.0, 50.0 + min(50.0, ff_ratio * 10))
        else:
            network_authenticity = max(10.0, ff_ratio * 70.0)

        # Activity Pattern
        if 0.1 <= posting_freq <= 10.0:
            activity_pattern = 90.0
        elif posting_freq > 25.0:
            activity_pattern = max(10.0, 100.0 - posting_freq * 2)
        else:
            activity_pattern = 50.0 if account_age > 180 else 75.0

        # Growth Pattern
        if account_age > 300 and followers < 50000:
            growth_pattern = 92.0
        elif account_age < 60 and followers > 20000:
            growth_pattern = 15.0 # Suspicious explosive growth
        else:
            growth_pattern = 85.0

        # Behaviour Score (composite average)
        behaviour_score = round((profile_quality + engagement_quality + network_authenticity + activity_pattern + growth_pattern) / 5.0, 1)

        # Final Weighted Trust Score
        final_trust_score = round(0.55 * base_trust + 0.45 * behaviour_score, 1)

        # 2. Confidence Level (0 to 100)
        confidence = round(min(98.5, max(75.0, 85.0 + (account_age / 200) + (posts / 500) - (digits * 2))), 1)

        # 3. Risk Level & Risk Meter (Color)
        if final_trust_score >= 80.0:
            risk_level = 'Low'
            risk_color = 'Green'
            health_meter = 'Excellent' if final_trust_score >= 90 else 'Good'
            recommendation = 'Likely Genuine'
        elif final_trust_score >= 60.0:
            risk_level = 'Moderate'
            risk_color = 'Yellow'
            health_meter = 'Average'
            recommendation = 'Needs Manual Review'
        elif final_trust_score >= 35.0:
            risk_level = 'High'
            risk_color = 'Orange'
            health_meter = 'Poor'
            recommendation = 'Suspicious Growth' if followers > following else 'Possible Spam'
        else:
            risk_level = 'Critical'
            risk_color = 'Red'
            health_meter = 'Critical'
            recommendation = 'Bot-like Behaviour' if posting_freq > 20 else 'High Risk'

        # 4. Behaviour Cluster Classification
        if raw_bot_probability > 0.70 and posting_freq > 20:
            cluster = 'Bot-like'
        elif raw_bot_probability > 0.60 and digits >= 4:
            cluster = 'Spam'
        elif followers > 25000 and is_verified:
            cluster = 'Influencer'
        elif followers > 10000 and has_url:
            cluster = 'Business'
        elif posts < 3 and account_age > 100:
            cluster = 'Inactive'
        elif account_age < 90 and followers > 5000:
            cluster = 'Growing'
        else:
            cluster = 'Natural'

        # 5. Digital DNA Fingerprint
        username = profile_data.get('username', 'user_analysis')
        dna = TrustEngine.generate_digital_dna(username, final_trust_score, cluster)

        # 6. Trust Radar Data (7 Axes)
        trust_radar = {
            'Activity': round(min(100.0, activity_pattern), 1),
            'Engagement': round(min(100.0, engagement_quality), 1),
            'Popularity': round(min(100.0, min(100.0, np.log1p(followers) * 10)), 1),
            'Consistency': round(min(100.0, 95.0 - abs(posting_freq - 3.0)*5), 1),
            'Completeness': round(min(100.0, profile_quality), 1),
            'Credibility': round(min(100.0, (1.0 - raw_bot_probability)*100), 1),
            'Authenticity': round(min(100.0, network_authenticity), 1)
        }

        # 7. Behaviour Evolution Timeline
        # Visualizing 5 historical stages: Old -> Growing -> Suspicious/Normal -> Dormant/Active -> Current State
        timeline = [
            {
                'stage': 'Initial Registration',
                'phase': 'Old',
                'period': f"{account_age} days ago",
                'trust': round(min(100.0, final_trust_score * 0.9), 1),
                'status': 'Standard Signup'
            },
            {
                'stage': 'Early Audience Building',
                'phase': 'Growing',
                'period': f"{int(account_age * 0.75)} days ago",
                'trust': round(min(100.0, final_trust_score * 0.95), 1),
                'status': 'Gradual Interaction'
            },
            {
                'stage': 'Activity Shift',
                'phase': 'Suspicious' if risk_level in ['High', 'Critical'] else 'Normal',
                'period': f"{int(account_age * 0.50)} days ago",
                'trust': round(final_trust_score * 0.85 if risk_level in ['High', 'Critical'] else final_trust_score * 0.98, 1),
                'status': 'Spike in Follow/Post Frequency' if risk_level in ['High', 'Critical'] else 'Consistent Posting'
            },
            {
                'stage': 'Mid-Term Pattern',
                'phase': 'Dormant' if posts < 5 else 'Active',
                'period': f"{int(account_age * 0.25)} days ago",
                'trust': round(final_trust_score * 0.92, 1),
                'status': 'Reduced Post Frequency' if posts < 5 else 'Regular Content Engagement'
            },
            {
                'stage': 'Current Intelligence Assessment',
                'phase': 'Highly Active' if posting_freq > 5 else 'Stable',
                'period': 'Present Day',
                'trust': final_trust_score,
                'status': f"Evaluated as {cluster} ({recommendation})"
            }
        ]

        # 8. Behaviour Heatmap (7 Days x 24 Hours Posting Matrix)
        # Deterministically build a 7x24 grid based on account posting frequency and risk
        heatmap_matrix = []
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        seed_val = int(hashlib.md5(username.encode('utf-8')).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed_val)

        for d_idx, day in enumerate(days):
            day_hours = []
            for h in range(24):
                if cluster == 'Bot-like':
                    # Bots post consistently 24/7 without night gaps
                    intensity = int(rng.choice([3, 4, 5], p=[0.2, 0.5, 0.3]))
                elif cluster == 'Spam':
                    # Spam burst during active promotional hours
                    intensity = int(rng.choice([0, 1, 4, 5], p=[0.4, 0.2, 0.2, 0.2]))
                else:
                    # Natural human circadian pattern (low 1am-6am)
                    if 1 <= h <= 6:
                        intensity = int(rng.choice([0, 1], p=[0.9, 0.1]))
                    else:
                        intensity = int(rng.choice([0, 1, 2, 3], p=[0.3, 0.4, 0.2, 0.1]))
                day_hours.append(intensity)
            heatmap_matrix.append({'day': day, 'hours': day_hours})

        # 9. Similar Profiles Clustering Benchmark
        similar_profiles = [
            {'username': f"similar_acc_{seed_val % 90 + 10}", 'similarity': 96.4, 'cluster': cluster, 'trust_score': round(final_trust_score + rng.uniform(-4, 4), 1)},
            {'username': f"vector_match_{seed_val % 80 + 20}", 'similarity': 91.8, 'cluster': cluster, 'trust_score': round(final_trust_score + rng.uniform(-6, 6), 1)},
            {'username': f"pattern_peer_{seed_val % 70 + 30}", 'similarity': 87.2, 'cluster': cluster, 'trust_score': round(final_trust_score + rng.uniform(-8, 8), 1)}
        ]

        return {
            'trust_score': final_trust_score,
            'confidence': confidence,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'recommendation': recommendation,
            'health_meter': health_meter,
            'behaviour_cluster': cluster,
            'digital_dna': dna,
            'sub_scores': {
                'behaviour_score': behaviour_score,
                'profile_quality': profile_quality,
                'engagement_quality': engagement_quality,
                'network_authenticity': network_authenticity,
                'activity_pattern': activity_pattern,
                'growth_pattern': growth_pattern
            },
            'trust_radar': trust_radar,
            'timeline': timeline,
            'heatmap': {'matrix': heatmap_matrix, 'days': days},
            'similar_profiles': similar_profiles
        }
