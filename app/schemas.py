"""Pydantic schemas for request/response serialisation."""

import string
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FontSampleBase(BaseModel):
    font_name: str | None = None
    font_category: str | None = None
    style: str | None = None
    genre: str | None = None
    theme: str | None = None
    era: str | None = None
    provenance: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    notes: str | None = None
    source: str | None = None
    restoration_notes: str | None = None
    tags: list[str] = []
    # Extended taxonomy fields (issues #34, #35, #37, #38)
    origin_context: str | None = None
    source_type: str | None = None
    restoration_status: str | None = None
    rights_status: str | None = None
    rights_notes: str | None = None
    completeness: float | None = Field(default=None, ge=0.0, le=1.0)
    moods: list[str] = []
    use_cases: list[str] = []
    construction_traits: list[str] = []
    visual_traits: list[str] = []
    # Curation review state (issue #50, #52)
    review_status: str | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            # Accept comma-separated string from multipart forms
            return [t.strip() for t in v.split(",") if t.strip()]
        return v or []

    @field_validator("moods", "use_cases", "construction_traits", "visual_traits", mode="before")
    @classmethod
    def parse_list_fields(cls, v):
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return v or []


class FontSampleCreate(FontSampleBase):
    pass


class FontSampleUpdate(BaseModel):
    font_name: str | None = None
    font_category: str | None = None
    style: str | None = None
    genre: str | None = None
    theme: str | None = None
    era: str | None = None
    provenance: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    notes: str | None = None
    source: str | None = None
    restoration_notes: str | None = None
    tags: list[str] | None = None
    # Extended taxonomy fields
    origin_context: str | None = None
    source_type: str | None = None
    restoration_status: str | None = None
    rights_status: str | None = None
    rights_notes: str | None = None
    completeness: float | None = Field(default=None, ge=0.0, le=1.0)
    moods: list[str] | None = None
    use_cases: list[str] | None = None
    construction_traits: list[str] | None = None
    visual_traits: list[str] | None = None
    # Curation review state (issue #50, #52)
    review_status: str | None = None


class FontSampleResponse(FontSampleBase):
    id: int
    slug: str | None = None
    filename: str
    original_filename: str
    file_size: int | None = None
    content_type: str | None = None
    uploaded_at: datetime
    is_archived: bool = False
    archived_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Glyph schemas
# ---------------------------------------------------------------------------

class GlyphResponse(BaseModel):
    id: int
    sample_id: int
    filename: str
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    label: str | None = None
    advance_width: int | None = None
    left_bearing: int | None = None
    verified: bool = False
    synthesized: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GlyphUpdate(BaseModel):
    label: str | None = None
    bbox_x: int | None = None
    bbox_y: int | None = None
    bbox_w: int | None = None
    bbox_h: int | None = None
    advance_width: int | None = None
    left_bearing: int | None = None
    verified: bool | None = None


# ---------------------------------------------------------------------------
# Reconstruction / export schemas
# ---------------------------------------------------------------------------

_DEFAULT_CHARSET = string.ascii_letters + string.digits


class ReconstructRequest(BaseModel):
    charset: str = _DEFAULT_CHARSET


class ExportRequest(BaseModel):
    format: str = "ttf"
    font_name: str = "ReconstructedFont"
    style_name: str = "Regular"


# ---------------------------------------------------------------------------
# Catalog schemas
# ---------------------------------------------------------------------------

class CatalogEntryResponse(FontSampleResponse):
    """FontSampleResponse extended with a preview URL and glyph count."""

    preview_url: str
    glyph_count: int = 0


# ---------------------------------------------------------------------------
# Editor / QA schemas
# ---------------------------------------------------------------------------

class GlyphCompareEntry(BaseModel):
    """Comparison entry pairing a glyph's source image with its outline URL."""

    id: int
    label: str | None = None
    source_url: str
    outline_url: str
    verified: bool = False
    synthesized: bool = False


# ---------------------------------------------------------------------------
# v1 API schemas
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    total: int
    page: int
    per_page: int
    items: list


class ErrorResponse(BaseModel):
    """Standardised API error envelope."""

    error: str
    detail: str | None = None
    code: int


class SimilarFontEntry(BaseModel):
    """A font entry returned from the similarity query."""

    id: int
    font_name: str | None = None
    font_category: str | None = None
    style: str | None = None
    genre: str | None = None
    theme: str | None = None
    era: str | None = None
    tags: list[str] = []
    moods: list[str] = []
    visual_traits: list[str] = []
    preview_url: str
    similarity_score: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


class PreviewConfigResponse(BaseModel):
    """Embeddable render configuration for a font specimen."""

    sample_id: int
    font_name: str | None = None
    preview_url: str
    specimen_url: str
    embed_url: str
    available_chars: list[str] = []
    suggested_text: str = "The quick brown fox"


class ApiKeyCreate(BaseModel):
    """Request body for creating a new API key."""

    owner: str
    scope: str = "read"
    rate_limit: int = Field(default=1000, ge=1, le=100_000)


class ApiKeyResponse(BaseModel):
    """Response returned after creating or retrieving an API key."""

    id: int
    key: str
    owner: str
    scope: str
    is_active: bool
    rate_limit: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Audit trail schemas (issue #52)
# ---------------------------------------------------------------------------

class CurationAuditLogResponse(BaseModel):
    """A single audit log entry for a curation or restoration change."""

    id: int
    sample_id: int | None = None
    actor: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: int | None = None
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
