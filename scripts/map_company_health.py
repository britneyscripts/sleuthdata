import json
import re
import time
from duckduckgo_search import DDGS
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "target_companies.json"
OUTPUT_FILE = BASE_DIR / "company_health.json"

def fetch_glassdoor_rating(company_name: str) -> str:
    """Uses DDGS to find the glassdoor rating from the search snippet."""
    query = f'site:glassdoor.com "{company_name}" reviews'
    print(f"[*] Searching rating for: {company_name}")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
            if not results:
                return "Not found"
                
            # Regex to match common Glassdoor star patterns in search snippets
            regex = r'(\d\.\d)\s*(?:★|out of 5|stars|Rating)'
            
            for result in results:
                snippet = result.get("body", "") + " " + result.get("title", "")
                
                match = re.search(regex, snippet)
                if match:
                    return match.group(1)
                
                fallback_match = re.search(r'(\d\.\d).*?Glassdoor', snippet, re.IGNORECASE)
                if fallback_match:
                    return fallback_match.group(1)
                    
            return "Rating missing in snippet"
            
    except Exception as e:
        print(f"Error fetching for {company_name}: {e}")
        return "Error"

def main():
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return
        
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)
        
    companies = data.get("target_companies", [])
    enriched_companies = []
    
    print(f"Starting varredura for {len(companies)} companies...\n")
    
    for idx, company in enumerate(companies):
        name = company.get("name")
        url = company.get("url")
        
        rating = fetch_glassdoor_rating(name)
        
        company_data = {
            "name": name,
            "careers_url": url,
            "glassdoor_rating": rating
        }
        
        enriched_companies.append(company_data)
        print(f" -> {name}: {rating} stars\n")
        
        if idx < len(companies) - 1:
            time.sleep(2)
            
    output_data = {"enriched_companies": enriched_companies}
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"Varredura complete! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
