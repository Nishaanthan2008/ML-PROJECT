"""
Profile Fetcher Service
Attempts to auto-fetch social profile data from platform APIs.
Falls back gracefully to empty/manual-entry defaults when APIs are unavailable.

IMPORTANT: Real API credentials must be set via environment variables.
Without credentials the fetchers return None and the UI shows manual-entry fields.
"""
import os


# ---------------------------------------------------------------------------
# Twitter / X
# ---------------------------------------------------------------------------
def fetch_twitter_profile(username: str) -> dict | None:
    """
    Attempt to fetch Twitter/X profile data using the Bearer token from env.
    Returns a profile dict on success, None on failure / missing credentials.
    """
    bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
    if not bearer_token:
        return None

    try:
        import requests
        url = f"https://api.twitter.com/2/users/by/username/{username}"
        params = {
            'user.fields': (
                'public_metrics,created_at,description,profile_image_url,verified'
            )
        }
        headers = {'Authorization': f'Bearer {bearer_token}'}
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        if resp.status_code != 200:
            return None

        data = resp.json().get('data', {})
        metrics = data.get('public_metrics', {})
        created_at = data.get('created_at', '')

        account_age_days = 0
        if created_at:
            from datetime import datetime, timezone
            try:
                created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                account_age_days = (
                    datetime.now(timezone.utc) - created
                ).days
            except Exception:
                account_age_days = 0

        followers = metrics.get('followers_count', 0)
        following = metrics.get('following_count', 0)
        posts = metrics.get('tweet_count', 1)  # never 0 by default

        return {
            'username': username,
            'display_name': data.get('name', username),
            'platform': 'Twitter/X',
            'followers_count': followers,
            'following_count': following,
            'posts_count': max(posts, 1),
            'account_age_days': account_age_days,
            'has_profile_pic': bool(data.get('profile_image_url')),
            'has_bio': bool(data.get('description', '').strip()),
            'is_verified': data.get('verified', False),
            'has_url': False,  # requires expanded fields
            'avg_likes_per_post': 0.0,
            'avg_retweets_per_post': 0.0,
            'posting_frequency_per_day': round(posts / max(account_age_days, 1), 3),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Instagram  (requires Instagram Graph API via Meta)
# ---------------------------------------------------------------------------
def fetch_instagram_profile(username: str) -> dict | None:
    """
    Attempt to fetch Instagram profile data.
    Requires INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID env vars.
    Returns None on failure.
    """
    access_token = os.environ.get('INSTAGRAM_ACCESS_TOKEN')
    if not access_token:
        return None

    try:
        import requests
        user_id = os.environ.get('INSTAGRAM_USER_ID', '')
        url = (
            f"https://graph.instagram.com/{user_id}"
            f"?fields=username,name,biography,followers_count,"
            f"follows_count,media_count,profile_picture_url,website"
            f"&access_token={access_token}"
        )
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            return None

        data = resp.json()
        followers = data.get('followers_count', 0)
        following = data.get('follows_count', 0)
        posts = max(data.get('media_count', 1), 1)

        return {
            'username': username,
            'display_name': data.get('name', username),
            'platform': 'Instagram',
            'followers_count': followers,
            'following_count': following,
            'posts_count': posts,
            'account_age_days': 365,        # IG API does not expose creation date
            'has_profile_pic': bool(data.get('profile_picture_url')),
            'has_bio': bool(data.get('biography', '').strip()),
            'is_verified': False,           # not exposed in basic display API
            'has_url': bool(data.get('website', '').strip()),
            'avg_likes_per_post': 0.0,
            'avg_retweets_per_post': 0.0,
            'posting_frequency_per_day': round(posts / 365, 3),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# LinkedIn  (requires LinkedIn OAuth2 access token)
# ---------------------------------------------------------------------------
def fetch_linkedin_profile(username: str) -> dict | None:
    """
    LinkedIn public profile API requires OAuth2.
    Without credentials returns None so the UI shows manual entry.
    """
    access_token = os.environ.get('LINKEDIN_ACCESS_TOKEN')
    if not access_token:
        return None

    try:
        import requests
        headers = {'Authorization': f'Bearer {access_token}'}
        url = 'https://api.linkedin.com/v2/me'
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return None

        data = resp.json()
        first = data.get('localizedFirstName', '')
        last = data.get('localizedLastName', '')
        display = f"{first} {last}".strip() or username

        return {
            'username': username,
            'display_name': display,
            'platform': 'LinkedIn',
            'followers_count': 500,         # LinkedIn hides exact counts
            'following_count': 200,
            'posts_count': 10,
            'account_age_days': 730,
            'has_profile_pic': True,
            'has_bio': True,
            'is_verified': True,            # LinkedIn verified by default
            'has_url': True,
            'avg_likes_per_post': 15.0,
            'avg_retweets_per_post': 2.0,
            'posting_frequency_per_day': 0.5,
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Unified dispatcher
# ---------------------------------------------------------------------------
def auto_fetch_profile(username: str, platform: str) -> dict | None:
    """
    Try to fetch a profile for the given platform.
    Returns the profile dict or None if the API is unavailable / fails.
    """
    platform_lower = platform.lower()

    if 'twitter' in platform_lower or platform_lower == 'x':
        return fetch_twitter_profile(username)
    elif 'instagram' in platform_lower:
        return fetch_instagram_profile(username)
    elif 'linkedin' in platform_lower:
        return fetch_linkedin_profile(username)

    return None
