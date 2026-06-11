from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..auth import get_current_user
from ..config import get_settings
from ..database import get_db
from ..models import User, SocialAccount, OrganizationMember, GeneratedPost
from ..security import encrypt_value, decrypt_value
from ..linkedin_service import linkedin_authorization_url, exchange_code_for_token, fetch_member_profile, publish_text_post

router = APIRouter(prefix='/api/linkedin', tags=['linkedin'])
settings = get_settings()


def _assert_member(db: Session, user_id: int, org_id: int):
    member = db.query(OrganizationMember).filter_by(user_id=user_id, organization_id=org_id).first()
    if not member:
        raise HTTPException(status_code=403, detail='Not a member of this organization')


@router.get('/connect/{org_id}')
def connect_linkedin(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, current_user.id, org_id)
    if not settings.linkedin_client_id:
        raise HTTPException(status_code=400, detail='LINKEDIN_CLIENT_ID is missing')
    state = f'{org_id}:{current_user.id}'
    return {'authorization_url': linkedin_authorization_url(state)}


@router.get('/callback')
async def callback(code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
    try:
        org_id_str, user_id_str = state.split(':', 1)
        org_id, user_id = int(org_id_str), int(user_id_str)
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid OAuth state')
    token = await exchange_code_for_token(code)
    access_token = token.get('access_token')
    profile = await fetch_member_profile(access_token)
    member_urn = f"urn:li:person:{profile.get('sub')}" if profile.get('sub') else ''
    account = db.query(SocialAccount).filter_by(organization_id=org_id, platform='linkedin').first()
    if not account:
        account = SocialAccount(organization_id=org_id, platform='linkedin')
        db.add(account)
    account.account_name = profile.get('name') or profile.get('email') or 'LinkedIn Account'
    account.member_urn = member_urn
    account.encrypted_access_token = encrypt_value(access_token or '')
    account.scopes = settings.linkedin_scopes
    account.connection_status = 'connected'
    db.commit()
    return RedirectResponse(f"{settings.frontend_base_url}?linkedin=connected&org_id={org_id}")


@router.get('/org/{org_id}/status')
def status(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, current_user.id, org_id)
    account = db.query(SocialAccount).filter_by(organization_id=org_id, platform='linkedin').first()
    if not account:
        return {'connected': False}
    return {'connected': account.connection_status == 'connected', 'account_name': account.account_name, 'member_urn': account.member_urn}


@router.post('/publish/{post_id}')
async def publish(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(GeneratedPost).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    _assert_member(db, current_user.id, post.organization_id)
    account = db.query(SocialAccount).filter_by(organization_id=post.organization_id, platform='linkedin', connection_status='connected').first()
    if not account:
        raise HTTPException(status_code=400, detail='LinkedIn is not connected')
    access_token = decrypt_value(account.encrypted_access_token)
    author_urn = account.page_urn or settings.linkedin_default_org_urn or account.member_urn
    if not author_urn:
        raise HTTPException(status_code=400, detail='No LinkedIn author URN found')
    result = await publish_text_post(access_token, author_urn, post.content)
    post.status = 'published'
    db.commit()
    return result
