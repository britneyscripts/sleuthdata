# Document Control
*   **Document Title:** MoSCoW Prioritization - Query-Driven Job Crawler
*   **Version:** 1.2.0
*   **Status:** Approved
*   **Date:** 2026-06-30
*   **Author:** Bettina Acosta de Paula
*   **Description:** Scope prioritization and release roadmap for the Query-Driven Job Crawler.

## Revision History
| Version | Date | Author | Description of Change |
|---------|------|--------|-----------------------|
| 1.0.0   | 2026-06-29 | Bettina Acosta de Paula | Initial publication of the MoSCoW scope definition. |
| 1.2.0   | 2026-06-30 | Bettina Acosta de Paula | Restructured into versioned releases; added v1.2.0 scope for Target Companies & Insights. |

---

# MoSCoW Prioritization by Release

This document outlines the phased roadmap and feature prioritization using the MoSCoW framework.

---

## Release v1.0.0: Core MVP (Must-Have)
The absolute critical path for a working local prototype.

*   **Search Query Registry:**
    *   API endpoints to CRUD search parameters: `Keywords/Job Titles`, `Location/Region`, and `Work Type`.
*   **Basic Scraper Engines:**
    *   Unified base spider class (`BaseSpider`).
    *   Scrapers for WeWorkRemotely RSS and Gupy Public Portal API.
*   **Data Ingestion & Storage:**
    *   PostgreSQL database with JSONB columns for flexible job metadata.
*   **Deterministic Deduplication:**
    *   Hash-based duplicate checking using `sha256(canonical_title + company + remote_status)`.
*   **Worker & Queue System:**
    *   Redis Queue (RQ) integration to execute scraping jobs asynchronously.
*   **Basic REST API:**
    *   `GET /jobs` with pagination and basic text search filters.

---

## Release v1.2.0: Target Companies & Market Insights (Should-Have)
Focuses on targeted company pipelines and enriching company metadata with market health indicators.

*   **Target Companies Ingestion:**
    *   Scrape direct careers pages/APIs of companies listed in [target_companies.json](./target_companies.json).
*   **Company Entity Separation:**
    *   Move company-specific fields (ratings, layoffs, salary metrics) into a dedicated `companies` table, separating them from the `job_listings` table.
*   **Fallback & Merge Ingestion Pipeline:**
    *   Ingest jobs from both aggregators and direct career pages. If a duplicate is found:
        *   Mark direct careers page URL as primary.
        *   Enrich with aggregator description if direct page lacks text.
        *   Retain aggregator data if direct spider fails (no data loss).
*   **Glassdoor Rating Scraper:**
    *   DuckDuckGo Search snippet parsing (via the Python `ddgs` library) to fetch Glassdoor star ratings for free without Cloudflare blockages.
*   **Layoffs & Compensation Indicators:**
    *   Integrate layoff history indicators (from Layoffs.fyi search results) and average salary brackets (from Levels.fyi metrics).
*   **Location Normalization Engine:**
    *   Parsing and categorization of raw location strings into structured `Country`, `City`, and `Remote/Hybrid/Onsite` fields.

---

## Release v1.5.0: AI Parsing & Alerts (Could-Have)
Enhancements for personal productivity and integrations.

*   **LLM-based Schema Parsing & Enrichment:**
    *   Passing crawled job descriptions to an LLM (such as Gemini) to extract required skills, experience levels, and company "red flags".
*   **Integration with Career Tools:**
    *   Exposing clean JSON payloads matching the input schemas of ATS matching and resume-tailoring tools.
*   **Webhooks & Alerts:**
    *   Webhook dispatcher to send real-time alerts (Slack, Discord, Email) when a new job matches a registered search query.

---

## Release v2.0.0+: Enterprise Scale (Won't-Have for now)
Deferred for long-term scalability.

*   **Geospatial Search (PostGIS):**
    *   Proximity-based queries for hybrid or localized remote job listings.
*   **Built-in Proxy Pool / CAPTCHA Solver:**
    *   Support integration with external proxy providers via simple middleware configuration.
*   **Unfocused Global Web Indexing:**
    *   No attempt to crawl whole job boards without query parameters.