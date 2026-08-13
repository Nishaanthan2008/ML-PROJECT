"""
CSV Validator Service
Validates uploaded training datasets before ML model training.
"""
import pandas as pd

REQUIRED_COLUMNS = [
    'username',
    'display_name',
    'platform',
    'followers_count',
    'following_count',
    'posts_count',
    'account_age_days',
    'has_profile_pic',
    'has_bio',
    'is_verified',
    'has_url',
    'avg_likes_per_post',
    'avg_retweets_per_post',
    'posting_frequency_per_day',
    'label',
]

NUMERIC_COLUMNS = [
    'followers_count', 'following_count', 'posts_count',
    'account_age_days', 'avg_likes_per_post',
    'avg_retweets_per_post', 'posting_frequency_per_day',
]

BOOLEAN_COLUMNS = [
    'has_profile_pic', 'has_bio', 'is_verified', 'has_url',
]


def validate_profile_csv(df: pd.DataFrame) -> list[str]:
    """
    Validate a profile training CSV DataFrame.

    Returns a list of human-friendly error strings.
    An empty list means the dataset is valid.
    """
    errors = []

    # 1. Check target label column (supporting 'label' or 'is_bot')
    label_col = 'label' if 'label' in df.columns else ('is_bot' if 'is_bot' in df.columns else None)
    if not label_col:
        errors.append("Dataset must contain a target label column ('label' or 'is_bot').")
        return errors

    # Check remaining required columns
    req_cols = [c for c in REQUIRED_COLUMNS if c != 'label']
    missing_cols = [c for c in req_cols if c not in df.columns]
    if missing_cols:
        errors.append(
            f"Missing required columns: {', '.join(missing_cols)}."
        )
        return errors

    # 2. Check minimum row count
    if len(df) < 10:
        errors.append(
            f"Dataset too small: only {len(df)} rows found. "
            "A minimum of 10 rows is required for training."
        )

    # 3. Check label column contains valid values (0 or 1)
    unique_labels = set(df[label_col].dropna().unique())
    if not unique_labels.issubset({0, 1, '0', '1', True, False}):
        errors.append(
            f"'{label_col}' column must contain only binary values (0 or 1). "
            f"Found: {unique_labels}"
        )

    # 4. Check label balance (at least 5% of each class)
    label_counts = df[label_col].value_counts()
    if len(label_counts) < 2:
        errors.append(
            f"Dataset must contain both classes (genuine=0 and bot=1) in '{label_col}' column."
        )
    else:
        total = len(df)
        for lbl, cnt in label_counts.items():
            if cnt / total < 0.05:
                errors.append(
                    f"Class imbalance warning: label '{lbl}' has only {cnt} samples "
                    f"({cnt/total*100:.1f}%). Consider adding more samples of that class."
                )

    # 5. Validate numeric columns
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            non_numeric = pd.to_numeric(df[col], errors='coerce').isna().sum()
            if non_numeric > 0:
                errors.append(
                    f"Column '{col}' contains {non_numeric} non-numeric value(s). "
                    "All values must be numbers."
                )
            elif df[col].min() < 0:
                errors.append(
                    f"Column '{col}' contains negative values, which is not valid for this field."
                )

    # 6. Validate boolean columns (0/1 only)
    for col in BOOLEAN_COLUMNS:
        if col in df.columns:
            valid = df[col].dropna().isin([0, 1, '0', '1', True, False]).all()
            if not valid:
                errors.append(
                    f"Column '{col}' must contain only 0 or 1 values."
                )

    # 7. posts_count should not all be zero
    if 'posts_count' in df.columns:
        zero_posts = (pd.to_numeric(df['posts_count'], errors='coerce') == 0).sum()
        if zero_posts == len(df):
            errors.append(
                "All rows have posts_count = 0. "
                "Please provide actual post counts."
            )

    return errors
