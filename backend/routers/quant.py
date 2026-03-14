"""
CarbonIQ - Quant Engine Router
Fair-value pricing, arbitrage detection, and portfolio valuation endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Project, Vintage, RiskSignal, Audit
from schemas import FairValueResult, ArbitrageOpportunity, PortfolioValuation
from services.quant_engine import price_project, detect_arbitrage_opportunities

router = APIRouter(prefix="/api/quant", tags=["Quant Engine"])


def _get_pricing_inputs(project, db: Session) -> dict:
    """Gather all inputs needed for pricing a project."""
    # Latest risk signal
    risk = (
        db.query(RiskSignal)
        .filter(RiskSignal.project_id == project.id)
        .order_by(RiskSignal.timestamp.desc())
        .first()
    )

    # Aggregate vintage data
    vintages = db.query(Vintage).filter(Vintage.project_id == project.id).all()
    total_volume = sum(v.total_volume for v in vintages)
    available_volume = sum(v.available_volume for v in vintages)
    avg_price = sum(v.price_per_tonne for v in vintages if v.price_per_tonne) / max(1, len([v for v in vintages if v.price_per_tonne]))
    avg_velocity = sum(v.retirement_velocity for v in vintages) / max(1, len(vintages))

    # Latest audit quality
    latest_audit = (
        db.query(Audit)
        .filter(Audit.project_id == project.id)
        .order_by(Audit.audit_date.desc())
        .first()
    )
    audit_quality = latest_audit.audit_quality_score if latest_audit else 70.0

    return {
        "project_id": project.id,
        "project_name": project.name,
        "registry": project.registry,
        "project_type": project.project_type,
        "market_price": round(avg_price, 2),
        "additionality_score": risk.additionality_score if risk else 65.0,
        "audit_quality_score": audit_quality,
        "buffer_pool_percent": project.buffer_pool_percent or 0,
        "retirement_velocity": avg_velocity,
        "total_volume": total_volume,
        "available_volume": available_volume,
        "reversal_risk": risk.reversal_risk if risk else 30.0,
        "wildfire_proximity": risk.wildfire_proximity if risk else 20.0,
        "political_risk": risk.political_risk_score if risk else 40.0,
    }


@router.get("/fair-value/{project_id}", response_model=FairValueResult)
def get_fair_value(project_id: str, db: Session = Depends(get_db)):
    """Compute fair value per tonne for a specific project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    inputs = _get_pricing_inputs(project, db)
    result = price_project(**inputs)
    return result


@router.get("/portfolio", response_model=PortfolioValuation)
def get_portfolio_valuation(
    registry: Optional[str] = Query(None),
    project_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Portfolio-level risk-adjusted valuation across all or filtered projects."""
    q = db.query(Project).filter(Project.status == "active")
    if registry:
        q = q.filter(Project.registry == registry)
    if project_type:
        q = q.filter(Project.project_type == project_type)

    projects = q.all()
    if not projects:
        raise HTTPException(404, "No active projects found")

    positions = []
    risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    total_volume = 0
    total_market = 0.0
    total_fair = 0.0
    risk_scores = []

    for project in projects:
        inputs = _get_pricing_inputs(project, db)
        result = price_project(**inputs)
        positions.append(result)

        # Get latest risk for distribution
        risk = (
            db.query(RiskSignal)
            .filter(RiskSignal.project_id == project.id)
            .order_by(RiskSignal.timestamp.desc())
            .first()
        )
        if risk:
            rating = risk.overall_risk_rating
            if rating in risk_distribution:
                risk_distribution[rating] += 1
            risk_scores.append(risk.composite_score)

        total_volume += inputs["total_volume"]
        total_market += inputs["market_price"] * inputs["total_volume"]
        total_fair += result["fair_value"] * inputs["total_volume"]

    return PortfolioValuation(
        total_projects=len(projects),
        total_volume=total_volume,
        total_market_value=round(total_market, 2),
        total_fair_value=round(total_fair, 2),
        portfolio_alpha=round(total_fair - total_market, 2),
        avg_risk_score=round(sum(risk_scores) / max(1, len(risk_scores)), 2),
        risk_distribution=risk_distribution,
        positions=positions,
    )


@router.get("/arbitrage", response_model=List[ArbitrageOpportunity])
def get_arbitrage_opportunities(
    min_alpha: float = Query(10.0, description="Minimum alpha % to qualify"),
    db: Session = Depends(get_db),
):
    """Detect undervalued credits: projects where fair value >> market price."""
    projects = db.query(Project).filter(Project.status == "active").all()

    valuations = []
    for project in projects:
        inputs = _get_pricing_inputs(project, db)
        result = price_project(**inputs)
        result["breakdown"]["project_type"] = project.project_type
        valuations.append(result)

    opportunities = detect_arbitrage_opportunities(valuations, min_alpha)

    # Enrich with project details
    for opp in opportunities:
        project = db.query(Project).filter(Project.id == opp["project_id"]).first()
        if project:
            opp["country"] = project.country
            opp["project_type"] = project.project_type
            risk = (
                db.query(RiskSignal)
                .filter(RiskSignal.project_id == project.id)
                .order_by(RiskSignal.timestamp.desc())
                .first()
            )
            opp["risk_rating"] = risk.overall_risk_rating if risk else "UNKNOWN"

    return opportunities
