"""Pytest configuration and shared fixtures for font-lab tests."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# In-memory SQLite database for tests (single shared connection via StaticPool)
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite://"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create tables once for the whole test session."""
    from app.models import (  # noqa: F401
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

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_db():
    """Truncate tables between tests."""
    from app.models import (
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

    yield
    db = TestSession()
    try:
        db.query(ProvenanceRecord).delete()
        db.query(SourceArtifact).delete()
        db.query(FontSampleTaxonomy).delete()
        db.query(FontSearchIndex).delete()
        db.query(GlyphCoverageSummary).delete()
        db.query(PreviewAsset).delete()
        db.query(FontFile).delete()
        db.query(FontVariant).delete()
        db.query(FontAlias).delete()
        db.query(Glyph).delete()
        db.query(FontSample).delete()
        db.query(ApiKey).delete()
        db.query(TaxonomyTerm).delete()
        db.query(TaxonomyDimension).delete()
        db.commit()
    finally:
        db.close()
    # Reset in-memory rate limit counters between tests
    from app import auth as auth_module
    auth_module._REQUEST_LOG.clear()


@pytest.fixture(scope="session")
def upload_dir():
    """Temporary directory used as the upload destination during tests."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["UPLOAD_DIR"] = tmp
        # Patch the routes modules as well (already imported, so patch in-place)
        import app.routes.images as img_routes
        import app.routes.glyphs as glyph_routes

        img_routes.UPLOAD_DIR = tmp
        glyph_routes.UPLOAD_DIR = tmp
        import app.routes.reconstruction as reconstruction_routes

        reconstruction_routes.UPLOAD_DIR = tmp
        import app.routes.editor as editor_routes

        editor_routes.UPLOAD_DIR = tmp
        yield tmp


@pytest.fixture(scope="session")
def client(upload_dir, setup_test_db):
    """FastAPI TestClient with overridden DB and upload directory."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_image_bytes() -> bytes:
    """Return a minimal valid PNG byte string (1×1 red pixel)."""
    # A real 1×1 red PNG
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def make_blank_image_bytes(width: int = 20, height: int = 20) -> bytes:
    """Return a valid all-white PNG image with no dark pixels (yields no glyphs)."""
    from PIL import Image
    import io

    img = Image.new("L", (width, height), color=255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_segmentable_image_bytes() -> bytes:
    """Return a simple PNG with two clearly separated dark rectangles.

    The image is 40 px wide × 20 px tall, white background with two 8×12 black
    rectangles separated by a 6-px gap — enough for the segmentation algorithm
    to detect two distinct glyphs.
    """
    from PIL import Image
    import io

    img = Image.new("L", (40, 20), color=255)  # white background
    pixels = img.load()
    # Left glyph: columns 2–9, rows 4–15
    for x in range(2, 10):
        for y in range(4, 16):
            pixels[x, y] = 0
    # Right glyph: columns 16–23, rows 4–15
    for x in range(16, 24):
        for y in range(4, 16):
            pixels[x, y] = 0

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
