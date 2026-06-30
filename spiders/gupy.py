import requests
from datetime import datetime
from spiders.base_spider import BaseSpider

class GupySpider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.name = "gupy"
        # Public search API endpoint used by the portal.gupy.io candidate frontend
        self.api_url = "https://portal.gupy.io/api/v1/jobs"

    def search(self, keywords: str, region: str) -> list[dict]:
        """
        Queries Gupy's public portal API for jobs matching keywords and region.
        """
        params = {
            "name": keywords,
            "limit": 100,
            "offset": 0
        }

        # Apply remote filter if the region check involves remote work or if the user filters it
        # workplaceType = "remote" filters for 100% remote roles in Gupy
        params["workplaceType"] = "remote"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        try:
            response = requests.get(self.api_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching data from Gupy Portal API: {e}")
            return []

        # Gupy returns the job listings in data["data"]
        raw_listings = data.get("data", [])
        filtered_jobs = []

        # Region cleaning
        region_clean = region.lower().strip()

        for job in raw_listings:
            title = job.get("name", "")
            company = job.get("companyName", "Unknown")
            workplace_type = job.get("workplaceType", "")
            career_page_url = job.get("careerPageUrl", "")
            
            # Gupy locations are objects or strings
            city = job.get("city", "")
            state = job.get("state", "")
            location_raw = f"{city}, {state}" if city and state else (city or state or workplace_type)

            # Filter by region in memory (e.g. if we are looking for Brazil/LATAM and the company is Brazilian)
            # Usually Gupy is 95% Brazilian/LATAM companies, but we filter if region is specified.
            region_match = False
            if not region_clean:
                region_match = True
            elif "brazil" in region_clean or "brasil" in region_clean:
                # Gupy is primarily Brazil, so we assume yes, unless state/country specifies otherwise
                region_match = True
            elif "latam" in region_clean:
                region_match = True
            elif "usa" in region_clean or "canada" in region_clean:
                # Gupy has very few US/Canada listings, so we check if location text matches
                if "usa" in location_raw.lower() or "united states" in location_raw.lower() or "canada" in location_raw.lower():
                    region_match = True
            else:
                region_match = True

            if not region_match:
                continue

            # Parse Publication Date
            # Expected format: "2026-06-25T12:00:00.000Z"
            pub_date = None
            pub_date_str = job.get("publishedAt")
            if pub_date_str:
                try:
                    clean_date_str = pub_date_str.replace("Z", "+00:00")
                    pub_date = datetime.fromisoformat(clean_date_str).date()
                except ValueError:
                    pub_date = datetime.utcnow().date()

            # For the description, Gupy Portal API returns a summary or html. 
            # We fetch 'description' or fall back to 'name' details
            description = job.get("description", "") or f"Job position: {title} at {company}."

            standardized_job = {
                "title": title,
                "company": company,
                "location_raw": location_raw,
                "description": description,
                "salary_raw": None, # Gupy rarely exposes salary in the search api list
                "source_url": career_page_url,
                "date_posted": pub_date
            }
            filtered_jobs.append(standardized_job)

        return filtered_jobs
