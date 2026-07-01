from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# Create database engine
db_url = settings.database_url_resolved
if db_url.startswith("sqlite"):
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,  # Validates connections before using them
        pool_size=5,
        max_overflow=10
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base model for SQLAlchemy schemas
Base = declarative_base()

def get_db():
    """Dependency to inject database session into FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
