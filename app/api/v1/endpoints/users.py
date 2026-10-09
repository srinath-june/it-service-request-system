from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["Users & IT Staff"])

@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """List all users with optional role and status filters."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.order_by(User.full_name).all()

@router.get("/it-team", response_model=List[UserResponse])
def list_it_team_members(db: Session = Depends(get_db)):
    """Convenience endpoint returning active IT Support, Managers, and Admins eligible for ticket assignment."""
    return db.query(User).filter(
        User.role.in_([UserRole.IT_SUPPORT, UserRole.IT_MANAGER, UserRole.ADMIN]),
        User.is_active == True
    ).order_by(User.full_name).all()

@router.get("/requesters", response_model=List[UserResponse])
def list_requesters(db: Session = Depends(get_db)):
    """Convenience endpoint returning active employees."""
    return db.query(User).filter(User.is_active == True).order_by(User.full_name).all()

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Create a new user/employee."""
    existing = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username or email already exists."
        )
    user = User(
        username=user_in.username.strip(),
        email=user_in.email.strip(),
        full_name=user_in.full_name.strip(),
        role=user_in.role,
        department=user_in.department,
        is_active=user_in.is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user profile by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
