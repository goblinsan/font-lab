"""SQLAlchemy ORM models for font-lab."""

import json
import secrets
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref as sa_backref

from app.database import Base


class FontSample(Base):
    """A scanned or photographed font sample image with metadata."""

    __tablename__ = "font_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    font_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    font_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    theme: Mapped[str | None] = mapped_column(String(100), nullable=True)
    era: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provenance: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    restoration_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    _tags: Mapped[str | None] = mapped_column("tags", Text, nullable=True, default="[]")
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Extended taxonomy fields (issues #34, #35, #37, #38)
    origin_context: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    restoration_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rights_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rights_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completeness: Mapped[float | None] = mapped_column(Float, nullable=True)
    _moods: Mapped[str | None] = mapped_column("moods", Text, nullable=True, default="[]")
    _use_cases: Mapped[str | None] = mapped_column("use_cases", Text, nullable=True, default="[]")
    _construction_traits: Mapped[str | None] = mapped_column(
        "construction_traits", Text, nullable=True, default="[]"
    )
    _visual_traits: Mapped[str | None] = mapped_column(
        "visual_traits", Text, nullable=True, default="[]"
    )

    @property
    def tags(self) -> list[str]:
        try:
            return json.loads(self._tags or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self._tags = json.dumps(value)

    @property
    def moods(self) -> list[str]:
        try:
            return json.loads(self._moods or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @moods.setter
    def moods(self, value: list[str]) -> None:
        self._moods = json.dumps(value)

    @property
    def use_cases(self) -> list[str]:
        try:
            return json.loads(self._use_cases or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @use_cases.setter
    def use_cases(self, value: list[str]) -> None:
        self._use_cases = json.dumps(value)

    @property
    def construction_traits(self) -> list[str]:
        try:
            return json.loads(self._construction_traits or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @construction_traits.setter
    def construction_traits(self, value: list[str]) -> None:
        self._construction_traits = json.dumps(value)

    @property
    def visual_traits(self) -> list[str]:
        try:
            return json.loads(self._visual_traits or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @visual_traits.setter
    def visual_traits(self, value: list[str]) -> None:
        self._visual_traits = json.dumps(value)


class Glyph(Base):
    """A single character crop extracted from a FontSample image."""

    __tablename__ = "glyphs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("font_samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_w: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_h: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str | None] = mapped_column(String(10), nullable=True)
    advance_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    left_bearing: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    synthesized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ApiKey(Base):
    """An API key granting access to the developer platform."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[str] = mapped_column(String(100), nullable=False, default="read")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rate_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @staticmethod
    def generate() -> str:
        """Generate a cryptographically secure API key."""
        return secrets.token_urlsafe(32)


# ---------------------------------------------------------------------------
# Issue #42 – Font variants, aliases, files, preview assets, glyph coverage
# ---------------------------------------------------------------------------


class FontVariant(Base):
    """A named variant (weight/style/optical-size) of a FontSample.

    Represents a single instantiation of a reconstructed or sourced font
    (e.g. "Bold Italic", "Caption").  Multiple variants share a parent
    ``FontSample`` but differ in their typographic attributes.
    """

    __tablename__ = "font_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("font_samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    weight: Mapped[str | None] = mapped_column(String(100), nullable=True)
    width: Mapped[str | None] = mapped_column(String(100), nullable=True)
    slope: Mapped[str | None] = mapped_column(String(100), nullable=True)
    optical_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lifecycle_state: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sample = relationship("FontSample", back_populates="variants")

    __table_args__ = (
        UniqueConstraint("sample_id", "variant_name", name="uq_font_variant"),
    )


class FontAlias(Base):
    """An alternative name or display name for a FontSample.

    Aliases support alternate historical names, trade names, or locale-specific
    labels that should resolve to the same canonical record.
    """

    __tablename__ = "font_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("font_samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    locale: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sample = relationship("FontSample", back_populates="aliases")

    __table_args__ = (
        UniqueConstraint("sample_id", "alias", name="uq_font_alias"),
    )


class FontFile(Base):
    """A binary font file asset attached to a FontSample or FontVariant.

    Stores references to the actual font files (TTF, OTF, WOFF2, etc.) that
    are produced during reconstruction, along with size and hash for integrity
    checking.
    """

    __tablename__ = "font_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("font_samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("font_variants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sample = relationship("FontSample", back_populates="font_files")
    variant = relationship("FontVariant")


class PreviewAsset(Base):
    """A rendered preview image for a FontSample or FontVariant.

    Preview assets are generated images (e.g. specimen sheets, waterfall
    specimens, character grid images) stored alongside the source upload.
    """

    __tablename__ = "preview_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("font_samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("font_variants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sample = relationship("FontSample", back_populates="preview_assets")
    variant = relationship("FontVariant")


class GlyphCoverageSummary(Base):
    """Aggregated glyph coverage statistics for a FontSample.

    Stores counts per Unicode block or script so that API consumers and search
    pipelines can quickly assess coverage without scanning every individual
    glyph row.
    """

    __tablename__ = "glyph_coverage_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("font_samples.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_glyphs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_glyphs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latin_basic_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latin_extended_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    digits_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    punctuation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coverage_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sample = relationship("FontSample", back_populates="coverage_summary")


# ---------------------------------------------------------------------------
# Issue #43 – Taxonomy tables and controlled vocabularies
# ---------------------------------------------------------------------------


class TaxonomyDimension(Base):
    """A named taxonomy dimension (e.g. "style", "genre", "moods").

    Each dimension groups a set of controlled vocabulary terms and defines
    whether it is single-select or multi-select.
    """

    __tablename__ = "taxonomy_dimensions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    cardinality: Mapped[str] = mapped_column(String(10), nullable=False, default="single")
    filterable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sortable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    terms = relationship("TaxonomyTerm", back_populates="dimension", cascade="all, delete-orphan")


class TaxonomyTerm(Base):
    """A single controlled vocabulary value within a TaxonomyDimension.

    Terms can also carry synonym lists and a parent term to represent
    hierarchical relationships (e.g. genre → parent style).
    """

    __tablename__ = "taxonomy_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dimension_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("taxonomy_dimensions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("taxonomy_terms.id", ondelete="SET NULL"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    _synonyms: Mapped[str | None] = mapped_column("synonyms", Text, nullable=True, default="[]")

    dimension = relationship("TaxonomyDimension", back_populates="terms")
    children = relationship(
        "TaxonomyTerm",
        backref=sa_backref("parent", remote_side="TaxonomyTerm.id"),
        foreign_keys=[parent_id],
    )

    __table_args__ = (
        UniqueConstraint("dimension_id", "value", name="uq_taxonomy_term"),
    )

    @property
    def synonyms(self) -> list[str]:
        try:
            return json.loads(self._synonyms or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @synonyms.setter
    def synonyms(self, value: list[str]) -> None:
        self._synonyms = json.dumps(value)


class FontSampleTaxonomy(Base):
    """Junction table linking a FontSample to its taxonomy term assignments.

    Using an explicit junction table (rather than JSON columns) enables
    efficient facet-count queries and normalized filtering.
    """

    __tablename__ = "font_sample_taxonomy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("font_samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    term_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("taxonomy_terms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("sample_id", "term_id", name="uq_sample_taxonomy"),
        Index("ix_sample_taxonomy_sample", "sample_id"),
        Index("ix_sample_taxonomy_term", "term_id"),
    )


# ---------------------------------------------------------------------------
# Issue #44 – Provenance and source artifact schema
# ---------------------------------------------------------------------------


class SourceArtifact(Base):
    """A physical or digital source artifact associated with a FontSample.

    Records the original item (book, specimen, photograph, scan file) from
    which the font was sourced, including rights and digitisation metadata.
    """

    __tablename__ = "source_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("font_samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    repository: Mapped[str | None] = mapped_column(String(500), nullable=True)
    identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scan_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scan_resolution_dpi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rights_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    rights_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sample = relationship("FontSample", back_populates="source_artifacts")
    provenance_records = relationship(
        "ProvenanceRecord", back_populates="artifact", cascade="all, delete-orphan"
    )


class ProvenanceRecord(Base):
    """A timestamped provenance / review event for a FontSample or SourceArtifact.

    Tracks the restoration workflow history: each step (segmentation, outlining,
    kerning, rights review, etc.) is recorded with the actor, outcome, notes,
    and reconstruction confidence at that point in time.
    """

    __tablename__ = "provenance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("font_samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("source_artifacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    completeness: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sample = relationship("FontSample", back_populates="provenance_records")
    artifact = relationship("SourceArtifact", back_populates="provenance_records")

    __table_args__ = (Index("ix_provenance_sample_event", "sample_id", "event_type"),)


# ---------------------------------------------------------------------------
# Issue #45 – Search projection and ranking support
# ---------------------------------------------------------------------------


class FontSearchIndex(Base):
    """Denormalized search projection row for fast filtering and ranking.

    One row per FontSample; updated asynchronously after any metadata change.
    Stores pre-computed similarity features, facet values, and a combined
    full-text search blob for back-end query acceleration.
    """

    __tablename__ = "font_search_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("font_samples.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # Denormalized scalar facets (copies of FontSample fields for fast filtering)
    font_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    font_category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    style: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    era: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    origin_context: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    restoration_status: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    rights_status: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    completeness: Mapped[float | None] = mapped_column(Float, nullable=True)
    glyph_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Multi-value facets stored as JSON text for direct search/filter access
    _tags: Mapped[str | None] = mapped_column("tags", Text, nullable=True, default="[]")
    _moods: Mapped[str | None] = mapped_column("moods", Text, nullable=True, default="[]")
    _use_cases: Mapped[str | None] = mapped_column("use_cases", Text, nullable=True, default="[]")
    _visual_traits: Mapped[str | None] = mapped_column(
        "visual_traits", Text, nullable=True, default="[]"
    )
    _construction_traits: Mapped[str | None] = mapped_column(
        "construction_traits", Text, nullable=True, default="[]"
    )
    # Full-text search blob: concatenation of all searchable text fields
    search_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Similarity feature vector stored as JSON (for cosine/Jaccard ranking)
    _feature_vector: Mapped[str | None] = mapped_column(
        "feature_vector", Text, nullable=True, default="{}"
    )
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sample = relationship("FontSample", back_populates="search_index")

    @property
    def tags(self) -> list[str]:
        try:
            return json.loads(self._tags or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self._tags = json.dumps(value)

    @property
    def moods(self) -> list[str]:
        try:
            return json.loads(self._moods or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @moods.setter
    def moods(self, value: list[str]) -> None:
        self._moods = json.dumps(value)

    @property
    def use_cases(self) -> list[str]:
        try:
            return json.loads(self._use_cases or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @use_cases.setter
    def use_cases(self, value: list[str]) -> None:
        self._use_cases = json.dumps(value)

    @property
    def visual_traits(self) -> list[str]:
        try:
            return json.loads(self._visual_traits or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @visual_traits.setter
    def visual_traits(self, value: list[str]) -> None:
        self._visual_traits = json.dumps(value)

    @property
    def construction_traits(self) -> list[str]:
        try:
            return json.loads(self._construction_traits or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @construction_traits.setter
    def construction_traits(self, value: list[str]) -> None:
        self._construction_traits = json.dumps(value)

    @property
    def feature_vector(self) -> dict:
        try:
            return json.loads(self._feature_vector or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    @feature_vector.setter
    def feature_vector(self, value: dict) -> None:
        self._feature_vector = json.dumps(value)


# ---------------------------------------------------------------------------
# Back-populate relationships on FontSample
# ---------------------------------------------------------------------------

FontSample.variants = relationship(
    "FontVariant", back_populates="sample", cascade="all, delete-orphan"
)
FontSample.aliases = relationship(
    "FontAlias", back_populates="sample", cascade="all, delete-orphan"
)
FontSample.font_files = relationship(
    "FontFile", back_populates="sample", cascade="all, delete-orphan"
)
FontSample.preview_assets = relationship(
    "PreviewAsset", back_populates="sample", cascade="all, delete-orphan"
)
FontSample.coverage_summary = relationship(
    "GlyphCoverageSummary",
    back_populates="sample",
    cascade="all, delete-orphan",
    uselist=False,
)
FontSample.source_artifacts = relationship(
    "SourceArtifact", back_populates="sample", cascade="all, delete-orphan"
)
FontSample.provenance_records = relationship(
    "ProvenanceRecord", back_populates="sample", cascade="all, delete-orphan"
)
FontSample.search_index = relationship(
    "FontSearchIndex",
    back_populates="sample",
    cascade="all, delete-orphan",
    uselist=False,
)

