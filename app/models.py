"""SQLAlchemy ORM models for font-lab."""

import json
import secrets
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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
