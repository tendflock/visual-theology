"""Secret loader. Tries macOS Keychain first, falls back to env vars."""

import os

try:
    import keyring as _kr
except ImportError:
    _kr = None

_SERVICE = "logos4"


def get_secret(name: str, env_var: str = None) -> str:
    if _kr is not None:
        value = _kr.get_password(_SERVICE, name)
        if value:
            return value
    if env_var:
        return os.environ.get(env_var, "")
    return ""


def sermonaudio_api_key() -> str:
    return get_secret("sermonaudio_api_key", "SERMONAUDIO_API_KEY")


def sermonaudio_broadcaster_id() -> str:
    return get_secret("sermonaudio_broadcaster_id", "SERMONAUDIO_BROADCASTER_ID")


def anthropic_api_key() -> str:
    return get_secret("anthropic_api_key", "ANTHROPIC_API_KEY")
