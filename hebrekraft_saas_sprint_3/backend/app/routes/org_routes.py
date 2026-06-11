from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..auth import get_current_user
from ..database import get_db
from ..models import User, OrganizationMember, BrandProfile
from ..schemas import BrandProfileIn

router = APIRouter(prefix='/api/orgs', tags=['organizations'])


@router.get('/mine')
def my_orgs(current_user: User = Depends(get_current_user)):
    return [
        {'organization_id': m.organization_id, 'name': m.organization.name, 'role': m.role}
        for m in current_user.memberships
    ]


def _assert_member(db: Session, user_id: int, org_id: int):
    member = db.query(OrganizationMember).filter_by(user_id=user_id, organization_id=org_id).first()
    if not member:
        raise HTTPException(status_code=403, detail='Not a member of this organization')
    return member


@router.get('/{org_id}/brand')
def get_brand(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, current_user.id, org_id)
    brand = db.query(BrandProfile).filter_by(organization_id=org_id).first()
    return brand or {}


@router.put('/{org_id}/brand')
def upsert_brand(org_id: int, payload: BrandProfileIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, current_user.id, org_id)
    brand = db.query(BrandProfile).filter_by(organization_id=org_id).first()
    data = payload.model_dump()
    if not brand:
        brand = BrandProfile(organization_id=org_id, **data)
        db.add(brand)
    else:
        for k, v in data.items():
            setattr(brand, k, v)
    db.commit()
    db.refresh(brand)
    return {'status': 'saved', 'brand_profile_id': brand.id}
