"""SQLAlchemy ORM models for font-lab."""

import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
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
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    _tags: Mapped[str | None] = mapped_column("tags", Text, nullable=True, default="[]")
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
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
