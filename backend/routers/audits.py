"""
CarbonIQ - Audits Router
CRUD for audit trail records.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Audit, Project
from schemas import AuditCreate, AuditResponse
from services.cdc_service import track_change

router = APIRouter(prefix="/api/audits", tags=["Audits"])


@router.post("/", response_model=AuditResponse)
def create_audit(data: AuditCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    audit = Audit(**data.model_dump())
    db.add(audit)
    db.commit()
    db.refresh(audit)
    track_change(db, "audit", audit.id, "create", new_values=data.model_dump(mode="json"))
    db.commit()
    return audit


@router.get("/project/{project_id}", response_model=List[AuditResponse])
def get_project_audits(project_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Audit)
        .filter(Audit.project_id == project_id)
        .order_by(Audit.audit_date.desc())
        .all()
    )


@router.get("/{audit_id}", response_model=AuditResponse)
def get_audit(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(404, "Audit not found")
    return audit


@router.get("/", response_model=List[AuditResponse])
def list_all_audits(
    reversal_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(Audit)
    if reversal_only:
        q = q.filter(Audit.reversal_event == True)
    return q.order_by(Audit.audit_date.desc()).limit(100).all()
