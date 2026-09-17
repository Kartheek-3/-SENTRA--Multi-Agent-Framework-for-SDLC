import re

class KnowledgeSanitizer:
    def __init__(self):
        # Extend regex to include JWT and stricter token catching
        self.patterns = [
            (re.compile(r"api_key\s*=\s*['\"][a-zA-Z0-9_-]+['\"]", re.IGNORECASE), "REDACTED_SECRET"),
            (re.compile(r"password\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE), "REDACTED_SECRET"),
            (re.compile(r"secret\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE), "REDACTED_SECRET"),
            (re.compile(r"token\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE), "REDACTED_SECRET"),
            # AWS Access Keys
            (re.compile(r"AKIA[0-9A-Z]{16}"), "REDACTED_AWS_KEY"),
            # JWT Tokens
            (re.compile(r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"), "REDACTED_JWT"),
            # Private keys
            (re.compile(r"-----BEGIN [A-Z]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z]+ PRIVATE KEY-----"), "REDACTED_PRIVATE_KEY")
        ]

    def sanitize(self, text: str) -> str:
        sanitized = text
        for pattern, replacement in self.patterns:
            sanitized = pattern.sub(f"[{replacement}]", sanitized)
        return sanitized
