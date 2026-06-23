from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Import database and models
from app.database import get_db
from app.models import InventoryItem

router = APIRouter(tags=["inventory"])


# Pydantic Schemas
class InventoryItemSchema(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    brand: str = Field(..., min_length=1, max_length=150)
    quantity: float = Field(..., ge=0)
    unit: str = Field(default="un", max_length=10)
    type: str = Field(..., max_length=100)
    observations: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginationResponse(BaseModel):
    page: int
    per_page: int
    total: int
    pages: int


class InventoryListResponse(BaseModel):
    success: bool = True
    data: List[InventoryItemSchema]
    pagination: PaginationResponse


class InventoryDetailResponse(BaseModel):
    success: bool = True
    data: InventoryItemSchema


class InventoryItemUpdateSchema(BaseModel):
    """Schema for updating inventory items - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = Field(None, min_length=1, max_length=150)
    quantity: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=10)
    type: Optional[str] = Field(None, max_length=100)
    observations: Optional[str] = None

    class Config:
        from_attributes = True


# Routes
@router.get("/inventory", response_model=InventoryListResponse)
async def get_inventory(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all inventory items with pagination and filtering.
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)
    - search: Search by name or brand
    - type: Filter by product type
    """
    try:
        query = db.query(InventoryItem)
        
        # Apply search filter
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    InventoryItem.name.ilike(search_term),
                    InventoryItem.brand.ilike(search_term)
                )
            )
        
        # Apply type filter
        if type:
            query = query.filter(InventoryItem.type == type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        skip = (page - 1) * per_page
        items = query.order_by(desc(InventoryItem.created_at)).offset(skip).limit(per_page).all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "success": True,
            "data": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": total_pages
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/{item_id}", response_model=InventoryDetailResponse)
async def get_inventory_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific inventory item by ID."""
    try:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return {
            "success": True,
            "data": item
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inventory", response_model=InventoryDetailResponse, status_code=201)
async def create_inventory_item(
    item: InventoryItemSchema,
    db: Session = Depends(get_db)
):
    """Create a new inventory item."""
    try:
        # Check if item with same name already exists
        existing = db.query(InventoryItem).filter(
            InventoryItem.name == item.name.strip()
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Product name already exists")
        
        # Create new item
        db_item = InventoryItem(
            name=item.name.strip(),
            brand=item.brand.strip(),
            quantity=item.quantity,
            unit=item.unit,
            type=item.type.strip(),
            observations=item.observations.strip() if item.observations else None
        )
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        return {
            "success": True,
            "data": db_item
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/inventory/{item_id}", response_model=InventoryDetailResponse)
async def update_inventory_item(
    item_id: int,
    item_update: InventoryItemUpdateSchema,
    db: Session = Depends(get_db)
):
    """Update an existing inventory item."""
    try:
        # Get existing item
        db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Update fields only if provided
        if item_update.name is not None:
            db_item.name = item_update.name.strip()
        if item_update.brand is not None:
            db_item.brand = item_update.brand.strip()
        if item_update.quantity is not None:
            db_item.quantity = item_update.quantity
        if item_update.unit is not None:
            db_item.unit = item_update.unit
        if item_update.type is not None:
            db_item.type = item_update.type.strip()
        if item_update.observations is not None:
            db_item.observations = item_update.observations.strip() if item_update.observations else None
        
        # Update timestamp
        db_item.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_item)
        
        return {
            "success": True,
            "data": db_item
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/inventory/{item_id}", status_code=204)
async def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Delete an inventory item."""
    try:
        # Get existing item
        db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Delete item
        db.delete(db_item)
        db.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
