"""Pure URL helpers shared by Affiliate Friction Auditor phases."""

from __future__ import annotations

import html
import urllib.parse


def deep_decode(value: str) -> str:
    if not value:
        return ""
    decoded = str(value)
    for _ in range(4):
        decoded_html = html.unescape(decoded)
        decoded_url = urllib.parse.unquote(decoded_html)
        if decoded_url == decoded:
            break
        decoded = decoded_url
    return decoded.strip()


def normalize_url(base_url: str, value: str) -> str:
    if not value:
        return ""

    value = deep_decode(value).strip()
    low = value.lower()

    if low.startswith(("mailto:", "tel:", "javascript:", "data:", "blob:", "#")):
        return ""

    if value.startswith("//"):
        value = "https:" + value

    try:
        url = urllib.parse.urljoin(base_url, value)
        parsed = urllib.parse.urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            return ""

        parsed = parsed._replace(fragment="")
        return urllib.parse.urlunparse(parsed).rstrip("/")
    except Exception:
        return ""


def canonical_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(str(url).strip())
        parsed = parsed._replace(fragment="")
        return urllib.parse.urlunparse(parsed).rstrip("/")
    except Exception:
        return str(url).strip().rstrip("/")


def host_of(url: str, *, decode: bool = False) -> str:
    try:
        value = deep_decode(url) if decode else str(url).strip()
        return (urllib.parse.urlparse(value).hostname or "").lower()
    except Exception:
        return ""


def path_of(url: str, *, decode: bool = False) -> str:
    try:
        value = deep_decode(url) if decode else str(url).strip()
        return urllib.parse.urlparse(value).path.rstrip("/").lower() or "/"
    except Exception:
        return ""


def query_keys(url: str, *, decode: bool = True) -> set[str]:
    try:
        value = deep_decode(url) if decode else str(url).strip()
        parsed = urllib.parse.urlparse(value)
        return {key.lower() for key in urllib.parse.parse_qs(parsed.query).keys()}
    except Exception:
        return set()


def slug_of(url: str) -> str:
    path = path_of(url).strip("/")
    if "/" in path:
        return path.split("/")[-1]
    return path
