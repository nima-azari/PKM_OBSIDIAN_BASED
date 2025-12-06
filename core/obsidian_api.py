import os
import urllib.parse
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("OBSIDIAN_API_URL", "https://127.0.0.1:27124").rstrip("/")
API_KEY = os.getenv("OBSIDIAN_API_KEY", "")
VERIFY_SSL = os.getenv("OBSIDIAN_VERIFY_SSL", "false").lower() == "true"

if not API_KEY:
    raise RuntimeError("OBSIDIAN_API_KEY is not set in .env")


def _headers(extra=None):
    h = {
        "Authorization": f"Bearer {API_KEY}",
    }
    if extra:
        h.update(extra)
    return h


def _request(method: str, endpoint: str, **kwargs) -> requests.Response:
    url = f"{BASE_URL}{endpoint}"
    headers = kwargs.pop("headers", {})
    headers = _headers(headers)
    # Add timeout if not specified
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 30  # 30 second timeout
    resp = requests.request(method, url, headers=headers, verify=VERIFY_SSL, **kwargs)
    resp.raise_for_status()
    return resp


def get_server_info() -> dict:
    """GET / – check API is alive and authenticated."""
    resp = _request("GET", "/")
    return resp.json()


def list_dir(path: str = "") -> dict:
    """
    List a directory inside the vault.
    path "" = root, "30-Reference" = that folder, etc.
    """
    if path:
        endpoint = f"/vault/{urllib.parse.quote(path, safe='/')}/"
    else:
        endpoint = "/vault/"
    resp = _request("GET", endpoint)
    return resp.json()


def get_file(path: str) -> str:
    """Get a note as raw markdown."""
    endpoint = f"/vault/{urllib.parse.quote(path, safe='/')}"
    resp = _request("GET", endpoint, headers={"Accept": "text/markdown"})
    return resp.text


def put_file(path: str, content: str):
    """Create/replace a note."""
    endpoint = f"/vault/{urllib.parse.quote(path, safe='/')}"
    _request(
        "PUT",
        endpoint,
        data=content.encode("utf-8"),
        headers={"Content-Type": "text/markdown"},
    )


def append_file(path: str, content: str):
    """Append content to the end of an existing note."""
    endpoint = f"/vault/{urllib.parse.quote(path, safe='/')}"
    _request(
        "POST",
        endpoint,
        data=content.encode("utf-8"),
        headers={"Content-Type": "text/markdown"},
    )


def patch_file_heading(path: str, heading: str, content: str, operation: str = "append"):
    """
    Patch content under a specific heading in a note.
    operation: "append", "prepend", or "replace"
    """
    endpoint = f"/vault/{urllib.parse.quote(path, safe='/')}"
    _request(
        "PATCH",
        endpoint,
        data=content.encode("utf-8"),
        headers={
            "Content-Type": "text/markdown",
            "Heading": heading,
            "Content-Insertion-Position": operation,
        },
    )


def delete_file(path: str):
    """Delete a note from the vault."""
    endpoint = f"/vault/{urllib.parse.quote(path, safe='/')}"
    _request("DELETE", endpoint)


def search_vault(query: str) -> dict:
    """
    Search the vault for notes matching a query.
    Returns search results from the API.
    """
    endpoint = "/search/simple/"
    resp = _request("POST", endpoint, json={"query": query})
    return resp.json()


def get_active_file() -> dict:
    """Get information about the currently active file in Obsidian."""
    endpoint = "/active/"
    resp = _request("GET", endpoint)
    return resp.json()
