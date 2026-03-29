"""Repository layer – persistence contracts for font-lab.

Each ``*Repository`` class encapsulates all database reads and writes for its
aggregate root so that application services and route handlers never need to
construct raw SQLAlchemy queries directly.

Design contract
---------------
* Methods accept and return ORM model instances (or scalars / lists thereof).
* All writes must be committed by the caller via ``db.commit()`` so that
  multiple repository operations can participate in a single transaction.
* ``get_db`` session injection is assumed; repositories are instantiated
  per-request.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import (
    CurationAuditLog,
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
    _make_slug,
)


# ---------------------------------------------------------------------------
# FontSampleRepository
# ---------------------------------------------------------------------------


class FontSampleRepository:
    """CRUD and query operations for :class:`~app.models.FontSample`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # -- internal helpers ----------------------------------------------------

    @staticmethod
    def _active_filter(query: Any) -> Any:
        """Apply a filter that excludes archived samples from *query*."""
        return query.filter(FontSample.is_archived == False)  # noqa: E712

    # -- reads ---------------------------------------------------------------

    def get(self, sample_id: int) -> FontSample | None:
        """Return the FontSample with *sample_id*, or ``None``."""
        return self.db.get(FontSample, sample_id)

    def get_by_slug(self, slug: str) -> FontSample | None:
        """Return the FontSample matching *slug*, or ``None``.

        Uses the unique slug index for O(1) lookup (issue #51).
        """
        return (
            self.db.query(FontSample)
            .filter(FontSample.slug == slug)
            .first()
        )

    def list(
        self,
        *,
        font_name: str | None = None,
        font_category: str | None = None,
        style: str | None = None,
        genre: str | None = None,
        theme: str | None = None,
        era: str | None = None,
        origin_context: str | None = None,
        source_type: str | None = None,
        restoration_status: str | None = None,
        rights_status: str | None = None,
        tag: str | None = None,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> list[FontSample]:
        """Return a filtered, paginated list of FontSamples.

        Archived samples are excluded by default; pass ``include_archived=True``
        to include them (issue #50).
        """
        q = self.db.query(FontSample)
        if not include_archived:
            q = self._active_filter(q)
        if font_name:
            q = q.filter(FontSample.font_name.ilike(f"%{font_name}%"))
        if font_category:
            q = q.filter(FontSample.font_category.ilike(f"%{font_category}%"))
        if style:
            q = q.filter(FontSample.style.ilike(f"%{style}%"))
        if genre:
            q = q.filter(FontSample.genre.ilike(f"%{genre}%"))
        if theme:
            q = q.filter(FontSample.theme.ilike(f"%{theme}%"))
        if era:
            q = q.filter(FontSample.era.ilike(f"%{era}%"))
        if origin_context:
            q = q.filter(FontSample.origin_context.ilike(f"%{origin_context}%"))
        if source_type:
            q = q.filter(FontSample.source_type.ilike(f"%{source_type}%"))
        if restoration_status:
            q = q.filter(FontSample.restoration_status.ilike(f"%{restoration_status}%"))
        if rights_status:
            q = q.filter(FontSample.rights_status.ilike(f"%{rights_status}%"))
        samples = q.offset(offset).limit(limit).all()
        if tag:
            samples = [s for s in samples if tag.lower() in [t.lower() for t in s.tags]]
        return samples

    def count(self, **filters: Any) -> int:
        """Return a total count matching the same filters as :meth:`list`."""
        q = self.db.query(func.count(FontSample.id))
        if not filters.get("include_archived"):
            q = self._active_filter(q)
        if filters.get("font_name"):
            q = q.filter(FontSample.font_name.ilike(f"%{filters['font_name']}%"))
        if filters.get("style"):
            q = q.filter(FontSample.style.ilike(f"%{filters['style']}%"))
        if filters.get("genre"):
            q = q.filter(FontSample.genre.ilike(f"%{filters['genre']}%"))
        if filters.get("era"):
            q = q.filter(FontSample.era.ilike(f"%{filters['era']}%"))
        return q.scalar() or 0

    def search(
        self,
        q: str | None = None,
        *,
        offset: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> tuple[list[FontSample], int]:
        """Full-text + facet search.  Returns ``(items, total)``.

        Archived samples are excluded unless ``include_archived=True`` is
        passed as a filter keyword (issue #50).
        """
        query = self.db.query(FontSample)
        if not filters.get("include_archived"):
            query = self._active_filter(query)
        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    FontSample.font_name.ilike(like),
                    FontSample.font_category.ilike(like),
                    FontSample.style.ilike(like),
                    FontSample.genre.ilike(like),
                    FontSample.theme.ilike(like),
                    FontSample.era.ilike(like),
                    FontSample.origin_context.ilike(like),
                    FontSample.notes.ilike(like),
                )
            )
        for field in (
            "font_name", "font_category", "style", "genre", "theme", "era",
            "origin_context", "source_type", "restoration_status", "rights_status",
        ):
            if filters.get(field):
                col = getattr(FontSample, field)
                query = query.filter(col.ilike(f"%{filters[field]}%"))
        if filters.get("tag"):
            query = query.filter(FontSample._tags.ilike(f"%{filters['tag']}%"))
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return items, total

    # -- writes --------------------------------------------------------------

    def add(self, sample: FontSample) -> FontSample:
        """Add *sample* to the session (caller must commit).

        If ``sample.slug`` is not yet set and ``sample.font_name`` is
        available, a slug is auto-generated via :func:`~app.models._make_slug`.
        Callers that need a guaranteed-unique slug should handle any
        ``IntegrityError`` raised by the database unique constraint (e.g. by
        appending the sample id after the initial commit).
        """
        if sample.slug is None and sample.font_name:
            sample.slug = _make_slug(sample.font_name)
        self.db.add(sample)
        return sample

    def archive(self, sample: FontSample) -> FontSample:
        """Soft-delete *sample* by marking it archived (issue #50).

        The record is retained in the database with ``is_archived=True`` so
        that audit logs and referential integrity constraints remain intact.
        Caller must commit.
        """
        sample.is_archived = True
        sample.archived_at = datetime.now(timezone.utc)
        return sample

    def delete(self, sample: FontSample) -> None:
        """Hard-delete *sample* from the session (caller must commit)."""
        self.db.delete(sample)


# ---------------------------------------------------------------------------
# FontVariantRepository
# ---------------------------------------------------------------------------


class FontVariantRepository:
    """Persistence contract for :class:`~app.models.FontVariant`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, variant_id: int) -> FontVariant | None:
        return self.db.get(FontVariant, variant_id)

    def list_for_sample(self, sample_id: int) -> list[FontVariant]:
        return (
            self.db.query(FontVariant)
            .filter(FontVariant.sample_id == sample_id)
            .order_by(FontVariant.variant_name)
            .all()
        )

    def add(self, variant: FontVariant) -> FontVariant:
        self.db.add(variant)
        return variant

    def delete(self, variant: FontVariant) -> None:
        self.db.delete(variant)


# ---------------------------------------------------------------------------
# FontAliasRepository
# ---------------------------------------------------------------------------


class FontAliasRepository:
    """Persistence contract for :class:`~app.models.FontAlias`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_sample(self, sample_id: int) -> list[FontAlias]:
        return (
            self.db.query(FontAlias)
            .filter(FontAlias.sample_id == sample_id)
            .order_by(FontAlias.alias)
            .all()
        )

    def find_by_alias(self, alias: str) -> FontAlias | None:
        return (
            self.db.query(FontAlias)
            .filter(FontAlias.alias.ilike(alias))
            .first()
        )

    def add(self, alias: FontAlias) -> FontAlias:
        self.db.add(alias)
        return alias

    def delete(self, alias: FontAlias) -> None:
        self.db.delete(alias)


# ---------------------------------------------------------------------------
# TaxonomyRepository
# ---------------------------------------------------------------------------


class TaxonomyRepository:
    """Persistence contract for taxonomy dimensions and terms."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # Dimensions

    def get_dimension(self, name: str) -> TaxonomyDimension | None:
        return (
            self.db.query(TaxonomyDimension)
            .filter(TaxonomyDimension.name == name)
            .first()
        )

    def list_dimensions(self) -> list[TaxonomyDimension]:
        return self.db.query(TaxonomyDimension).order_by(TaxonomyDimension.name).all()

    def upsert_dimension(self, name: str, label: str, cardinality: str = "single",
                         filterable: bool = True, sortable: bool = False,
                         required: bool = False) -> TaxonomyDimension:
        dim = self.get_dimension(name)
        if dim is None:
            dim = TaxonomyDimension(
                name=name, label=label, cardinality=cardinality,
                filterable=filterable, sortable=sortable, required=required,
            )
            self.db.add(dim)
        else:
            dim.label = label
            dim.cardinality = cardinality
            dim.filterable = filterable
            dim.sortable = sortable
            dim.required = required
        return dim

    # Terms

    def get_term(self, dimension_id: int, value: str) -> TaxonomyTerm | None:
        return (
            self.db.query(TaxonomyTerm)
            .filter(
                TaxonomyTerm.dimension_id == dimension_id,
                TaxonomyTerm.value == value,
            )
            .first()
        )

    def list_terms(self, dimension_id: int) -> list[TaxonomyTerm]:
        return (
            self.db.query(TaxonomyTerm)
            .filter(TaxonomyTerm.dimension_id == dimension_id)
            .order_by(TaxonomyTerm.sort_order, TaxonomyTerm.value)
            .all()
        )

    def upsert_term(self, dimension_id: int, value: str, *,
                    sort_order: int = 0, synonyms: list[str] | None = None,
                    parent_id: int | None = None) -> TaxonomyTerm:
        term = self.get_term(dimension_id, value)
        if term is None:
            term = TaxonomyTerm(
                dimension_id=dimension_id, value=value,
                sort_order=sort_order, parent_id=parent_id,
            )
            self.db.add(term)
        else:
            term.sort_order = sort_order
            term.parent_id = parent_id
        if synonyms is not None:
            term.synonyms = synonyms
        return term

    # FontSample taxonomy assignments

    def assign_term(self, sample_id: int, term_id: int) -> FontSampleTaxonomy:
        existing = (
            self.db.query(FontSampleTaxonomy)
            .filter(
                FontSampleTaxonomy.sample_id == sample_id,
                FontSampleTaxonomy.term_id == term_id,
            )
            .first()
        )
        if existing:
            return existing
        row = FontSampleTaxonomy(sample_id=sample_id, term_id=term_id)
        self.db.add(row)
        return row

    def remove_term(self, sample_id: int, term_id: int) -> None:
        self.db.query(FontSampleTaxonomy).filter(
            FontSampleTaxonomy.sample_id == sample_id,
            FontSampleTaxonomy.term_id == term_id,
        ).delete()

    def get_assignments(self, sample_id: int) -> list[FontSampleTaxonomy]:
        return (
            self.db.query(FontSampleTaxonomy)
            .filter(FontSampleTaxonomy.sample_id == sample_id)
            .all()
        )

    def facet_counts(self, dimension_name: str) -> dict[str, int]:
        """Return ``{term_value: count}`` for a given dimension."""
        dim = self.get_dimension(dimension_name)
        if not dim:
            return {}
        rows = (
            self.db.query(TaxonomyTerm.value, func.count(FontSampleTaxonomy.id))
            .join(FontSampleTaxonomy, FontSampleTaxonomy.term_id == TaxonomyTerm.id)
            .filter(TaxonomyTerm.dimension_id == dim.id)
            .group_by(TaxonomyTerm.value)
            .all()
        )
        return {value: count for value, count in rows}


# ---------------------------------------------------------------------------
# ProvenanceRepository
# ---------------------------------------------------------------------------


class ProvenanceRepository:
    """Persistence contract for :class:`~app.models.SourceArtifact`
    and :class:`~app.models.ProvenanceRecord`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # SourceArtifact

    def list_artifacts(self, sample_id: int) -> list[SourceArtifact]:
        return (
            self.db.query(SourceArtifact)
            .filter(SourceArtifact.sample_id == sample_id)
            .order_by(SourceArtifact.created_at)
            .all()
        )

    def get_artifact(self, artifact_id: int) -> SourceArtifact | None:
        return self.db.get(SourceArtifact, artifact_id)

    def add_artifact(self, artifact: SourceArtifact) -> SourceArtifact:
        self.db.add(artifact)
        return artifact

    def delete_artifact(self, artifact: SourceArtifact) -> None:
        self.db.delete(artifact)

    # ProvenanceRecord

    def list_records(self, sample_id: int) -> list[ProvenanceRecord]:
        return (
            self.db.query(ProvenanceRecord)
            .filter(ProvenanceRecord.sample_id == sample_id)
            .order_by(ProvenanceRecord.created_at)
            .all()
        )

    def add_record(self, record: ProvenanceRecord) -> ProvenanceRecord:
        self.db.add(record)
        return record


# ---------------------------------------------------------------------------
# SearchIndexRepository
# ---------------------------------------------------------------------------


class SearchIndexRepository:
    """Persistence contract for :class:`~app.models.FontSearchIndex`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, sample_id: int) -> FontSearchIndex | None:
        return (
            self.db.query(FontSearchIndex)
            .filter(FontSearchIndex.sample_id == sample_id)
            .first()
        )

    def upsert(self, sample: FontSample, glyph_count: int = 0) -> FontSearchIndex:
        """Create or refresh the search index row for *sample*."""
        index = self.get(sample.id)
        if index is None:
            index = FontSearchIndex(sample_id=sample.id)
            self.db.add(index)
        index.font_name = sample.font_name
        index.font_category = sample.font_category
        index.style = sample.style
        index.genre = sample.genre
        index.era = sample.era
        index.origin_context = sample.origin_context
        index.restoration_status = sample.restoration_status
        index.rights_status = sample.rights_status
        index.review_status = sample.review_status
        index.confidence = sample.confidence
        index.completeness = sample.completeness
        index.glyph_count = glyph_count
        index.tags = sample.tags
        index.moods = sample.moods
        index.use_cases = sample.use_cases
        index.visual_traits = sample.visual_traits
        index.construction_traits = sample.construction_traits
        index.search_text = " ".join(
            filter(
                None,
                [
                    sample.font_name,
                    sample.font_category,
                    sample.style,
                    sample.genre,
                    sample.theme,
                    sample.era,
                    sample.origin_context,
                    sample.notes,
                    sample.provenance,
                    " ".join(sample.tags),
                    " ".join(sample.moods),
                    " ".join(sample.use_cases),
                    " ".join(sample.visual_traits),
                ],
            )
        )
        index.feature_vector = {
            "style": sample.style or "",
            "genre": sample.genre or "",
            "theme": sample.theme or "",
            "font_category": sample.font_category or "",
            "era": sample.era or "",
            "tags": sample.tags,
            "moods": sample.moods,
            "visual_traits": sample.visual_traits,
        }
        index.indexed_at = datetime.now(timezone.utc)
        return index

    def delete(self, sample_id: int) -> None:
        self.db.query(FontSearchIndex).filter(
            FontSearchIndex.sample_id == sample_id
        ).delete()


# ---------------------------------------------------------------------------
# PreviewAssetRepository
# ---------------------------------------------------------------------------


class PreviewAssetRepository:
    """Persistence contract for :class:`~app.models.PreviewAsset`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_sample(self, sample_id: int) -> list[PreviewAsset]:
        return (
            self.db.query(PreviewAsset)
            .filter(PreviewAsset.sample_id == sample_id)
            .order_by(PreviewAsset.created_at)
            .all()
        )

    def add(self, asset: PreviewAsset) -> PreviewAsset:
        self.db.add(asset)
        return asset

    def delete(self, asset: PreviewAsset) -> None:
        self.db.delete(asset)


# ---------------------------------------------------------------------------
# GlyphCoverageRepository
# ---------------------------------------------------------------------------


class GlyphCoverageRepository:
    """Persistence contract for :class:`~app.models.GlyphCoverageSummary`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, sample_id: int) -> GlyphCoverageSummary | None:
        return (
            self.db.query(GlyphCoverageSummary)
            .filter(GlyphCoverageSummary.sample_id == sample_id)
            .first()
        )

    def upsert(self, sample_id: int, glyphs: list[Glyph]) -> GlyphCoverageSummary:
        """Recompute and persist coverage statistics for *sample_id*."""
        summary = self.get(sample_id)
        if summary is None:
            summary = GlyphCoverageSummary(sample_id=sample_id)
            self.db.add(summary)

        labels = [g.label for g in glyphs if g.label]
        total = len(glyphs)
        verified = sum(1 for g in glyphs if g.verified)

        latin_basic = sum(1 for lbl in labels if len(lbl) == 1 and lbl.isascii() and lbl.isalpha())
        digits = sum(1 for lbl in labels if len(lbl) == 1 and lbl.isdigit())
        punctuation = sum(1 for lbl in labels if len(lbl) == 1 and not lbl.isalnum())

        # Latin extended: non-ASCII printable single chars
        latin_ext = sum(
            1 for lbl in labels
            if len(lbl) == 1 and not lbl.isascii() and lbl.isprintable()
        )

        coverage = (len(set(labels)) / 95) if total > 0 else 0.0

        summary.total_glyphs = total
        summary.verified_glyphs = verified
        summary.latin_basic_count = latin_basic
        summary.latin_extended_count = latin_ext
        summary.digits_count = digits
        summary.punctuation_count = punctuation
        summary.coverage_percent = min(round(coverage, 4), 1.0)
        return summary


# ---------------------------------------------------------------------------
# CurationAuditLogRepository
# ---------------------------------------------------------------------------


class CurationAuditLogRepository:
    """Persistence contract for :class:`~app.models.CurationAuditLog`.

    Provides append-only write access (audit rows must never be updated or
    deleted) and targeted read access by sample, action category, and time
    window (issue #52).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, entry: CurationAuditLog) -> CurationAuditLog:
        """Append an audit log entry (caller must commit)."""
        self.db.add(entry)
        return entry

    def log(
        self,
        *,
        sample_id: int | None,
        actor: str | None,
        action: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        field_name: str | None = None,
        old_value: Any = None,
        new_value: Any = None,
    ) -> CurationAuditLog:
        """Convenience helper: create and add an audit entry in one call.

        Serialises *old_value* and *new_value* as JSON strings so callers
        can pass Python objects directly.  Caller must commit.
        """
        entry = CurationAuditLog(
            sample_id=sample_id,
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            old_value=json.dumps(old_value) if old_value is not None else None,
            new_value=json.dumps(new_value) if new_value is not None else None,
        )
        self.db.add(entry)
        return entry

    def list_for_sample(self, sample_id: int) -> list[CurationAuditLog]:
        """Return all audit entries for *sample_id* ordered by creation time."""
        return (
            self.db.query(CurationAuditLog)
            .filter(CurationAuditLog.sample_id == sample_id)
            .order_by(CurationAuditLog.created_at)
            .all()
        )

    def list_by_action(
        self,
        action: str,
        *,
        limit: int = 100,
    ) -> list[CurationAuditLog]:
        """Return the most recent *limit* entries for a given *action* type."""
        return (
            self.db.query(CurationAuditLog)
            .filter(CurationAuditLog.action == action)
            .order_by(CurationAuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
