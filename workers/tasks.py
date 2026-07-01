import uuid
from datetime import datetime
from core.database import SessionLocal
from core.models import SearchQuery, JobListing, Company
from core.deduper import calculate_canonical_hash, clean_string
from core.normalizer import parse_remote_status, normalize_location
from spiders.wworkremotely import WeWorkRemotelySpider
from spiders.gupy import GupySpider
from spiders.target_company import TargetCompanySpider

def crawl_query_job(query_id: str):
    """
    Background job triggered by Redis Queue or FastAPI BackgroundTasks.
    Instantiates spiders, queries job portals, parses results,
    normalizes data, deduplicates, and saves listings to the database.
    """
    db = SessionLocal()
    try:
        # 1. Fetch the active query configuration
        query = db.query(SearchQuery).filter(SearchQuery.id == uuid.UUID(query_id)).first()
        if not query or not query.is_active:
            print(f"Query {query_id} not found or is inactive. Skipping crawl.")
            return

        print(f"Starting crawl for query: {query.keywords} | Region: {query.region}")

        # 2. Instantiate spiders
        spiders = [
            WeWorkRemotelySpider(),
            GupySpider(),
            TargetCompanySpider()
        ]

        jobs_collected = []
        for spider in spiders:
            print(f"Running spider: {spider.name}")
            try:
                raw_jobs = spider.search(keywords=query.keywords, region=query.region)
                print(f"Spider {spider.name} found {len(raw_jobs)} raw postings.")
                
                # Tag the source of the jobs collected
                for job in raw_jobs:
                    job["source"] = spider.name
                    jobs_collected.append(job)
            except Exception as spider_err:
                print(f"Error executing spider {spider.name}: {spider_err}")

        # 3. Process and ingest jobs into database (Dialect-agnostic ORM logic)
        new_jobs_count = 0
        updated_jobs_count = 0
        aggregators = {"weworkremotely", "gupy", "builtin", "clutch", "awwwards"}

        seen_hashes_in_batch = set()

        for job in jobs_collected:
            title = job["title"]
            company_name = job["company"]
            location_raw = job["location_raw"]
            
            # Normalization
            is_remote = parse_remote_status(location_raw)
            city, country = normalize_location(location_raw)
            canonical_hash = calculate_canonical_hash(title, company_name, is_remote)

            # Deduplicate within the current ingestion batch to prevent unique constraint failures
            if canonical_hash in seen_hashes_in_batch:
                continue
            seen_hashes_in_batch.add(canonical_hash)

            # Resolve Company (Find or Create)
            normalized_company = clean_string(company_name)
            comp_obj = db.query(Company).filter(Company.normalized_name == normalized_company).first()
            if not comp_obj:
                comp_obj = Company(name=company_name, normalized_name=normalized_company)
                db.add(comp_obj)
                db.commit()
                db.refresh(comp_obj)

            # Check if company needs enrichment (every 7 days)
            should_enrich = False
            if not comp_obj.last_enriched_at:
                should_enrich = True
            else:
                delta = datetime.utcnow() - comp_obj.last_enriched_at
                if delta.days >= 7:
                    should_enrich = True
            
            if should_enrich:
                from core.enricher import enrich_company_insights
                try:
                    enrich_company_insights(comp_obj, db)
                except Exception as enrich_err:
                    print(f"Error enriching company {comp_obj.name}: {enrich_err}")

            # Query existing job to verify if it is a duplicate
            existing_job = db.query(JobListing).filter(JobListing.canonical_hash == canonical_hash).first()
            
            if existing_job:
                # Merge logic: if existing is aggregator and new is direct Careers page, prioritize direct
                is_new_direct = job["source"] not in aggregators
                is_existing_direct = existing_job.source not in aggregators

                if is_new_direct and not is_existing_direct:
                    existing_job.source_url = job["source_url"]
                    existing_job.source = job["source"]
                    existing_job.description = job["description"]

                # Update common variable fields
                existing_job.date_posted = job["date_posted"]
                existing_job.company_id = comp_obj.id
                updated_jobs_count += 1
            else:
                # Create a new listing record
                new_job = JobListing(
                    search_query_id=query.id,
                    company_id=comp_obj.id,
                    title=title,
                    company=company_name,
                    location_raw=location_raw,
                    country=country,
                    city=city,
                    is_remote=is_remote,
                    description=job["description"],
                    salary_raw=job["salary_raw"],
                    source=job["source"],
                    source_url=job["source_url"],
                    canonical_hash=canonical_hash,
                    skills_extracted=[], # default empty list
                    date_posted=job["date_posted"]
                )
                db.add(new_job)
                new_jobs_count += 1

        db.commit()
        print(f"Crawl completed. Ingested {new_jobs_count} new jobs, updated {updated_jobs_count} jobs.")

    except Exception as e:
        db.rollback()
        print(f"Critical error executing crawl_query_job: {e}")
        raise e
    finally:
        db.close()
