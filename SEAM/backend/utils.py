import re

def slugify(text: str) -> str:
    """Convert text to a safe directory name."""
    if not text:
        return "project"
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')[:50]
