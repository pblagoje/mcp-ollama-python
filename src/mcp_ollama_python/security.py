"""Security helpers for host validation, env allowlists, and input limits."""

from __future__ import annotations

import ipaddress
import os
import re
from typing import Optional
from urllib.parse import urlparse

MODEL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]*$")

ALLOWED_ENV_VARS = frozenset(
    {
        "OLLAMA_HOST",
        "OLLAMA_API_KEY",
        "OLLAMA_MODELS",
        "OLLAMA_EXECUTE_ENABLED",
        "OLLAMA_ALLOW_REMOTE_HOST",
    }
)

_LOCAL_HOSTNAMES = frozenset({"localhost", "host.docker.internal"})
_BLOCKED_METADATA_HOSTS = frozenset(
    {
        "metadata.google.internal",
        "169.254.169.254",
    }
)

MAX_CODE_BYTES = 65_536
MAX_EXECUTE_PROMPT_LEN = 10_000
MAX_CHAT_MESSAGES = 100
MAX_MESSAGE_CONTENT_LEN = 500_000
MAX_EMBED_INPUTS = 64
MAX_EMBED_TEXT_LEN = 100_000

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def is_truthy_env(name: str) -> bool:
    """Return True when an environment variable is set to a truthy value."""
    return os.getenv(name, "").strip().lower() in _TRUTHY


def is_execute_enabled() -> bool:
    """Code execution via ollama_execute is opt-in only."""
    return is_truthy_env("OLLAMA_EXECUTE_ENABLED")


def is_remote_host_allowed() -> bool:
    """When false, OLLAMA_HOST must point at loopback/local interfaces only."""
    return is_truthy_env("OLLAMA_ALLOW_REMOTE_HOST")


def validate_env_var_key(key: str) -> str:
    """Allow only known Ollama-related configuration keys."""
    if not key or not isinstance(key, str):
        raise ValueError("Environment variable name is required")
    clean = key.strip()
    if clean != key or not clean:
        raise ValueError("Invalid environment variable name")
    if clean not in ALLOWED_ENV_VARS:
        raise ValueError(
            f"Unsupported environment variable '{clean}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_ENV_VARS))}"
        )
    return clean


def validate_ollama_host(
    host: str,
    *,
    allow_remote: Optional[bool] = None,
) -> str:
    """
    Validate OLLAMA_HOST to reduce SSRF and credential leakage risks.

    By default only loopback/local hosts are permitted unless
    OLLAMA_ALLOW_REMOTE_HOST=1 is set.
    """
    if not host or not isinstance(host, str):
        raise ValueError("Host must be a non-empty string")

    host = host.strip()
    if not host.startswith(("http://", "https://")):
        raise ValueError("Host must start with http:// or https://")

    try:
        parsed = urlparse(host)
    except Exception as exc:
        raise ValueError(f"Invalid host URL: {exc}") from exc

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Host must use http or https scheme")
    if parsed.username or parsed.password:
        raise ValueError("Host URL must not contain embedded credentials")
    if not parsed.hostname:
        raise ValueError("Host must include a valid hostname")
    if parsed.path not in ("", "/"):
        raise ValueError("Host must not include a path")
    if parsed.query or parsed.fragment:
        raise ValueError("Host must not include query or fragment")

    hostname = parsed.hostname.lower()
    if hostname in _BLOCKED_METADATA_HOSTS:
        raise ValueError("Host points to a blocked metadata endpoint")

    remote_ok = is_remote_host_allowed() if allow_remote is None else allow_remote
    if not remote_ok and not _is_local_hostname(hostname):
        raise ValueError(
            "OLLAMA_HOST must use localhost/127.0.0.1. "
            "Set OLLAMA_ALLOW_REMOTE_HOST=1 to use a remote Ollama server."
        )

    if remote_ok:
        _reject_link_local_or_metadata_ip(hostname)

    if parsed.port is not None and not (1 <= parsed.port <= 65535):
        raise ValueError("Host port must be between 1 and 65535")

    return host.rstrip("/")


def _is_local_hostname(hostname: str) -> bool:
    bare = hostname.strip("[]")
    if bare.lower() in _LOCAL_HOSTNAMES:
        return True
    try:
        return ipaddress.ip_address(bare).is_loopback
    except ValueError:
        return bare.endswith(".localhost")


def _reject_link_local_or_metadata_ip(hostname: str) -> None:
    bare = hostname.strip("[]")
    try:
        ip = ipaddress.ip_address(bare)
    except ValueError:
        return
    if ip.is_link_local or ip.is_multicast or ip.is_reserved:
        raise ValueError("Host must not use link-local, multicast, or reserved IPs")
    if str(ip) == "169.254.169.254":
        raise ValueError("Host points to a blocked metadata endpoint")


def validate_model_name(model: str) -> str:
    """Validate Ollama model identifiers."""
    if not model or not isinstance(model, str):
        raise ValueError("Model name must be a non-empty string")
    clean = model.strip()
    if not MODEL_NAME_PATTERN.match(clean):
        raise ValueError(
            f"Invalid model name '{clean}'. Must start with alphanumeric "
            "and contain only alphanumeric, dots, underscores, hyphens, or colons."
        )
    return clean


def validate_code_payload(code: str, *, label: str = "code") -> str:
    """Reject oversized or null-byte code before subprocess execution."""
    if not code or not isinstance(code, str):
        raise ValueError(f"{label} is required")
    if "\x00" in code:
        raise ValueError(f"{label} must not contain null bytes")
    encoded = code.encode("utf-8")
    if len(encoded) > MAX_CODE_BYTES:
        raise ValueError(f"{label} exceeds maximum size of {MAX_CODE_BYTES} bytes")
    return code


def clamp_int(value: int, *, minimum: int, maximum: int) -> int:
    """Clamp an integer to an inclusive range."""
    return max(minimum, min(maximum, int(value)))
