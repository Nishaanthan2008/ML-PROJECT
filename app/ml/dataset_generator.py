import numpy as np
import pandas as pd
import random
import os

def generate_synthetic_profile_dataset(num_samples=1200, random_seed=42):
    """
    Generates a synthetic dataset of social profiles with realistic features.
    
    Includes 20+ raw and engineered features:
    - account_age_days
    - followers_count
    - following_count
    - posts_count
    - has_profile_pic
    - has_bio
    - is_verified
    - has_url
    - avg_likes_per_post
    - avg_retweets_per_post
    - posting_frequency_per_day
    - bio_length
    - username_digits_count
    - follower_following_ratio
    - engagement_rate
    - profile_completeness
    - activity_burstiness
    - target (0: Organic/Genuine, 1: Inorganic/Spam/Bot)
    """
    np.random.seed(random_seed)
    random.seed(random_seed)
    
    data = []
    
    for i in range(num_samples):
        # Determine archetype
        # 0: Genuine Regular, 1: Genuine Influencer, 2: Suspicious Growth, 3: Bot/Spam, 4: Inactive Fake
        archetype = np.random.choice([0, 1, 2, 3, 4], p=[0.40, 0.15, 0.15, 0.20, 0.10])
        
        if archetype == 0: # Genuine Regular User
            account_age_days = int(np.random.exponential(scale=800) + 120)
            followers_count = int(np.random.gamma(shape=2, scale=350) + 50)
            following_count = int(np.random.gamma(shape=2, scale=300) + 40)
            posts_count = int(np.random.gamma(shape=2, scale=400) + 20)
            has_profile_pic = 1 if np.random.rand() > 0.02 else 0
            has_bio = 1 if np.random.rand() > 0.10 else 0
            is_verified = 1 if np.random.rand() > 0.96 else 0
            has_url = 1 if np.random.rand() > 0.40 else 0
            avg_likes_per_post = round(float(np.random.normal(loc=18.0, scale=8.0)), 2)
            avg_retweets_per_post = round(float(np.random.normal(loc=3.5, scale=2.0)), 2)
            posting_frequency_per_day = round(float(np.random.uniform(0.1, 2.5)), 2)
            bio_length = int(np.random.normal(loc=65, scale=25)) if has_bio else 0
            username_digits_count = int(np.random.choice([0, 1, 2], p=[0.7, 0.2, 0.1]))
            is_bot_label = 0
            
        elif archetype == 1: # Genuine Influencer / Business
            account_age_days = int(np.random.exponential(scale=1200) + 500)
            followers_count = int(np.random.exponential(scale=50000) + 10000)
            following_count = int(np.random.normal(loc=800, scale=300))
            posts_count = int(np.random.gamma(shape=3, scale=1000) + 500)
            has_profile_pic = 1
            has_bio = 1
            is_verified = 1 if np.random.rand() > 0.40 else 0
            has_url = 1
            avg_likes_per_post = round(float(np.random.exponential(scale=1200) + 200), 2)
            avg_retweets_per_post = round(float(np.random.exponential(scale=250) + 40), 2)
            posting_frequency_per_day = round(float(np.random.uniform(1.0, 8.0)), 2)
            bio_length = int(np.random.normal(loc=110, scale=20))
            username_digits_count = 0
            is_bot_label = 0

        elif archetype == 2: # Suspicious Growth / Inorganic
            account_age_days = int(np.random.uniform(15, 120))
            followers_count = int(np.random.exponential(scale=15000) + 3000)
            following_count = int(np.random.normal(loc=4500, scale=500))
            posts_count = int(np.random.uniform(5, 50))
            has_profile_pic = 1 if np.random.rand() > 0.25 else 0
            has_bio = 1 if np.random.rand() > 0.40 else 0
            is_verified = 0
            has_url = 1 if np.random.rand() > 0.50 else 0
            avg_likes_per_post = round(float(np.random.uniform(0.5, 5.0)), 2)
            avg_retweets_per_post = round(float(np.random.uniform(0.0, 1.0)), 2)
            posting_frequency_per_day = round(float(np.random.uniform(0.05, 0.5)), 2)
            bio_length = int(np.random.uniform(10, 40)) if has_bio else 0
            username_digits_count = int(np.random.choice([2, 3, 4, 5], p=[0.2, 0.3, 0.3, 0.2]))
            is_bot_label = 1

        elif archetype == 3: # Bot / Spam Network
            account_age_days = int(np.random.uniform(5, 90))
            followers_count = int(np.random.uniform(10, 300))
            following_count = int(np.random.uniform(1500, 5000))
            posts_count = int(np.random.exponential(scale=2000) + 100)
            has_profile_pic = 1 if np.random.rand() > 0.50 else 0
            has_bio = 1 if np.random.rand() > 0.60 else 0
            is_verified = 0
            has_url = 1 if np.random.rand() > 0.70 else 0
            avg_likes_per_post = round(float(np.random.uniform(0.0, 1.5)), 2)
            avg_retweets_per_post = round(float(np.random.uniform(0.0, 0.8)), 2)
            posting_frequency_per_day = round(float(np.random.uniform(15.0, 120.0)), 2)
            bio_length = int(np.random.uniform(5, 30)) if has_bio else 0
            username_digits_count = int(np.random.choice([4, 5, 6, 7, 8], p=[0.1, 0.2, 0.3, 0.3, 0.1]))
            is_bot_label = 1

        else: # Inactive / Abandoned Fake
            account_age_days = int(np.random.uniform(100, 600))
            followers_count = int(np.random.uniform(0, 20))
            following_count = int(np.random.uniform(100, 2000))
            posts_count = int(np.random.choice([0, 1, 2, 3]))
            has_profile_pic = 0 if np.random.rand() > 0.30 else 1
            has_bio = 0 if np.random.rand() > 0.20 else 1
            is_verified = 0
            has_url = 0
            avg_likes_per_post = 0.0
            avg_retweets_per_post = 0.0
            posting_frequency_per_day = 0.0
            bio_length = 0
            username_digits_count = int(np.random.choice([3, 4, 5, 6]))
            is_bot_label = 1

        # Sanity cleanups
        avg_likes_per_post = max(0.0, avg_likes_per_post)
        avg_retweets_per_post = max(0.0, avg_retweets_per_post)
        bio_length = max(0, min(160, bio_length))
        followers_count = max(0, followers_count)
        following_count = max(0, following_count)
        posts_count = max(0, posts_count)

        # Derived metrics
        ff_ratio = round(followers_count / (following_count + 1), 4)
        total_eng = (avg_likes_per_post + avg_retweets_per_post * 2) * posts_count
        engagement_rate = round(total_eng / (followers_count + 1), 4)
        completeness = round((has_profile_pic * 0.3 + has_bio * 0.3 + has_url * 0.2 + (1 if bio_length > 30 else 0.2)), 2)

        data.append({
            'username': f"user_{i+1000}_{username_digits_count}",
            'display_name': f"User {i+1000}",
            'platform': 'Twitter/X',
            'account_age_days': account_age_days,
            'followers_count': followers_count,
            'following_count': following_count,
            'posts_count': posts_count,
            'has_profile_pic': has_profile_pic,
            'has_bio': has_bio,
            'is_verified': is_verified,
            'has_url': has_url,
            'avg_likes_per_post': avg_likes_per_post,
            'avg_retweets_per_post': avg_retweets_per_post,
            'posting_frequency_per_day': posting_frequency_per_day,
            'bio_length': bio_length,
            'username_digits_count': username_digits_count,
            'follower_following_ratio': ff_ratio,
            'engagement_rate': engagement_rate,
            'profile_completeness': completeness,
            'label': is_bot_label,
            'is_bot': is_bot_label
        })

    df = pd.DataFrame(data)
    return df

if __name__ == '__main__':
    df = generate_synthetic_profile_dataset()
    print(f"Generated {len(df)} records. Class distribution:")
    print(df['is_bot'].value_counts())
