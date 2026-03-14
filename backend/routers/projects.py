"""
CarbonIQ - Projects Router
CRUD + filtered listing for carbon projects.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import Project, Vintage, RiskSignal, Audit
from schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetail
from services.cdc_service import track_change

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    track_change(db, "project", project.id, "create", new_values=data.model_dump())
    db.commit()
    return project


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    registry: Optional[str] = Query(None),
    project_type: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    q = db.query(Project)
    if registry:
        q = q.filter(Project.registry == registry)
    if project_type:
        q = q.filter(Project.project_type == project_type)
    if country:
        q = q.filter(Project.country == country)
    if status:
        q = q.filter(Project.status == status)

    return q.order_by(Project.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    vintages = db.query(Vintage).filter(Vintage.project_id == project_id).order_by(Vintage.issuance_year).all()
    risk_signals = db.query(RiskSignal).filter(RiskSignal.project_id == project_id).order_by(RiskSignal.timestamp.desc()).all()
    audits = db.query(Audit).filter(Audit.project_id == project_id).order_by(Audit.audit_date.desc()).all()

    result = ProjectDetail.model_validate(project)
    result.vintages = vintages
    result.risk_signals = risk_signals
    result.audits = audits
    return result


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    update_data = data.model_dump(exclude_unset=True)
    old_values = {}
    changed_fields = []

    for field, value in update_data.items():
        old_val = getattr(project, field, None)
        if old_val != value:
            old_values[field] = old_val
            changed_fields.append(field)
            setattr(project, field, value)

    if changed_fields:
        track_change(db, "project", project_id, "update",
                     changed_fields=changed_fields,
                     old_values=old_values,
                     new_values=update_data)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    track_change(db, "project", project_id, "delete")
    project.status = "deleted"
    db.commit()
    return {"status": "deleted", "project_id": project_id}
