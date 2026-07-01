from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from core.config import settings
import secrets


_DEV_FALLBACK_KEY = "dev-local-key"

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def require_api_key(provided_key: str | None = Security(api_key_header)) -> None:
    """
    FastAPI dependency that guards write endpoints from unauthenticated use.
    Falls back to a fixed dev key only when ENV=development and API_KEY is unset,
    so local testing keeps working without extra setup.
    """
    expected_key = settings.API_KEY
    if not expected_key:
        if settings.ENV == "development":
            expected_key = _DEV_FALLBACK_KEY
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API_KEY is not configured on the server."
            )

    if not provided_key or not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key."
        )
