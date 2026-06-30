import json
import os
import re
import html
import requests
from datetime import datetime
from spiders.base_spider import BaseSpider

# Helper to strip HTML tags from description texts
def strip_html_tags(text_html: str) -> str:
    if not text_html:
        return ""
    clean = re.sub(r'<[^>]*>', ' ', text_html)
    clean = html.unescape(clean)
    return re.sub(r'\s+', ' ', clean).strip()

class TargetCompanySpider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.name = "target_companies"
        self.config_path = "target_companies.json"

        # Known mapping of normalized company name to ATS details: (ats_type, board_token)
        self.ats_map = {
            "latecheckout": ("lever", "latecheckout"),
            "metalab": ("greenhouse", "metalab"),
            "thoughtbot": ("greenhouse", "thoughtbot"),
            "workco": ("greenhouse", "workandco"),
            "linear": ("greenhouse", "linear"),
            "supabase": ("greenhouse", "supabase"),
            "vercel": ("greenhouse", "vercel"),
            "doist": ("greenhouse", "doist"),
            "huggingface": ("greenhouse", "huggingface"),
            "reforge": ("lever", "reforge"),
            "akqa": ("greenhouse", "akqa"),
            "huge": ("greenhouse", "huge"),
            "mediamonks": ("greenhouse", "mediamonks"),
            "thoughtworks": ("greenhouse", "thoughtworks"),  # Fallback token
            "rga": ("greenhouse", "rga")
        }

    def _normalize_key(self, name: str) -> str:
        s = name.lower().strip()
        s = re.sub(r'\b(inc|llc|corp|corporation|ltda|ltd|s\.a\.|sa|me|eireli)\b', '', s)
        s = re.sub(r'[^a-z0-9]', '', s)
        return s

    def _load_target_companies(self) -> list[dict]:
        if not os.path.exists(self.config_path):
            print(f"Warning: {self.config_path} not found.")
            return []
        try:
            with open(self.config_path, "r") as f:
                config_data = json.load(f)
                return config_data.get("target_companies", [])
        except Exception as e:
            print(f"Error loading target companies config: {e}")
            return []

    def search(self, keywords: str, region: str) -> list[dict]:
        """
        Loops through the configured target companies, queries their public ATS APIs
        (Greenhouse/Lever), filters findings by keywords/region, and aggregates results.
        """
        targets = self._load_target_companies()
        jobs_collected = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        keyword_terms = [k.strip().lower() for k in keywords.split() if len(k.strip()) > 1]
        region_clean = region.lower().strip()

        for target in targets:
            name = target.get("name", "")
            norm_name = self._normalize_key(name)
            
            if norm_name not in self.ats_map:
                print(f"Target company '{name}' has no defined ATS mappings. Skipping.")
                continue

            ats_type, token = self.ats_map[norm_name]
            print(f"Fetching listings for target company: {name} (ATS: {ats_type}, Token: {token})")

            raw_jobs = []
            try:
                if ats_type == "greenhouse":
                    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
                    response = requests.get(url, headers=headers, timeout=12)
                    if response.status_code == 200:
                        raw_jobs = response.json().get("jobs", [])
                    else:
                        print(f"Greenhouse board {token} returned status code {response.status_code}")
                elif ats_type == "lever":
                    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
                    response = requests.get(url, headers=headers, timeout=12)
                    if response.status_code == 200:
                        raw_jobs = response.json()
                    else:
                        print(f"Lever board {token} returned status code {response.status_code}")
            except Exception as api_err:
                print(f"Error querying {ats_type} API for {name}: {api_err}")
                continue

            # Parse and filter job listings
            for raw_job in raw_jobs:
                title = ""
                description_raw = ""
                location_raw = "Remote"
                source_url = ""
                date_posted = None

                if ats_type == "greenhouse":
                    title = raw_job.get("title", "")
                    description_raw = raw_job.get("content", "")
                    location_raw = raw_job.get("location", {}).get("name", "Remote")
                    source_url = raw_job.get("absolute_url", "")
                    # Greenhouse date format example: "2026-06-25T12:00:00Z"
                    updated_at_str = raw_job.get("updated_at")
                    if updated_at_str:
                        try:
                            date_posted = datetime.fromisoformat(updated_at_str.split("T")[0]).date()
                        except ValueError:
                            date_posted = datetime.utcnow().date()
                elif ats_type == "lever":
                    title = raw_job.get("text", "")
                    description_raw = raw_job.get("description", "") + " " + raw_job.get("lists", [{}])[0].get("content", "")
                    location_raw = raw_job.get("categories", {}).get("location", "Remote")
                    source_url = raw_job.get("hostedUrl", "")
                    # Lever lists milliseconds timestamp
                    created_at_ts = raw_job.get("createdAt")
                    if created_at_ts:
                        try:
                            date_posted = datetime.utcfromtimestamp(created_at_ts / 1000.0).date()
                        except Exception:
                            date_posted = datetime.utcnow().date()

                description = strip_html_tags(description_raw)
                title_lower = title.lower()
                desc_lower = description.lower()
                location_lower = location_raw.lower()

                # 1. Keywords filtering
                keyword_match = False
                if keywords.lower() in title_lower or keywords.lower() in desc_lower:
                    keyword_match = True
                elif any(term in title_lower for term in keyword_terms):
                    keyword_match = True

                if not keyword_match:
                    continue

                # 2. Location/Region filtering
                region_match = False
                if not region_clean:
                    region_match = True
                elif region_clean in location_lower:
                    region_match = True
                elif "remote" in location_lower or "remoto" in location_lower or "anywhere" in location_lower or "worldwide" in location_lower:
                    region_match = True
                elif region_clean == "brazil" and ("americas" in location_lower or "latam" in location_lower):
                    region_match = True

                if not region_match:
                    continue

                jobs_collected.append({
                    "title": title,
                    "company": name,
                    "location_raw": location_raw,
                    "description": description,
                    "salary_raw": None,
                    "source_url": source_url,
                    "date_posted": date_posted
                })

        return jobs_collected
