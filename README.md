<p align="center">
  <img src="assets/logo.png" alt="Sleuth Data Logo" width="220px"/>
  <br>
  <font size="6"><b>Sleuth Data</b></font>
</p>

<p align="center">
  <strong>A Query-Driven, Config-Based Job Aggregator & Market Intelligence Engine</strong>
</p>

<p align="center">
  <a href="https://github.com/britneyscripts/sleuthdata/actions"><img src="https://img.shields.io/badge/build-passing-brightgreen.svg" alt="Build Status"/></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg" alt="Python Support"/></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.110.0-009688.svg" alt="FastAPI"/></a>
  <a href="https://ai.google.dev"><img src="https://img.shields.io/badge/Powered%20By-Gemini%20AI-blueviolet" alt="Gemini AI"/></a>
  <a href="https://github.com/britneyscripts/sleuthdata/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"/></a>
</p>

---

"All the dashes used in this article were the author's own." - Shakespeare

**Sleuth Data** is an open-source, configuration-driven remote job aggregator designed to dynamically gather job opportunities based on personalized query settings, rather than scraping target websites in bulk. 

Optimized for tech and product roles (PMs, Data PMs, Engineers), it enriches candidate workflows by fetching direct career links and consolidating organizational health parameters - such as Glassdoor sentiment ratings, market salary brackets, and layoff alerts - using **Gemini AI Structured Outputs**.

---

## 🚀 Key Features

### 📦 Release v1.0.0 (Core MVP)
*   **Search Query Management:** Custom parameters configuration (`Keywords/Job Titles`, `Location/Region`, `Work Type`) exposed via REST API.
*   **Modular Spider Core:** decupled base engine (`BaseSpider`) executing lightweight, high-performance crawls from `WeWorkRemotely` (RSS) and `Gupy` (Public Search API).
*   **Deduplication:** Hash-based verification engine using SHA-256 hashes (`normalized_title + company + remote_status`) to prevent data clutter.
*   **Asynchronous Processing:** Asynchronous background worker tasks managed via `Redis Queue` (RQ) and `FastAPI BackgroundTasks`.

### ⚡ Release v1.2.0 (Target Companies & Market Insights)
*   **Target Companies Ingestion:** Config-driven scraping of specific company portals defined in `target_companies.json`.
*   **Fallback & Merge Ingestion Pipeline:** Seamless ingestion merging. If a job is found on WeWorkRemotely and Vercel's careers page, the direct careers URL is prioritized without losing description richness.
*   **Gemini AI-Powered Company Insights:**
    *   Asynchronous search queries (DuckDuckGo Search) querying ratings, salaries, and layoff records.
    *   Structured metadata parsing using **Gemini 2.5 Flash** to extract exact ratings, compensation indicators, and layoff notes with zero Regex complexity.
*   **Auto-Migrations:** Automatic SQLite database schema updating on launch to ease local development setup.

---

## 🛠️ Architecture & Technologies

*   **API Framework:** [FastAPI](https://fastapi.tiangolo.com) (Python)
*   **Background Worker:** [Redis Queue (RQ)](https://python-rq.org)
*   **Database:** PostgreSQL (with `JSONB` flexibility) / SQLite (for zero-dependency local testing)
*   **AI Engine:** [Google GenAI SDK](https://github.com/google/generative-ai-python) (Gemini 2.5 Flash)
*   **Search / Scraping:** Scrapy + Playwright (Headless browser support) + `ddgs` (DuckDuckGo search scraper interface)

---

## 💻 Local Setup & Installation

### 1. Clone the repository and navigate into the folder:
```bash
git clone https://github.com/britneyscripts/sleuthdata.git
cd sleuthdata
```

### 2. Configure Virtual Environment:
```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
# or .\.venv\Scripts\activate on Windows
```

### 3. Install dependencies:
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables:
Copy `.env.example` to `.env` and configure your API keys:
```bash
cp .env.example .env
```
Ensure you set your `GEMINI_API_KEY` for company insights extraction.

### 5. Running the Application:
Start the FastAPI server locally:
```bash
uvicorn api.main:app --reload
```
Access the interactive API docs (Swagger UI) at `http://localhost:8000/docs`.

---

## 🧪 Verification & Testing

To test company insights enrichment and crawling using the SQLite database:

**Run the enrichment test:**
```bash
python .gemini/antigravity-ide/brain/04c7146f-ca4b-4865-bbe2-d29ebfaba98f/scratch/test_v12.py
```

**Run the end-to-end crawl pipeline test:**
```bash
python .gemini/antigravity-ide/brain/04c7146f-ca4b-4865-bbe2-d29ebfaba98f/scratch/test_crawl.py
```

---

## 📋 Project Management & Roadmap

The planning, prioritization, and product strategy documents are maintained in the repository:
*   [Product Requirements Document (PRD)](PRD.md)
*   [MoSCoW Prioritization Roadmap](MoSCoW.md)
*   [Architecture Decisions Log](ARCHITECTURE.md)
*   [Technical Implementation Plan](IMPLEMENTATION_PLAN.md)

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
