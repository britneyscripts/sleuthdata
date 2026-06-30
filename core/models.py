import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Date, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import Base

class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keywords = Column(String, nullable=False)           # e.g., "Data Product Manager"
    region = Column(String, nullable=False)             # e.g., "Brazil", "LATAM", "USA/Canada"
    is_remote_only = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to listings
    listings = relationship("JobListing", back_populates="search_query", cascade="all, delete-orphan")

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)
    normalized_name = Column(String, unique=True, index=True, nullable=False)
    glassdoor_rating = Column(Float, nullable=True)
    average_salary_usd = Column(Float, nullable=True)
    has_layoffs = Column(Boolean, default=False, nullable=False)
    layoff_details = Column(Text, nullable=True)
    last_enriched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to listings
    listings = relationship("JobListing", back_populates="company_profile", cascade="all, delete-orphan")

class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_query_id = Column(UUID(as_uuid=True), ForeignKey("search_queries.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)
    
    title = Column(String, nullable=False)              # e.g., "Senior Product Manager"
    company = Column(String, nullable=False)            # e.g., "TechCorp" (raw name)
    location_raw = Column(String, nullable=False)       # Raw parsed location string
    country = Column(String, nullable=True)             # Normalized country
    city = Column(String, nullable=True)                # Normalized city
    is_remote = Column(Boolean, default=True)           # Remote indicator
    description = Column(Text, nullable=False)          # Full job description
    salary_raw = Column(String, nullable=True)          # Salary string if visible
    source = Column(String, nullable=False)             # e.g. "WeWorkRemotely"
    source_url = Column(String, nullable=False)         # Application link
    
    # SHA-256 hash: sha256(lowercase(title) + lowercase(company) + remote_status)
    canonical_hash = Column(String, unique=True, index=True, nullable=False)
    
    # Skills extracted (e.g. ["SQL", "Analytics", "Agile"])
    skills_extracted = Column(JSON, default=list, nullable=False)
    
    date_posted = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    search_query = relationship("SearchQuery", back_populates="listings")
    company_profile = relationship("Company", back_populates="listings")

    @property
    def company_rating(self) -> float | None:
        return self.company_profile.glassdoor_rating if self.company_profile else None

    @property
    def company_salary_avg(self) -> float | None:
        return self.company_profile.average_salary_usd if self.company_profile else None

    @property
    def company_has_layoffs(self) -> bool:
        return self.company_profile.has_layoffs if self.company_profile else False

    @property
    def company_layoff_details(self) -> str | None:
        return self.company_profile.layoff_details if self.company_profile else None

