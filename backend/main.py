"""
CarbonIQ - Main Application
FastAPI entry point with all routers, CORS, static files, and auto-seeding.
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base, SessionLocal
from models import Project

# ─── Import Routers ──────────────────────────────────────────────
from routers import projects, vintages, risk_signals, audits, quant, crawler, analytics

# ─── Create App ──────────────────────────────────────────────────
app = FastAPI(
    title="CarbonIQ",
    description="AI-Native Quant Engine for Voluntary Carbon Markets",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ───────────────────────────────────────────
app.include_router(projects.router)
app.include_router(vintages.router)
app.include_router(risk_signals.router)
app.include_router(audits.router)
app.include_router(quant.router)
app.include_router(crawler.router)
app.include_router(analytics.router)

# ─── Static Files (Frontend) ────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
def serve_frontend():
    """Serve the frontend dashboard."""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "CarbonIQ API is running. Visit /docs for API documentation."}


# ─── Startup Event ──────────────────────────────────────────────
@app.on_event("startup")
def startup():
    """Create tables and seed data if empty."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        count = db.query(Project).count()
        if count == 0:
            print("[CarbonIQ] No data found. Running initial registry crawl...")
            from services.crawler_service import run_crawl
            result = run_crawl(db)
            print(f"[CarbonIQ] Seeded {result['total_new']} projects from {result['registries_crawled']} registries.")

            # Index documents for vector search
            from services.pdf_parser import extract_pdd_data
            projects = db.query(Project).all()
            for p in projects:
                extract_pdd_data(p.name, p.project_type, p.country)
            print(f"[CarbonIQ] Indexed {len(projects)} project documents for similarity search.")
        else:
            print(f"[CarbonIQ] Found {count} existing projects. Skipping seed.")
    finally:
        db.close()

    print("[CarbonIQ] Server ready at http://localhost:8000")
    print("[CarbonIQ] API docs at http://localhost:8000/docs")
    print("[CarbonIQ] Dashboard at http://localhost:8000")


# ─── Run ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
