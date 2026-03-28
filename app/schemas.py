"""Pydantic schemas for request/response serialisation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class FontSampleBase(BaseModel):
    font_name: str | None = None
    font_category: str | None = None
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
