import os

def allowed_file(filename, allowed_extensions):
    """Verifies file extension against allowed extension set."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def format_number(val):
    """Formats raw integers into human-readable compact strings (e.g. 1.5K, 2.4M)."""
    if val is None:
        return "0"
    num = float(val)
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return f"{int(num):,}"
