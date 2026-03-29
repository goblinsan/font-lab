"""Taxonomy seed script – bootstraps TaxonomyDimension and TaxonomyTerm rows.

Usage
-----
Run directly against any DATABASE_URL environment variable::

    DATABASE_URL=sqlite:///./font_lab.db python scripts/seed_taxonomy.py

Idempotent: safe to re-run; existing records are updated rather than
duplicated.
"""

from __future__ import annotations

import os
import sys

# Ensure the repo root is on the path so ``app`` can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (  # noqa: F401 – register all models
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
from app.repository import TaxonomyRepository
from app.taxonomy import (
    CATEGORIES,
    CONSTRUCTION_TRAITS,
    ERAS,
    FIELD_CONFIG,
    GENRES,
    HIERARCHY,
    MOODS,
    ORIGIN_CONTEXTS,
    RESTORATION_STATUSES,
    RIGHTS_STATUSES,
    SOURCE_TYPES,
    STYLES,
    SYNONYMS,
    THEMES,
    USE_CASES,
    VISUAL_TRAITS,
)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./font_lab.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)


# Map from dimension name → (values list, synonyms dict subset, hierarchy dict subset)
DIMENSION_DATA: dict[str, dict] = {
    "style": {
        "values": STYLES,
        "cardinality": "single",
        "synonyms": {k: v for k, v in SYNONYMS.items() if k in STYLES},
        "hierarchy": HIERARCHY,  # style → genre children
    },
    "genre": {
        "values": GENRES,
        "cardinality": "single",
        "synonyms": {k: v for k, v in SYNONYMS.items() if k in GENRES},
    },
    "themes": {
        "values": THEMES,
        "cardinality": "multi",
    },
    "moods": {
        "values": MOODS,
        "cardinality": "multi",
    },
    "font_category": {
        "values": CATEGORIES,
        "cardinality": "single",
    },
    "use_cases": {
        "values": USE_CASES,
        "cardinality": "multi",
    },
    "era": {
        "values": ERAS,
        "cardinality": "single",
        "synonyms": {k: v for k, v in SYNONYMS.items() if k in ERAS},
    },
    "origin_context": {
        "values": ORIGIN_CONTEXTS,
        "cardinality": "single",
    },
    "construction_traits": {
        "values": CONSTRUCTION_TRAITS,
        "cardinality": "multi",
    },
    "visual_traits": {
        "values": VISUAL_TRAITS,
        "cardinality": "multi",
    },
    "restoration_status": {
        "values": RESTORATION_STATUSES,
        "cardinality": "single",
    },
    "source_type": {
        "values": SOURCE_TYPES,
        "cardinality": "single",
    },
    "rights_status": {
        "values": RIGHTS_STATUSES,
        "cardinality": "single",
        "synonyms": {k: v for k, v in SYNONYMS.items() if k in RIGHTS_STATUSES},
    },
}


def seed(db_session) -> None:
    """Insert or update all taxonomy dimensions and terms."""
    repo = TaxonomyRepository(db_session)

    for dim_name, data in DIMENSION_DATA.items():
        fc = FIELD_CONFIG.get(dim_name, {})
        dim = repo.upsert_dimension(
            name=dim_name,
            label=fc.get("label", dim_name.replace("_", " ").title()),
            cardinality=data.get("cardinality", "single"),
            filterable=fc.get("filterable", True),
            sortable=fc.get("sortable", False),
            required=fc.get("required", False),
        )
        db_session.flush()  # ensure dim.id is available

        synonyms_map: dict[str, list[str]] = data.get("synonyms", {})
        values: list[str] = data.get("values", [])

        for idx, value in enumerate(values):
            syns = synonyms_map.get(value, [])
            repo.upsert_term(
                dimension_id=dim.id,
                value=value,
                sort_order=idx,
                synonyms=syns if syns else None,
            )

    db_session.commit()
    print(f"Seeded {len(DIMENSION_DATA)} taxonomy dimensions.")


if __name__ == "__main__":
    with Session() as session:
        seed(session)
