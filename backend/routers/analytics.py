"""
CarbonIQ - Analytics Router
Aggregated dashboard data, risk distributions, and CDC history.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
from models import Project, Vintage, RiskSignal, CDCLog, CrawlRun
from schemas import DashboardSummary, CDCLogResponse, DocumentSearchResult
from services.vector_service import vector_service
from services.pdf_parser import extract_pdd_data
from typing import List

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Aggregated dashboard statistics."""
    total_projects = db.query(Project).filter(Project.status == "active").count()

    # Volume stats
    volume_stats = db.query(
        func.coalesce(func.sum(Vintage.total_volume), 0),
        func.coalesce(func.sum(Vintage.retired_volume), 0),
    ).first()
    total_issued = int(volume_stats[0])
    total_retired = int(volume_stats[1])

    # Market value
    vintages = db.query(Vintage).all()
    total_market_value = sum(
        (v.price_per_tonne or 0) * v.available_volume for v in vintages
    )
    prices = [v.price_per_tonne for v in vintages if v.price_per_tonne and v.price_per_tonne > 0]
    avg_price = sum(prices) / max(1, len(prices))

    # Registry breakdown
    registry_counts = (
        db.query(Project.registry, func.count(Project.id))
        .filter(Project.status == "active")
        .group_by(Project.registry)
        .all()
    )
    registry_breakdown = {r: c for r, c in registry_counts}

    # Risk distribution
    risk_counts = (
        db.query(RiskSignal.overall_risk_rating, func.count(RiskSignal.id))
        .group_by(RiskSignal.overall_risk_rating)
        .all()
    )
    risk_distribution = {r: c for r, c in risk_counts}

    # Project type breakdown
    type_counts = (
        db.query(Project.project_type, func.count(Project.id))
        .filter(Project.status == "active")
        .group_by(Project.project_type)
        .all()
    )
    project_type_breakdown = {t: c for t, c in type_counts}

    # Recent crawls
    recent_crawls = (
        db.query(CrawlRun)
        .order_by(CrawlRun.started_at.desc())
        .limit(5)
        .all()
    )

    return DashboardSummary(
        total_projects=total_projects,
        total_credits_issued=total_issued,
        total_credits_retired=total_retired,
        total_market_value=round(total_market_value, 2),
        avg_price_per_tonne=round(avg_price, 2),
        registry_breakdown=registry_breakdown,
        risk_distribution=risk_distribution,
        project_type_breakdown=project_type_breakdown,
        recent_crawls=recent_crawls,
    )


@router.get("/risk-distribution")
def get_risk_distribution(db: Session = Depends(get_db)):
    """Detailed risk distribution across projects."""
    signals = db.query(RiskSignal).all()
    
    distribution = {
        "overall": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        "by_factor": {
            "wildfire": {"low": 0, "medium": 0, "high": 0},
            "deforestation": {"low": 0, "medium": 0, "high": 0},
            "political": {"low": 0, "medium": 0, "high": 0},
            "reversal": {"low": 0, "medium": 0, "high": 0},
        },
        "composite_histogram": [],
    }
    
    composites = []
    for s in signals:
        if s.overall_risk_rating in distribution["overall"]:
            distribution["overall"][s.overall_risk_rating] += 1
        composites.append(s.composite_score)
        
        # Factor-level bucketing
        for factor, value in [
            ("wildfire", s.wildfire_proximity),
            ("deforestation", s.deforestation_rate),
            ("political", s.political_risk_score),
            ("reversal", s.reversal_risk),
        ]:
            if value < 30:
                distribution["by_factor"][factor]["low"] += 1
            elif value < 60:
                distribution["by_factor"][factor]["medium"] += 1
            else:
                distribution["by_factor"][factor]["high"] += 1
    
    # Create histogram buckets
    if composites:
        for bucket_start in range(0, 100, 10):
            count = len([c for c in composites if bucket_start <= c < bucket_start + 10])
            distribution["composite_histogram"].append({
                "range": f"{bucket_start}-{bucket_start + 10}",
                "count": count,
            })
    
    return distribution


@router.get("/registry-breakdown")
def get_registry_breakdown(db: Session = Depends(get_db)):
    """Volume and value breakdown per registry."""
    registries = db.query(Project.registry).distinct().all()
    
    breakdown = []
    for (registry,) in registries:
        projects = db.query(Project).filter(Project.registry == registry, Project.status == "active").all()
        project_ids = [p.id for p in projects]
        
        vintages = db.query(Vintage).filter(Vintage.project_id.in_(project_ids)).all() if project_ids else []
        
        total_volume = sum(v.total_volume for v in vintages)
        retired_volume = sum(v.retired_volume for v in vintages)
        avg_price = sum(v.price_per_tonne for v in vintages if v.price_per_tonne) / max(1, len([v for v in vintages if v.price_per_tonne]))
        market_value = sum((v.price_per_tonne or 0) * v.available_volume for v in vintages)
        
        breakdown.append({
            "registry": registry,
            "project_count": len(projects),
            "total_volume": total_volume,
            "retired_volume": retired_volume,
            "avg_price": round(avg_price, 2),
            "market_value": round(market_value, 2),
        })
    
    return breakdown


@router.get("/cdc-log", response_model=List[CDCLogResponse])
def get_cdc_log(
    limit: int = Query(50, le=200),
    entity_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get recent change data capture log entries."""
    q = db.query(CDCLog)
    if entity_type:
        q = q.filter(CDCLog.entity_type == entity_type)
    return q.order_by(CDCLog.timestamp.desc()).limit(limit).all()


@router.get("/document-search", response_model=List[DocumentSearchResult])
def search_documents(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, le=20),
):
    """Search indexed PDD and methodology documents by semantic similarity."""
    results = vector_service.search_similar(query, top_k)
    return [
        DocumentSearchResult(
            doc_id=r["doc_id"],
            title=r["title"],
            similarity=r["similarity"],
            content_summary=r["content_summary"],
        )
        for r in results
    ]


@router.post("/index-documents")
def index_project_documents(db: Session = Depends(get_db)):
    """Index all project PDDs for similarity search."""
    projects = db.query(Project).filter(Project.status == "active").all()
    indexed = 0
    
    for project in projects:
        extract_pdd_data(project.name, project.project_type, project.country)
        indexed += 1
    
    return {
        "status": "completed",
        "documents_indexed": indexed,
        "index_stats": vector_service.get_stats(),
    }
