"""Database setup and session management."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./font_lab.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Yield a database session, closing it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    from app.models import (  # noqa: F401 – ensure models are registered
        ApiKey,
        FontAlias,
        FontFile,
        FontSample,
        FontSampleTaxonomy,
        FontSearchIndex,
        FontVariant,
        Glyph,
        GlyphCoverageSummary,
        PreviewAsset,
        ProvenanceRecord,
        SourceArtifact,
        TaxonomyDimension,
        TaxonomyTerm,
    )

    Base.metadata.create_all(bind=engine)
