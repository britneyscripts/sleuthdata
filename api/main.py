import redis
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from core.config import settings
from core.database import engine, Base, get_db
from core.models import SearchQuery, JobListing
from workers.tasks import crawl_query_job

# Import Pydantic models for validation
from pydantic import BaseModel, Field
from datetime import datetime, date

# 1. Initialize Database Tables (Auto-create for MVP)
Base.metadata.create_all(bind=engine)

# Auto-migrate SQLite schema for company_id column if needed
try:
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if 'job_listings' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('job_listings')]
        if 'company_id' not in columns:
            print("INFO: Adding company_id column to job_listings table...")
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE job_listings ADD COLUMN company_id VARCHAR(36) REFERENCES companies(id)"))
except Exception as migrate_err:
    print(f"WARNING: Schema migration failed: {migrate_err}")

# 2. Setup FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A query-driven, config-based job listing aggregator.",
    version="1.0.0"
)

# 3. Setup Task Queue with Graceful Fallback
try:
    redis_conn = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
    redis_conn.ping()
    from rq import Queue
    task_queue = Queue("job_crawler", connection=redis_conn)
    redis_active = True
    print("INFO: Redis Queue (RQ) worker connected successfully.")
except Exception:
    task_queue = None
    redis_active = False
    print("WARNING: Redis not reachable. Falling back to FastAPI BackgroundTasks.")

# --- Pydantic Schemas ---
class SearchQueryCreate(BaseModel):
    keywords: str = Field(..., example="Data Product Manager")
    region: str = Field(..., example="Brazil")
    is_remote_only: bool = Field(True, example=True)

class SearchQueryResponse(BaseModel):
    id: UUID
    keywords: str
    region: str
    is_remote_only: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class JobListingResponse(BaseModel):
    id: UUID
    search_query_id: UUID
    title: str
    company: str
    location_raw: str
    country: str | None
    city: str | None
    is_remote: bool
    description: str
    salary_raw: str | None
    source: str
    source_url: str
    skills_extracted: List[str]
    date_posted: date | None
    created_at: datetime

    # Enriched Company Metrics
    company_rating: float | None = None
    company_salary_avg: float | None = None
    company_has_layoffs: bool | None = None
    company_layoff_details: str | None = None

    class Config:
        from_attributes = True

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "queue_backend": "Redis Queue (RQ)" if redis_active else "FastAPI BackgroundTasks (In-Memory)"
    }

@app.post("/search-queries", response_model=SearchQueryResponse, status_code=210)
def create_search_query(
    query_data: SearchQueryCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Registers a new search query configuration and triggers
    an initial job ingestion task in the background.
    """
    new_query = SearchQuery(
        keywords=query_data.keywords,
        region=query_data.region,
        is_remote_only=query_data.is_remote_only
    )
    db.add(new_query)
    db.commit()
    db.refresh(new_query)

    # Trigger crawl automatically
    if redis_active and task_queue:
        task_queue.enqueue(crawl_query_job, str(new_query.id))
    else:
        background_tasks.add_task(crawl_query_job, str(new_query.id))

    return new_query

@app.get("/search-queries", response_model=List[SearchQueryResponse])
def list_search_queries(db: Session = Depends(get_db)):
    """
    Retrieves all active search query configurations.
    """
    return db.query(SearchQuery).all()

@app.post("/search-queries/{query_id}/crawl")
def trigger_crawler_manually(
    query_id: UUID, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Manually triggers the background scraper worker for a specific query configuration.
    """
    query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Search query not found")

    if redis_active and task_queue:
        task_queue.enqueue(crawl_query_job, str(query.id))
        return {"status": "enqueued", "backend": "Redis Queue"}
    else:
        background_tasks.add_task(crawl_query_job, str(query.id))
        return {"status": "started", "backend": "FastAPI BackgroundTasks"}

@app.get("/jobs", response_model=List[JobListingResponse])
def get_jobs(
    q: str | None = Query(None, description="Keyword search in job titles or descriptions"),
    source: str | None = Query(None, description="Filter by job source board (e.g. gupy, weworkremotely)"),
    is_remote: bool | None = Query(None, description="Filter by remote job status"),
    db: Session = Depends(get_db)
):
    """
    Retrieves job postings with optional filters (text query, source board, remote status).
    """
    query_builder = db.query(JobListing)

    if source:
        query_builder = query_builder.filter(JobListing.source == source.lower().strip())
    
    if is_remote is not None:
        query_builder = query_builder.filter(JobListing.is_remote == is_remote)
        
    if q:
        search_filter = f"%{q.lower().strip()}%"
        query_builder = query_builder.filter(
            (JobListing.title.ilike(search_filter)) | 
            (JobListing.description.ilike(search_filter)) |
            (JobListing.company.ilike(search_filter))
        )

    # Order by newest listings
    return query_builder.order_by(JobListing.date_posted.desc(), JobListing.created_at.desc()).all()
