import re

def parse_remote_status(location_raw: str) -> bool:
    """
    Infers if a raw location string indicates a remote position.
    """
    if not location_raw:
        return True # Default to remote for our scoping
    
    loc_lower = location_raw.lower()
    remote_keywords = ["remote", "remoto", "anywhere", "worldwide", "teletrabalho", "home office", "homeoffice", "remota"]
    
    return any(kw in loc_lower for kw in remote_keywords)

def normalize_location(location_raw: str) -> tuple[str | None, str | None]:
    """
    Attempts to normalize raw location text into (city, country).
    """
    if not location_raw:
        return None, None
        
    loc_clean = location_raw.strip()
    
    # Check for obvious remote placeholders
    if loc_clean.lower() in ["remote", "remoto", "anywhere", "worldwide"]:
        return None, None

    # Handle comma-separated values (e.g., "São Paulo, SP" or "New York, USA")
    parts = [p.strip() for p in loc_clean.split(",")]
    if len(parts) >= 2:
        city = parts[0]
        state_or_country = parts[1]
        
        # If the state/country matches common US/Brazil patterns
        if len(state_or_country) == 2: # State abbreviation e.g., SP, RJ, IL, CA
            return city, "Brazil" if state_or_country.upper() in ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "PE", "CE"] else "USA"
        return city, state_or_country

    return loc_clean, None
