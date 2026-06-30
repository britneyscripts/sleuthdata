# Document Control
*   **Document Title:** Architecture Decisions & Technology Choices - Query-Driven Job Crawler
*   **Version:** 1.0.0
*   **Status:** Approved
*   **Date:** 2026-06-29
*   **Author:** Bettina Acosta de Paula
*   **Description:** Rationale for selected architectural patterns, database storage engines, frameworks, and job queue choices for the Query-Driven Job Crawler.

## Revision History
| Version | Date | Author | Description of Change |
|---------|------|--------|-----------------------|
| 1.0.0   | 2026-06-29 | Bettina Acosta de Paula | Initial publication of architectural choices and trade-offs. |

---

# Architecture Decisions & Technology Choices

This document outlines the engineering reasoning, trade-offs, and scalability paths behind the core technology choices made for the Query-Driven Job Crawler.

---

## 1. Database Layer: PostgreSQL with JSONB

The crawler must store structured query parameters (user-defined search criteria) alongside highly variable job listing data (salaries, tags, description lengths, dynamic metadata unique to specific boards).

### The Choice
*   **Database Engine:** PostgreSQL
*   **Data Model:** Hybrid Relational and Semi-Structured (`JSONB` columns)

### Why PostgreSQL with JSONB?
*   **The Schema Flexibility of NoSQL:** Job postings scraped from WeWorkRemotely, Gupy, and Google Jobs do not share a single standardized format. Some include detailed salary structures or department tags, while others only provide raw text. Storing these varying fields in a `JSONB` column (`skills_extracted` and `raw_metadata`) allows the database to accept schemas from new spiders without requiring migration scripts for every new source added.
*   **Relational Integrity for User Configs:** User searches (`SearchQuery`) and queue tracking demand traditional relational properties (joins, foreign keys, transaction safety). Postgres excels at both relational schemas and document schemas.
*   **PostGIS & Geospatial Readiness:** Since job seekers often look for hybrid or local-remote jobs, the ability to calculate geospatial distances (e.g., jobs within 50km of São Paulo or Austin) is crucial. Postgres offers **PostGIS**, the industry-standard geospatial extension.

### Trade-offs Considered
*   **Alternative 1: Pure Relational SQL (Strict Table Schema)**
    *   *Downside:* Every time a new job board is added that provides a unique data point (e.g., "Remote stipend allocation"), we would need to run database migrations to alter the tables. This violates the goal of allowing developers to add new sources in under 2 hours.
*   **Alternative 2: NoSQL (MongoDB)**
    *   *Downside:* While Mongo provides total document flexibility, it lacks native support for strict relational integrity when mapping user accounts, query definitions, and stats. It also has a larger resource overhead for small-scale self-hosted setups.

---

## 2. API Framework: FastAPI (Python)

### The Choice
*   FastAPI

### Why FastAPI?
*   **Performance:** Built on top of Starlette and Pydantic, FastAPI is one of the fastest Python frameworks available, leveraging Python's `asyncio` for non-blocking I/O operations.
*   **Auto-generated Interactive Documentation:** FastAPI automatically generates interactive Swagger/OpenAPI documentation (`/docs`). For an open-source project, this drastically reduces developer onboarding time and eases API testing.
*   **Data Validation:** Pydantic models automatically validate incoming requests (e.g., ensuring location inputs, title strings, and keyword formats match requirements).

### Trade-offs Considered
*   **Alternative: Django REST Framework (DRF)**
    *   *Downside:* Django is highly opinionated and brings substantial boilerplate (ORM settings, admin panels, complex settings files). For a lightweight crawler focused on search APIs and simple job listings, Django is excessively heavy. FastAPI keeps the project footprint tiny and fast.

---

## 3. Concurrency & Queue Engine: Redis Queue (RQ)

Because scraping is an I/O-heavy and slow operation, crawls cannot run synchronously within API request-response loops. They must be offloaded to asynchronous background workers.

### The Choice
*   Redis Queue (RQ) + Redis

### Why Redis Queue?
*   **Simplicity and Maintainability:** RQ is a lightweight Python-native queuing library built on top of Redis. It requires very little configuration compared to Celery and integrates seamlessly with standard Python functions.
*   **Infrastructure Overhead:** RQ's memory footprint is extremely small, making it ideal for self-hosted MVPs and local development.
*   **Easy Diagnostics:** Failed jobs are automatically placed in a failed job registry, enabling straightforward error monitoring and retries.

### Trade-offs Considered
*   **Alternative: Celery**
    *   *Downside:* Celery is the industry standard for enterprise Python background tasks, but it is notoriously complex to configure, maintain, and monitor (often requiring RabbitMQ/Redis, event loops, and third-party monitoring tools like Flower). For an open-source MVP, Celery introduces unnecessary architectural friction.

---

## 4. Web Scraping Strategy: Scrapy + Playwright

Scraping job listings requires handling both static APIs/HTML and complex JavaScript-rendered single page applications (SPAs).

### The Choice
*   **API/HTTP-First Scraping (Scrapy/HTTP Client):** Default choice for fast, lightweight crawls.
*   **Headless Browsing (Playwright):** Used selectively as a fallback for JS-heavy or bot-protected sites.

### Why Scrapy & Playwright?
*   **Resource Efficiency:** Scrapy is designed for high-concurrency requests and can process hundreds of pages per minute on a single core.
*   **Selectively Headless:** Playwright is only booted when a site requires browser interaction (e.g., clicking pagination elements, bypass rendering). This saves RAM and CPU.

### Trade-offs Considered
*   **Alternative: Selenium**
    *   *Downside:* Selenium is slower, heavier, and has less robust async support than Playwright, making it harder to coordinate with a FastAPI/asyncio stack.

---

## 5. Deployment Model: Docker Compose

### The Choice
*   Docker Compose

### Why Docker Compose?
*   **Uniform Development Environments:** Ensures that Postgres, Redis, the FastAPI API, and the RQ worker run identically on local developer machines, macOS, Linux, and staging environments.
*   **Zero-Dependency Setup:** An open-source contributor can run `docker-compose up` and have the entire stack running immediately without installing Python, Redis, or PostgreSQL locally.

---

## 6. Future Scalability & Open-Source Roadmap

To ensure this MVP can scale seamlessly into a production-grade open-source system, we have defined the following migration paths:

| Core Component | Current (MVP) | Future Production Upgrade | Reason for Migration |
| :--- | :--- | :--- | :--- |
| **Search Engine** | SQL `LIKE` & `TSVECTOR` (Postgres) | **Elasticsearch / Opensearch** | Provides fast, faceted search auto-completions, fuzzy matching, and handles millions of listings efficiently. |
| **Orchestration** | Docker Compose | **Kubernetes (K8s)** | Allows autoscaling worker pods during peak crawl windows and isolated browser container pools (Playwright). |
| **Deduplication** | Strict Hash-based | **Semantic Vector Similarity (PGVector)** | Matches listings that are conceptually identical but written differently (e.g., "Senior PM" vs. "Senior Product Manager"). |
| **Proxy Management**| Direct Connection | **Rotating Residential Proxy Pool** | Essential to prevent IP bans and Cloudflare blocks when crawling large boards at scale. |
