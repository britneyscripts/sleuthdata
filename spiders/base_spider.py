class BaseSpider:
    def __init__(self):
        self.name = "base"

    def search(self, keywords: str, region: str) -> list[dict]:
        """
        Sends query parameters to target site search forms/APIs.
        
        Returns a list of standardized dictionaries:
        [
            {
                "title": str,
                "company": str,
                "location_raw": str,
                "description": str,
                "salary_raw": str or None,
                "source_url": str,
                "date_posted": datetime.date or None
            }
        ]
        """
        raise NotImplementedError
