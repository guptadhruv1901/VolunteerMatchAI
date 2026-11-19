from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Profile
from app.schemas.api import ProfileCreate, ProfileUpdate

def list_profiles(db: Session):
    return list(db.scalars(select(Profile).order_by(Profile.id)))
def get_profile(db: Session, profile_id: int):
    return db.get(Profile, profile_id)
def create_profile(db: Session, data: ProfileCreate):
    profile = Profile(**data.model_dump())
    db.add(profile)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "A profile with this email already exists.") from error
    db.refresh(profile)
    return profile
def update_profile(db: Session, profile: Profile, data: ProfileUpdate):
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.commit(); db.refresh(profile)
    return profile
def delete_profile(db: Session, profile: Profile):
    db.delete(profile); db.commit()
