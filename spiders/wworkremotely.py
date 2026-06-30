import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import email.utils
from spiders.base_spider import BaseSpider

class WeWorkRemotelySpider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.name = "weworkremotely"
        # Using WeWorkRemotely's public RSS feed as the official data endpoint
        self.rss_url = "https://weworkremotely.com/remote-jobs.rss"

    def search(self, keywords: str, region: str) -> list[dict]:
        """
        Fetches job postings from WeWorkRemotely's RSS feed and filters 
        by keywords and region/location parameters.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(self.rss_url, headers=headers, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching RSS from WeWorkRemotely: {e}")
            return []

        try:
            root = ET.fromstring(response.content)
        except Exception as e:
            print(f"Error parsing XML from WeWorkRemotely: {e}")
            return []

        items = root.findall(".//item")
        filtered_jobs = []

        # Keywords cleaning
        keyword_terms = [k.strip().lower() for k in keywords.split() if len(k.strip()) > 1]
        region_clean = region.lower().strip()

        for item in items:
            raw_title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            description = item.find("description").text if item.find("description") is not None else ""
            pub_date_str = item.find("pubDate").text if item.find("pubDate") is not None else ""
            category = item.find("category").text if item.find("category") is not None else ""

            # RSS titles typically follow the pattern "Company: Job Title"
            company = "Unknown"
            title = raw_title
            if ":" in raw_title:
                parts = raw_title.split(":", 1)
                company = parts[0].strip()
                title = parts[1].strip()

            title_lower = title.lower()
            desc_lower = description.lower()
            company_lower = company.lower()

            # 1. Keywords filtering
            keyword_match = False
            if keywords.lower() in title_lower or keywords.lower() in desc_lower:
                keyword_match = True
            elif any(term in title_lower or term in category.lower() for term in keyword_terms):
                keyword_match = True

            if not keyword_match:
                continue

            # 2. Location/Region filtering
            region_match = False
            if not region_clean:
                region_match = True
            elif region_clean in desc_lower or region_clean in title_lower:
                region_match = True
            elif "anywhere" in desc_lower or "worldwide" in desc_lower:
                region_match = True
            elif region_clean == "brazil" and ("americas" in desc_lower or "latam" in desc_lower):
                region_match = True
            elif region_clean == "latam" and ("americas" in desc_lower or "south america" in desc_lower):
                region_match = True

            if not region_match:
                continue

            # 3. Parse date string using python's built-in email.utils for RFC 2822
            pub_date = None
            if pub_date_str:
                try:
                    parsed_dt = email.utils.parsedate_to_datetime(pub_date_str)
                    pub_date = parsed_dt.date()
                except Exception:
                    pub_date = datetime.utcnow().date()

            filtered_jobs.append({
                "title": title,
                "company": company,
                "location_raw": "Remote",
                "description": description,
                "salary_raw": None,
                "source_url": link,
                "date_posted": pub_date
            })

        return filtered_jobs
