"""
CarbonIQ - Vintages Router
CRUD for credit vintages linked to projects.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Vintage, Project
from schemas import VintageCreate, VintageResponse
from services.cdc_service import track_change

router = APIRouter(prefix="/api/vintages", tags=["Vintages"])


@router.post("/", response_model=VintageResponse)
def create_vintage(data: VintageCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    vintage = Vintage(**data.model_dump())
    db.add(vintage)
    db.commit()
    db.refresh(vintage)
    track_change(db, "vintage", vintage.id, "create", new_values=data.model_dump())
    db.commit()
    return vintage


@router.get("/", response_model=List[VintageResponse])
def list_vintages(
    project_id: Optional[str] = Query(None),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Vintage)
    if project_id:
        q = q.filter(Vintage.project_id == project_id)
    if min_year:
        q = q.filter(Vintage.issuance_year >= min_year)
    if max_year:
        q = q.filter(Vintage.issuance_year <= max_year)

    return q.order_by(Vintage.issuance_year.desc()).all()


@router.get("/{vintage_id}", response_model=VintageResponse)
def get_vintage(vintage_id: str, db: Session = Depends(get_db)):
    vintage = db.query(Vintage).filter(Vintage.id == vintage_id).first()
    if not vintage:
        raise HTTPException(404, "Vintage not found")
    return vintage


@router.delete("/{vintage_id}")
def delete_vintage(vintage_id: str, db: Session = Depends(get_db)):
    vintage = db.query(Vintage).filter(Vintage.id == vintage_id).first()
    if not vintage:
        raise HTTPException(404, "Vintage not found")

    track_change(db, "vintage", vintage_id, "delete")
    db.delete(vintage)
    db.commit()
    return {"status": "deleted", "vintage_id": vintage_id}
