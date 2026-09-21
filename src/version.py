"""
Centralized Version and Repository Information for CookieRun Bot.
"""

CURRENT_VERSION = "2.2.7"
GITHUB_REPO = "Jakprim-2004/cookie-run-classic-auto-Bot"
RAW_VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def parse_version(ver_str: str) -> tuple:
    """Parse a version string (e.g., 'v2.0.1', '2.0.0') into a comparable tuple of ints."""
    if not ver_str:
        return (0, 0, 0)
    cleaned = ver_str.strip().lower().lstrip("v")
    # Take only numeric/dot portion before any pre-release tags like -beta
    main_part = cleaned.split("-")[0].split("+")[0]
    parts = []
    for p in main_part.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_newer_version(remote_ver: str, local_ver: str = CURRENT_VERSION) -> bool:
    """Return True if remote_ver is strictly greater than local_ver."""
    try:
        return parse_version(remote_ver) > parse_version(local_ver)
    except Exception:
        return False
