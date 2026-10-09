from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Request Categories"])

@router.get("", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """List all active and configured request categories."""
    return db.query(Category).order_by(Category.name).all()

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category_in: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category (e.g. Hardware, Software, Network)."""
    existing = db.query(Category).filter(Category.name.ilike(category_in.name.strip())).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category_in.name}' already exists."
        )
    cat = Category(
        name=category_in.name.strip(),
        description=category_in.description,
        is_active=category_in.is_active
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, cat_in: CategoryUpdate, db: Session = Depends(get_db)):
    """Update category properties or toggle active status."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    if cat_in.name:
        cat.name = cat_in.name.strip()
    if cat_in.description is not None:
        cat.description = cat_in.description
    if cat_in.is_active is not None:
        cat.is_active = cat_in.is_active
    db.commit()
    db.refresh(cat)
    return cat
