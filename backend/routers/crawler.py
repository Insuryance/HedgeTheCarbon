"""
CarbonIQ - Crawler Router
Trigger and monitor simulated registry crawls.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import CrawlRun
from schemas import CrawlRunResponse, CrawlTriggerRequest
from services.crawler_service import run_crawl

router = APIRouter(prefix="/api/crawler", tags=["Crawler"])


@router.post("/run", response_model=dict)
def trigger_crawl(request: CrawlTriggerRequest = None, db: Session = Depends(get_db)):
    """Trigger a simulated registry crawl."""
    if request is None:
        request = CrawlTriggerRequest()
    result = run_crawl(db, request.registries)
    return result


@router.get("/status", response_model=List[CrawlRunResponse])
def get_crawl_status(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent crawl run history."""
    runs = (
        db.query(CrawlRun)
        .order_by(CrawlRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return runs
