"""Google OAuth 2.0 helpers for YouTube integration.

Flow:
  1.  build_auth_url()          → redirect user to Google
  2.  exchange_code(code)       → get access_token + refresh_token
  3.  fetch_channel_info(token) → get channel id / name / thumbnail
  4.  refresh_access_token(rt)  → get a new access_token when expired
"""
from datetime import datetime, timedelta, timezone

import httpx

from src.core.config import config
from src.logger import logger

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_YOUTUBE_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"

_SCOPES = " ".join(
    [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
    ]
)


# ---------------------------------------------------------------------------
# Step 1 – Build the URL the user is redirected to
# ---------------------------------------------------------------------------

def build_auth_url(state: str) -> str:
    """Return the Google OAuth consent-screen URL."""
    import urllib.parse

    params = {
        "client_id": config.get_google_client_id(),
        "redirect_uri": config.get_google_redirect_uri(),
        "response_type": "code",
        "scope": _SCOPES,
        "access_type": "offline",   # so we get a refresh_token
        "prompt": "consent",        # always show consent to force refresh_token
        "state": state,
    }
    return f"{_GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


# ---------------------------------------------------------------------------
# Step 2 – Exchange the auth code for tokens
# ---------------------------------------------------------------------------

async def exchange_code(code: str) -> dict:
    """Exchange the one-time ``code`` for access + refresh tokens.

    Returns the raw token response dict, e.g.:
      {
        "access_token": "...",
        "refresh_token": "...",
        "expires_in": 3600,
        "token_type": "Bearer",
        ...
      }
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": config.get_google_client_id(),
                "client_secret": config.get_google_client_secret(),
                "redirect_uri": config.get_google_redirect_uri(),
                "grant_type": "authorization_code",
            },
        )
    if resp.is_error:
        logger.error("Google token exchange failed: %s", resp.text)
        raise RuntimeError(f"Google OAuth token exchange failed: {resp.text}")
    return resp.json()


# ---------------------------------------------------------------------------
# Step 3 – Fetch the user's YouTube channel info
# ---------------------------------------------------------------------------

async def fetch_channel_info(access_token: str) -> dict:
    """Return basic channel info: id, snippet.title, snippet.thumbnails.

    Returns an empty dict if the user has no YouTube channel.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _YOUTUBE_CHANNELS_URL,
            params={"part": "snippet", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.is_error:
        logger.error("YouTube channels API failed: %s", resp.text)
        return {}

    data = resp.json()
    items = data.get("items", [])
    if not items:
        return {}

    channel = items[0]
    snippet = channel.get("snippet", {})
    thumbnail = (
        snippet.get("thumbnails", {})
        .get("default", {})
        .get("url")
    )
    return {
        "channel_id": channel.get("id"),
        "channel_name": snippet.get("title"),
        "channel_thumbnail": thumbnail,
    }


# ---------------------------------------------------------------------------
# Step 4 – Refresh an expired access token
# ---------------------------------------------------------------------------

async def refresh_access_token(refresh_token: str) -> tuple[str, datetime]:
    """Use the refresh_token to get a new access_token.

    Returns (new_access_token, new_expiry_datetime).
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": config.get_google_client_id(),
                "client_secret": config.get_google_client_secret(),
                "grant_type": "refresh_token",
            },
        )
    if resp.is_error:
        logger.error("Google token refresh failed: %s", resp.text)
        raise RuntimeError(f"Google token refresh failed: {resp.text}")

    data = resp.json()
    new_access_token = data["access_token"]
    expires_in = int(data.get("expires_in", 3600))
    new_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    return new_access_token, new_expiry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def token_expiry_from_response(token_data: dict) -> datetime:
    """Compute the UTC expiry datetime from a Google token response."""
    expires_in = int(token_data.get("expires_in", 3600))
    return datetime.now(timezone.utc) + timedelta(seconds=expires_in)
