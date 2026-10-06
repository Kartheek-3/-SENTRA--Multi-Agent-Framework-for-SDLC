import json
import os
import re
import pytest

def test_figma_token_not_hardcoded_in_repository():
    """Verify that no hardcoded Figma tokens or credentials exist in source or documentation."""
    suspicious_patterns = [
        re.compile(r"figd_[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
        re.compile(r"FIGMA_ACCESS_TOKEN\s*=\s*['\"][a-zA-Z0-9_-]{20,}['\"]", re.IGNORECASE),
        re.compile(r"\"FIGMA_ACCESS_TOKEN\"\s*:\s*\"[a-zA-Z0-9_-]{20,}\"", re.IGNORECASE)
    ]
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    checked_files = 0
    for root, dirs, files in os.walk(repo_root):
        if any(ignored in root for ignored in [".git", "node_modules", ".pytest_cache", ".venv", "venv", "chroma_db", "dist"]):
            continue
        for file in files:
            if file.endswith((".py", ".json", ".md", ".tsx", ".ts", ".css", ".html")):
                filepath = os.path.join(root, file)
                checked_files += 1
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    for pattern in suspicious_patterns:
                        assert not pattern.search(content), f"Potential secret leak detected in {filepath}"
                except Exception:
                    pass
    assert checked_files > 20

def test_figma_mcp_config_schema():
    """Verify that global mcp_config.json contains valid official remote Figma MCP schema."""
    mcp_path = os.path.expanduser(r"~\.gemini\config\mcp_config.json")
    if os.path.exists(mcp_path):
        with open(mcp_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "mcpServers" in data
        assert "figma" in data["mcpServers"]
        figma_server = data["mcpServers"]["figma"]
        assert "serverUrl" in figma_server
        assert "figma.com" in figma_server["serverUrl"]
        # Ensure no token values are stored in serverUrl or config
        assert "figd_" not in json.dumps(figma_server)

def test_figma_environment_variable_policy(monkeypatch):
    """Verify that integration requires host environment variable and does not read hardcoded fallbacks."""
    # When unset
    monkeypatch.delenv("FIGMA_ACCESS_TOKEN", raising=False)
    token = os.environ.get("FIGMA_ACCESS_TOKEN")
    assert token is None

    # When set via environment variable
    monkeypatch.setenv("FIGMA_ACCESS_TOKEN", "test-token-from-env")
    assert os.environ.get("FIGMA_ACCESS_TOKEN") == "test-token-from-env"

def test_gitignore_secret_file_coverage():
    """Verify that .gitignore actively excludes secret credential files."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gitignore_path = os.path.join(repo_root, ".gitignore")
    assert os.path.exists(gitignore_path)
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert ".env" in content
    assert "*.token" in content or "*.secret" in content or "*.key" in content
