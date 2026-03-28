"""Pydantic schemas for request/response serialisation."""

import string
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class FontSampleBase(BaseModel):
    font_name: str | None = None
    font_category: str | None = None
    style: str | None = None
    theme: str | None = None
    notes: str | None = None
    tags: list[str] = []

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            # Accept comma-separated string from multipart forms
            return [t.strip() for t in v.split(",") if t.strip()]
        return v or []


class FontSampleCreate(FontSampleBase):
    pass


class FontSampleUpdate(BaseModel):
    font_name: str | None = None
    font_category: str | None = None
    style: str | None = None
    theme: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class FontSampleResponse(FontSampleBase):
    id: int
    filename: str
    original_filename: str
    file_size: int | None = None
    content_type: str | None = None
    uploaded_at: datetime

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
