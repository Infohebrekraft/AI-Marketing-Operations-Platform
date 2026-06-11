from urllib.parse import urlencode
import httpx
from .config import get_settings

settings = get_settings()


def linkedin_authorization_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "scope": settings.linkedin_scopes,
        "state": state,
    }
    return "https://www.linkedin.com/oauth/v2/authorization?" + urlencode(params)


async def exchange_code_for_token(code: str) -> dict:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.linkedin_redirect_uri,
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if resp.status_code >= 400:
            raise Exception(f"LinkedIn token exchange failed: {resp.status_code} {resp.text}")

        return resp.json()


async def fetch_member_profile(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers=headers,
        )

        if resp.status_code >= 400:
            raise Exception(f"LinkedIn profile fetch failed: {resp.status_code} {resp.text}")

        return resp.json()


def build_member_urn(profile: dict) -> str:
    """
    OpenID Connect userinfo returns `sub`.
    For many LinkedIn apps this can be used to construct a person URN.
    If publishing fails later, we will need to add the /v2/me profile call
    depending on app permissions.
    """
    sub = profile.get("sub")
    if not sub:
        return ""
    return f"urn:li:person:{sub}"


async def publish_text_post(access_token: str, author_urn: str, text: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=payload,
        )

        if resp.status_code >= 400:
            raise Exception(f"LinkedIn publish failed: {resp.status_code} {resp.text}")

        return {
            "status_code": resp.status_code,
            "post_id": resp.headers.get("X-RestLi-Id"),
        }