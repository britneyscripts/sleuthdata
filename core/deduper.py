import hashlib
import re

def clean_string(s: str) -> str:
    """
    Cleans strings by lowercasing, stripping whitespace, removing common
    suffixes (Inc, LLC, Corp, Ltda) and keeping only alphanumeric chars.
    """
    if not s:
        return ""
    s = s.lower().strip()
    # Strip common company structure suffixes
    s = re.sub(r'\b(inc|llc|corp|corporation|ltda|ltd|s\.a\.|sa|me|eireli)\b', '', s)
    # Keep only lowercase alphanumeric chars
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def calculate_canonical_hash(title: str, company: str, is_remote: bool) -> str:
    """
    Computes a SHA-256 hash from standardized job title, company name, and remote status.
    This hash serves as a unique key to prevent job duplicates.
    """
    clean_title = clean_string(title)
    clean_company = clean_string(company)
    remote_status = "remote" if is_remote else "local"
    raw_key = f"{clean_title}:{clean_company}:{remote_status}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
