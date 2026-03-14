"""
CarbonIQ - Risk Signals Router
Ingestion, computation, and querying of project risk signals.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Project, RiskSignal, Audit
from schemas import RiskSignalCreate, RiskSignalResponse
from services.risk_engine import compute_full_risk, compute_overall_risk_rating, compute_composite_risk
from services.cdc_service import track_change

router = APIRouter(prefix="/api/risk-signals", tags=["Risk Signals"])


@router.post("/", response_model=RiskSignalResponse)
def create_risk_signal(data: RiskSignalCreate, db: Session = Depends(get_db)):
    """Manually ingest a risk signal."""
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    # Compute derived fields
    composite = compute_composite_risk(
        data.wildfire_proximity, data.deforestation_rate,
        data.political_risk_score, data.additionality_score,
        data.reversal_risk, data.buffer_pool_health
    )
    rating = compute_overall_risk_rating(composite)

    signal = RiskSignal(
        **data.model_dump(),
        overall_risk_rating=rating,
        composite_score=composite,
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


@router.get("/{project_id}", response_model=List[RiskSignalResponse])
def get_risk_signals(project_id: str, db: Session = Depends(get_db)):
    """Get all risk signals for a project, most recent first."""
    signals = (
        db.query(RiskSignal)
        .filter(RiskSignal.project_id == project_id)
        .order_by(RiskSignal.timestamp.desc())
        .all()
    )
    return signals


@router.post("/compute/{project_id}", response_model=RiskSignalResponse)
def compute_risk_signal(project_id: str, db: Session = Depends(get_db)):
    """Trigger fresh risk computation for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    audits = db.query(Audit).filter(Audit.project_id == project_id).all()
    risk_data = compute_full_risk(project, audits)

    signal = RiskSignal(**risk_data)
    db.add(signal)
    db.commit()
    db.refresh(signal)

    track_change(db, "risk_signal", signal.id, "create", new_values=risk_data)
    db.commit()
    return signal


@router.get("/latest/{project_id}", response_model=RiskSignalResponse)
def get_latest_risk(project_id: str, db: Session = Depends(get_db)):
    """Get the most recent risk signal for a project."""
    signal = (
        db.query(RiskSignal)
        .filter(RiskSignal.project_id == project_id)
        .order_by(RiskSignal.timestamp.desc())
        .first()
    )
    if not signal:
        raise HTTPException(404, "No risk signals found for this project")
    return signal
