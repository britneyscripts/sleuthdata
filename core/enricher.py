from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from ddgs import DDGS
from datetime import datetime
from core.models import Company
import os

class CompanyInsightsSchema(BaseModel):
    glassdoor_rating: float | None = Field(None, description="The overall rating of the company on Glassdoor (from 0.0 to 5.0).")
    average_salary_usd: float | None = Field(None, description="Average estimated annual salary in USD for engineering/product roles.")
    has_layoffs: bool = Field(False, description="True if there are reports of layoffs in the search results.")
    layoff_details: str | None = Field(None, description="Summary of layoffs found, including date and percentage/number of employees laid off.")

def enrich_company_insights(company: Company, db_session) -> bool:
    """
    Searches DuckDuckGo for Glassdoor, Levels.fyi, and Layoffs info for the given company,
    uses Gemini 2.5 Flash to extract structured insights, and updates the database record.
    """
    company_name = company.name
    print(f"Enriching company insights for: {company_name}")
    
    # 1. Fetch search snippets
    snippets = []
    
    # We query Glassdoor, Levels.fyi, and generic Layoffs search
    queries = [
        f"{company_name} site:glassdoor.com/Reviews",
        f"{company_name} site:levels.fyi",
        f"{company_name} layoffs"
    ]
    
    try:
        with DDGS() as ddgs:
            for query in queries:
                try:
                    # Fetch search results
                    results = list(ddgs.text(query, max_results=3))
                    for r in results:
                        body = r.get("body", "")
                        title = r.get("title", "")
                        snippets.append(f"Title: {title}\nSnippet: {body}\n")
                except Exception as query_err:
                    print(f"Error querying DuckDuckGo for '{query}': {query_err}")
    except Exception as ddg_err:
        print(f"Error initializing DuckDuckGo Search: {ddg_err}")

    raw_search_text = "\n".join(snippets)
    if not raw_search_text.strip():
        print(f"No search results found for {company_name}. Skipping LLM parsing.")
        company.last_enriched_at = datetime.utcnow()
        db_session.commit()
        return False

    # 2. Call Gemini API for structured extraction
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        from core.config import settings
        api_key = settings.GEMINI_API_KEY
        
    if not api_key:
        print("WARNING: GEMINI_API_KEY is not set. Cannot run LLM insights extraction.")
        return False
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = (
            f"You are a talent intelligence agent. Analyze the search engine results below about the company '{company_name}'.\n"
            f"Extract the company's Glassdoor rating, average annual salary for tech/PM roles (in USD), and layoff history.\n\n"
            f"Search Results:\n{raw_search_text}\n"
        )
        
        # Call Gemini model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CompanyInsightsSchema,
                temperature=0.0
            )
        )
        
        insights = CompanyInsightsSchema.model_validate_json(response.text)
        print(f"Successfully extracted insights for {company_name}: {insights}")
        
        # 3. Update company record
        company.glassdoor_rating = insights.glassdoor_rating
        company.average_salary_usd = insights.average_salary_usd
        company.has_layoffs = insights.has_layoffs
        company.layoff_details = insights.layoff_details
        company.last_enriched_at = datetime.utcnow()
        db_session.commit()
        return True
        
    except Exception as gemini_err:
        print(f"Error calling Gemini API for company enrichment: {gemini_err}")
        return False
