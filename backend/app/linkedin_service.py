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
async def register_linkedin_image_upload(access_token: str, owner_urn: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }

    payload = {
        "registerUploadRequest": {
            "recipes": [
                "urn:li:digitalmediaRecipe:feedshare-image"
            ],
            "owner": owner_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ],
        }
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.linkedin.com/v2/assets?action=registerUpload",
            headers=headers,
            json=payload,
        )

        if resp.status_code >= 400:
            raise Exception(
                f"LinkedIn image registration failed: {resp.status_code} {resp.text}"
            )

        return resp.json()


async def upload_image_binary_to_linkedin(
    upload_url: str,
    access_token: str,
    image_path: str
) -> None:
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.put(
            upload_url,
            headers=headers,
            content=image_bytes,
        )

        if resp.status_code >= 400:
            raise Exception(
                f"LinkedIn image upload failed: {resp.status_code} {resp.text}"
            )


async def publish_image_post(
    access_token: str,
    author_urn: str,
    text: str,
    image_path: str,
    image_title: str = "HebreKraft AI Marketing"
) -> dict:
    registration = await register_linkedin_image_upload(
        access_token=access_token,
        owner_urn=author_urn,
    )

    value = registration.get("value", {})
    asset = value.get("asset")

    upload_url = (
        value.get("uploadMechanism", {})
        .get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {})
        .get("uploadUrl")
    )

    if not asset or not upload_url:
        raise Exception("LinkedIn image upload registration did not return asset/uploadUrl")

    await upload_image_binary_to_linkedin(
        upload_url=upload_url,
        access_token=access_token,
        image_path=image_path,
    )

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
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": image_title
                        },
                        "media": asset,
                        "title": {
                            "text": image_title
                        },
                    }
                ],
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=payload,
        )

        if resp.status_code >= 400:
            raise Exception(
                f"LinkedIn image post failed: {resp.status_code} {resp.text}"
            )

        return {
            "status_code": resp.status_code,
            "post_id": resp.headers.get("X-RestLi-Id"),
            "asset": asset,
            "image_attached": True,
        }