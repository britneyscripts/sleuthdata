# Document Control
*   **Document Title:** Product Requirements Document (PRD) - Query-Driven Job Crawler
*   **Version:** 1.0.0
*   **Status:** Approved
*   **Date:** 2026-06-29
*   **Author:** Bettina Acosta de Paula
*   **Description:** Specifications for an open-source, configuration-driven remote job crawler focusing on tech and product roles.

## Revision History
| Version | Date | Author | Description of Change |
|---------|------|--------|-----------------------|
| 1.0.0   | 2026-06-29 | Bettina Acosta de Paula | Initial publication with query-driven scoping and tech/PM focus. |

---

# Open Source Query-Driven Job Crawler PRD

## Overview
An open-source, configuration-driven job crawler designed to dynamically aggregate job postings based on personalized search queries. Rather than crawling entire job boards, this tool operates on user-defined search parameters (e.g., specific job titles, locations, and regions) to collect relevant postings. It aims to help job seekers find remote roles across Brazil, LATAM, and USA/Canada, and integrate these postings into career-optimization engines (like resume tailoring and ATS scanners).

---

## Problem Statement
Job search platforms are fragmented, have aggressive anti-bot protections, and present job descriptions in highly inconsistent formats. Manual search across multiple regions (such as searching for remote Product Manager roles in LATAM and the US simultaneously) is tedious. A centralized, query-driven crawler collects targeted job listings, normalizes the data, and exposes it through a clean API for personal tracking and analysis.

---

## Target Users
*   **Job Seekers:** Want to find and track specific roles (e.g., *Product Manager*, *Data Product Manager*, *Lead Product Manager*) matching their exact criteria across multiple locations/remote filters.
*   **Developers/Maintainers:** Want to add new scrapers, write custom scrapers for localized boards, or build third-party integrations (e.g., Slack notifications, resume-tailoring pipelines).
*   **Researchers/Analysts:** Export clean job-market data to analyze hiring trends and skill requirements.

---

## Product Goals & Objectives
1.  **Precision Aggregation:** Target search results from high-value sources rather than brute-force site scraping.
2.  **Extensibility:** Provide a standard plugin/spider scaffold allowing developers to add a new job source in less than 2 hours.
3.  **Data Quality:** Under 5% duplication rate using semantic and metadata deduplication; >95% completeness of core fields (Title, Company, Description, Apply URL).
4.  **Privacy & Portability:** Self-hostable, lightweight footprint, with easy exports to CSV, JSON, or external webhooks.

---

## Functional Requirements

### 1. Search Query Management
*   Allow users to define and store search configurations.
*   **Input parameters:**
    *   `Keywords/Job Titles` (e.g., "Data Product Manager", "Lead PM")
    *   `Location/Region` (e.g., Brazil, LATAM, USA, Canada)
    *   `Work Type` (Remote, Hybrid, On-site)

### 2. Scraping & Extensibility
*   Modular scraper engines (spiders) that map query parameters to target job board search forms/APIs.
*   Polite crawling: support rate-limiting, custom headers, robots.txt compliance, and backoff timing.
*   Headless browser support (Playwright) reserved only for highly interactive, JS-heavy target sites.

### 3. Data Extraction & Normalization
*   Extract core fields: `Title`, `Company`, `Location`, `Work Type` (remote/hybrid/onsite), `Salary Range` (if visible), `Date Posted`, `Description`, and `Source URL`.
*   Normalize disparate location strings into a structured format (Country, State/City, Remote Status).

### 4. Deduplication
*   Canonicalize listings using a hash of `Normalized Title + Normalized Company + Remote Status`.
*   Ensure that identical roles posted on different boards are grouped rather than duplicated.

### 5. Storage & API
*   Expose a REST API for managing search configurations and retrieving jobs:
    *   `POST /search-queries` - Register a search query.
    *   `GET /search-queries` - List active search configurations.
    *   `GET /jobs` - Paginated, searchable, and filterable list of captured jobs.
    *   `GET /stats` - Crawl metrics (success rate, job counts by source).

---

## Technical Architecture (Recommended Stack)
*   **Backend Framework:** FastAPI (Python) for clean, high-performance, asynchronous REST API.
*   **Task Queue:** Redis Queue (RQ) for lightweight, python-native task scheduling and concurrency.
*   **Database:** PostgreSQL with JSONB columns for structured schema combined with metadata flexibility.
*   **Scraping Tools:** Scrapy (HTTP/API-first) + Playwright (used selectively for JS-rendered targets).
*   **Deployment:** Docker Compose for local/self-hosted deployment.

---

## Architectural Decisions & Trade-offs Log

### Decision 1: Target Sector & Domain Scoping
*   **Trade-off:** Broad, unfocused job aggregation (scraping all industries/job classes) vs. specialized tech/management role tracking with user-defined parameters.
*   **Solution chosen:** Customizable query-driven job crawler, optimized initially for remote tech and product management roles (e.g., PM, Data PM, Lead PM) but allowing user-defined search parameters.
*   **Reason for the choice:** A completely unfocused crawler generates massive noise and low data quality. Standardizing scrapers and database schema for high-value remote tech and product roles ensures high structured data quality for the MVP, while keeping the query engine parameterized ensures the user can track any role they desire.
*   **Timestamp:** 2026-06-29T16:40:00-03:00

### Decision 2: Ingestion Strategy
*   **Trade-off:** Bulk database scraping (scraping all jobs from a target board) vs. query-driven scraping (querying specific search inputs dynamically).
*   **Solution chosen:** Query-driven scraping based on user-defined search parameters.
*   **Reason for the choice:** Bulk scraping of modern job boards is extremely resource-intensive, gets blocked quickly by CDN/Cloudflare rules, and accumulates massive amounts of irrelevant data. Query-driven scraping is target-specific, lightweight, and bypasses the need for massive data warehousing.
*   **Timestamp:** 2026-06-29T16:40:00-03:00

### Decision 3: Storage Schema Model
*   **Trade-off:** Rigid SQL Relational Database vs. NoSQL Document Database (MongoDB) vs. PostgreSQL Hybrid (JSONB).
*   **Solution chosen:** PostgreSQL with JSONB.
*   **Reason for the choice:** Job details vary wildly between boards (some include salary, tags, specific department fields; others have bare markdown descriptions). JSONB columns in PostgreSQL provide the flexibility of a document store while retaining SQL capabilities, transactions, and robust relational queries for user configs and statistics.
*   **Timestamp:** 2026-06-29T16:40:00-03:00

### Decision 4: Concurrency & Queue Engine
*   **Trade-off:** Celery (highly scalable, enterprise-standard, complex configuration) vs. Redis Queue (RQ) (lightweight, python-native, easy to manage).
*   **Solution chosen:** Redis Queue (RQ).
*   **Reason for the choice:** Celery introduces a lot of infrastructure overhead (requires RabbitMQ/Redis, complex serialization, and configuration boilerplate). For a self-hosted or small-scale open-source crawler, RQ is much simpler to implement, configure, and maintain, while providing all necessary queue features.
*   **Timestamp:** 2026-06-29T16:40:00-03:00