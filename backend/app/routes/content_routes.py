import os
import uuid
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..auth import get_current_user
from ..database import get_db
from ..models import User, OrganizationMember, BrandProfile, GeneratedPost
from ..schemas import GeneratePostRequest, SchedulePostRequest, PostOut
from ..ai_engine import generate_post_pipeline
from pydantic import BaseModel

class UpdatePostRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    image_prompt: str | None = None

router = APIRouter(prefix='/api/content', tags=['content'])

def _assert_member(db: Session, user_id: int, org_id: int):
    member = db.query(OrganizationMember).filter_by(user_id=user_id, organization_id=org_id).first()
    if not member:
        raise HTTPException(status_code=403, detail='Not a member of this organization')
    
class UpdatePostRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    image_prompt: str | None = None
    status: str | None = None


class RewritePostRequest(BaseModel):
    instruction: str

@router.post('/generate', response_model=PostOut)
def generate(payload: GeneratePostRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, current_user.id, payload.organization_id)
    brand = db.query(BrandProfile).filter_by(organization_id=payload.organization_id).first()
    if not brand:
        raise HTTPException(status_code=400, detail='Create brand profile first')
    result = generate_post_pipeline(brand, payload.topic, payload.extra_focus, payload.extra_avoid)
    post = GeneratedPost(
        organization_id=payload.organization_id,
        title=result.get('title', ''),
        content=result.get('content', ''),
        image_title=result.get('image_title', ''),
        image_subtitle=result.get('image_subtitle', ''),
        image_path=result.get('image_path', ''),
        topic=payload.topic,
        status='draft',
        ai_metadata=result.get('ai_metadata', {}),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.get('/org/{org_id}/posts', response_model=list[PostOut])
def list_posts(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, current_user.id, org_id)
    return db.query(GeneratedPost).filter_by(organization_id=org_id).order_by(GeneratedPost.created_at.desc()).all()

@router.put('/posts/{post_id}', response_model=PostOut)
def update_post(
    post_id: int,
    payload: UpdatePostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(GeneratedPost).filter_by(id=post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail='Post not found')

    _assert_member(db, current_user.id, post.organization_id)

    if payload.title is not None:
        post.title = payload.title

    if payload.content is not None:
        post.content = payload.content

    if payload.image_prompt is not None:
        post.image_title = payload.image_prompt[:120]
        post.image_subtitle = payload.image_prompt

    post.status = 'draft'

    db.commit()
    db.refresh(post)

    return post

@router.put('/posts/{post_id}', response_model=PostOut)
def update_post(
    post_id: int,
    payload: UpdatePostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(GeneratedPost).filter_by(id=post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail='Post not found')

    _assert_member(db, current_user.id, post.organization_id)

    if payload.title is not None:
        post.title = payload.title

    if payload.content is not None:
        post.content = payload.content

    if payload.image_prompt is not None:
        post.image_title = payload.image_prompt[:120]
        post.image_subtitle = payload.image_prompt

    if payload.status is not None:
        post.status = payload.status
    else:
        post.status = 'draft'

    db.commit()
    db.refresh(post)

    return post


@router.delete('/posts/{post_id}')
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(GeneratedPost).filter_by(id=post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail='Post not found')

    _assert_member(db, current_user.id, post.organization_id)

    db.delete(post)
    db.commit()

    return {'deleted': True, 'post_id': post_id}


@router.post('/posts/{post_id}/upload-image', response_model=PostOut)
async def upload_post_image(
    post_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(GeneratedPost).filter_by(id=post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail='Post not found')

    _assert_member(db, current_user.id, post.organization_id)

    os.makedirs('/tmp/hebrekraft_uploads', exist_ok=True)

    ext = os.path.splitext(file.filename or '')[1].lower() or '.png'
    filename = f'post_{post_id}_{uuid.uuid4().hex}{ext}'
    path = os.path.join('/tmp/hebrekraft_uploads', filename)

    content = await file.read()
    with open(path, 'wb') as f:
        f.write(content)

    post.image_path = path
    post.status = 'draft'

    db.commit()
    db.refresh(post)

    return post


@router.get('/posts/{post_id}/image')
def get_post_image(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(GeneratedPost).filter_by(id=post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail='Post not found')

    _assert_member(db, current_user.id, post.organization_id)

    if not post.image_path or not os.path.exists(post.image_path):
        raise HTTPException(status_code=404, detail='Image not found')

    return FileResponse(post.image_path)

@router.post('/schedule')
def schedule(payload: SchedulePostRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(GeneratedPost).filter_by(id=payload.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    _assert_member(db, current_user.id, post.organization_id)
    post.scheduled_time = payload.scheduled_time
    post.status = 'scheduled'
    db.commit()
    return {'status': 'scheduled', 'post_id': post.id, 'scheduled_time': post.scheduled_time}
