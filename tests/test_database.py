"""Tests for the database persistence layer (issues #42–#47)."""

from __future__ import annotations

import io

import pytest

from app.models import (
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
    CurationAuditLog,
)
from app.repository import (
    FontAliasRepository,
    FontSampleRepository,
    FontVariantRepository,
    GlyphCoverageRepository,
    PreviewAssetRepository,
    ProvenanceRepository,
    SearchIndexRepository,
    TaxonomyRepository,
    CurationAuditLogRepository,
)
from tests.conftest import TestSession, make_image_bytes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sample(db, font_name="TestFont", style="Serif", **kwargs) -> FontSample:
    sample = FontSample(
        filename=f"{font_name.replace(' ', '_')}.png",
        original_filename=f"{font_name}.png",
        font_name=font_name,
        style=style,
        **kwargs,
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


# ---------------------------------------------------------------------------
# Issue #42 – FontVariant
# ---------------------------------------------------------------------------


class TestFontVariant:
    def test_create_variant(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            variant = FontVariant(
                sample_id=sample.id,
                variant_name="Bold",
                weight="Bold",
                lifecycle_state="draft",
            )
            db.add(variant)
            db.commit()
            db.refresh(variant)
            assert variant.id is not None
            assert variant.sample_id == sample.id
            assert variant.variant_name == "Bold"
            assert variant.lifecycle_state == "draft"
        finally:
            db.close()

    def test_variant_repository_list(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            repo = FontVariantRepository(db)
            for name in ("Regular", "Bold", "Italic"):
                repo.add(FontVariant(sample_id=sample.id, variant_name=name))
            db.commit()
            variants = repo.list_for_sample(sample.id)
            assert len(variants) == 3
            assert {v.variant_name for v in variants} == {"Regular", "Bold", "Italic"}
        finally:
            db.close()

    def test_variant_unique_constraint(self):
        from sqlalchemy.exc import IntegrityError

        db = TestSession()
        try:
            sample = _make_sample(db)
            db.add(FontVariant(sample_id=sample.id, variant_name="Bold"))
            db.commit()
            db.add(FontVariant(sample_id=sample.id, variant_name="Bold"))
            with pytest.raises(IntegrityError):
                db.commit()
        finally:
            db.rollback()
            db.close()

    def test_variant_cascade_delete(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            db.add(FontVariant(sample_id=sample.id, variant_name="Regular"))
            db.commit()
            db.delete(sample)
            db.commit()
            count = db.query(FontVariant).count()
            assert count == 0
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #42 – FontAlias
# ---------------------------------------------------------------------------


class TestFontAlias:
    def test_create_alias(self):
        db = TestSession()
        try:
            sample = _make_sample(db, font_name="Helvetica")
            alias = FontAlias(sample_id=sample.id, alias="Helv", locale="en")
            db.add(alias)
            db.commit()
            db.refresh(alias)
            assert alias.id is not None
            assert alias.alias == "Helv"
        finally:
            db.close()

    def test_alias_repository(self):
        db = TestSession()
        try:
            sample = _make_sample(db, font_name="Garamond")
            repo = FontAliasRepository(db)
            repo.add(FontAlias(sample_id=sample.id, alias="Garamond Old Style"))
            repo.add(FontAlias(sample_id=sample.id, alias="EB Garamond"))
            db.commit()
            aliases = repo.list_for_sample(sample.id)
            assert len(aliases) == 2
        finally:
            db.close()

    def test_find_by_alias(self):
        db = TestSession()
        try:
            sample = _make_sample(db, font_name="Futura")
            db.add(FontAlias(sample_id=sample.id, alias="Futura Book"))
            db.commit()
            repo = FontAliasRepository(db)
            found = repo.find_by_alias("Futura Book")
            assert found is not None
            assert found.sample_id == sample.id
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #42 – FontFile
# ---------------------------------------------------------------------------


class TestFontFile:
    def test_create_font_file(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            ff = FontFile(
                sample_id=sample.id,
                filename="helvetica.ttf",
                file_format="ttf",
                file_size=102400,
                is_primary=True,
            )
            db.add(ff)
            db.commit()
            db.refresh(ff)
            assert ff.id is not None
            assert ff.is_primary is True
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #42 – PreviewAsset
# ---------------------------------------------------------------------------


class TestPreviewAsset:
    def test_create_preview_asset(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            asset = PreviewAsset(
                sample_id=sample.id,
                asset_type="waterfall",
                filename="preview_waterfall.png",
                width=800,
                height=600,
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)
            assert asset.id is not None
            assert asset.asset_type == "waterfall"
        finally:
            db.close()

    def test_preview_asset_repository(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            repo = PreviewAssetRepository(db)
            repo.add(PreviewAsset(sample_id=sample.id, asset_type="specimen", filename="s.png"))
            repo.add(PreviewAsset(sample_id=sample.id, asset_type="grid", filename="g.png"))
            db.commit()
            assets = repo.list_for_sample(sample.id)
            assert len(assets) == 2
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #42 – GlyphCoverageSummary
# ---------------------------------------------------------------------------


class TestGlyphCoverageSummary:
    def test_create_coverage_summary(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            summary = GlyphCoverageSummary(
                sample_id=sample.id,
                total_glyphs=52,
                verified_glyphs=40,
                latin_basic_count=52,
                coverage_percent=0.55,
            )
            db.add(summary)
            db.commit()
            db.refresh(summary)
            assert summary.id is not None
            assert summary.total_glyphs == 52
        finally:
            db.close()

    def test_coverage_repository_upsert(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            glyphs = [
                Glyph(
                    sample_id=sample.id,
                    filename="g.png",
                    bbox_x=0, bbox_y=0, bbox_w=10, bbox_h=10,
                    label=ch,
                    verified=(ch in "abc"),
                )
                for ch in "abcABC123"
            ]
            for g in glyphs:
                db.add(g)
            db.commit()
            repo = GlyphCoverageRepository(db)
            summary = repo.upsert(sample.id, glyphs)
            db.commit()
            assert summary.total_glyphs == 9
            assert summary.verified_glyphs == 3
            assert summary.latin_basic_count == 6  # a-c + A-C
            assert summary.digits_count == 3
        finally:
            db.close()

    def test_coverage_upsert_is_idempotent(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            glyphs = [
                Glyph(
                    sample_id=sample.id, filename="g.png",
                    bbox_x=0, bbox_y=0, bbox_w=10, bbox_h=10, label="a",
                )
            ]
            for g in glyphs:
                db.add(g)
            db.commit()
            repo = GlyphCoverageRepository(db)
            repo.upsert(sample.id, glyphs)
            db.commit()
            repo.upsert(sample.id, glyphs)
            db.commit()
            count = db.query(GlyphCoverageSummary).filter_by(sample_id=sample.id).count()
            assert count == 1
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #43 – TaxonomyDimension and TaxonomyTerm
# ---------------------------------------------------------------------------


class TestTaxonomyModels:
    def test_create_dimension(self):
        db = TestSession()
        try:
            dim = TaxonomyDimension(name="style", label="Style", cardinality="single")
            db.add(dim)
            db.commit()
            db.refresh(dim)
            assert dim.id is not None
            assert dim.name == "style"
        finally:
            db.close()

    def test_create_term(self):
        db = TestSession()
        try:
            dim = TaxonomyDimension(name="style", label="Style", cardinality="single")
            db.add(dim)
            db.flush()
            term = TaxonomyTerm(dimension_id=dim.id, value="Serif", sort_order=0)
            term.synonyms = ["roman"]
            db.add(term)
            db.commit()
            db.refresh(term)
            assert term.id is not None
            assert term.value == "Serif"
            assert "roman" in term.synonyms
        finally:
            db.close()

    def test_taxonomy_repository_upsert_dimension(self):
        db = TestSession()
        try:
            repo = TaxonomyRepository(db)
            dim = repo.upsert_dimension("genre", "Genre", cardinality="single")
            db.commit()
            assert dim.id is not None
            # Upsert again – should not create a duplicate
            repo.upsert_dimension("genre", "Genre (updated)")
            db.commit()
            count = db.query(TaxonomyDimension).filter_by(name="genre").count()
            assert count == 1
        finally:
            db.close()

    def test_taxonomy_repository_upsert_term(self):
        db = TestSession()
        try:
            repo = TaxonomyRepository(db)
            dim = repo.upsert_dimension("style", "Style")
            db.flush()
            term = repo.upsert_term(dim.id, "Serif", synonyms=["roman"])
            db.commit()
            assert term.id is not None
            # Upsert again
            repo.upsert_term(dim.id, "Serif", synonyms=["roman", "traditional"])
            db.commit()
            count = db.query(TaxonomyTerm).filter_by(dimension_id=dim.id, value="Serif").count()
            assert count == 1
        finally:
            db.close()

    def test_assign_and_remove_taxonomy_term(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            repo = TaxonomyRepository(db)
            dim = repo.upsert_dimension("style", "Style")
            db.flush()
            term = repo.upsert_term(dim.id, "Serif")
            db.commit()
            repo.assign_term(sample.id, term.id)
            db.commit()
            assignments = repo.get_assignments(sample.id)
            assert len(assignments) == 1
            repo.remove_term(sample.id, term.id)
            db.commit()
            assert repo.get_assignments(sample.id) == []
        finally:
            db.close()

    def test_assign_term_idempotent(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            repo = TaxonomyRepository(db)
            dim = repo.upsert_dimension("style", "Style")
            db.flush()
            term = repo.upsert_term(dim.id, "Serif")
            db.commit()
            repo.assign_term(sample.id, term.id)
            db.commit()
            repo.assign_term(sample.id, term.id)
            db.commit()
            count = db.query(FontSampleTaxonomy).filter_by(
                sample_id=sample.id, term_id=term.id
            ).count()
            assert count == 1
        finally:
            db.close()

    def test_facet_counts(self):
        db = TestSession()
        try:
            repo = TaxonomyRepository(db)
            dim = repo.upsert_dimension("style", "Style")
            db.flush()
            serif = repo.upsert_term(dim.id, "Serif")
            sans = repo.upsert_term(dim.id, "Sans-Serif")
            db.commit()
            s1 = _make_sample(db, "A")
            s2 = _make_sample(db, "B")
            s3 = _make_sample(db, "C")
            repo.assign_term(s1.id, serif.id)
            repo.assign_term(s2.id, serif.id)
            repo.assign_term(s3.id, sans.id)
            db.commit()
            counts = repo.facet_counts("style")
            assert counts["Serif"] == 2
            assert counts["Sans-Serif"] == 1
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #44 – SourceArtifact and ProvenanceRecord
# ---------------------------------------------------------------------------


class TestProvenanceModels:
    def test_create_source_artifact(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            artifact = SourceArtifact(
                sample_id=sample.id,
                artifact_type="Printed Specimen",
                title="Specimen Book 1923",
                rights_statement="Public Domain",
            )
            db.add(artifact)
            db.commit()
            db.refresh(artifact)
            assert artifact.id is not None
            assert artifact.artifact_type == "Printed Specimen"
        finally:
            db.close()

    def test_create_provenance_record(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            record = ProvenanceRecord(
                sample_id=sample.id,
                event_type="segmentation",
                actor="user@example.com",
                outcome="success",
                confidence=0.9,
                notes="Initial segmentation run",
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            assert record.id is not None
            assert record.event_type == "segmentation"
        finally:
            db.close()

    def test_provenance_repository(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            repo = ProvenanceRepository(db)
            artifact = SourceArtifact(
                sample_id=sample.id, artifact_type="Printed Specimen", title="Test"
            )
            repo.add_artifact(artifact)
            db.commit()
            artifacts = repo.list_artifacts(sample.id)
            assert len(artifacts) == 1
            repo.add_record(ProvenanceRecord(
                sample_id=sample.id, event_type="upload", outcome="success"
            ))
            repo.add_record(ProvenanceRecord(
                sample_id=sample.id, artifact_id=artifact.id,
                event_type="segmentation", outcome="success",
            ))
            db.commit()
            records = repo.list_records(sample.id)
            assert len(records) == 2
        finally:
            db.close()

    def test_provenance_cascade_delete(self):
        db = TestSession()
        try:
            sample = _make_sample(db)
            db.add(ProvenanceRecord(sample_id=sample.id, event_type="upload"))
            db.commit()
            db.delete(sample)
            db.commit()
            count = db.query(ProvenanceRecord).count()
            assert count == 0
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #45 – FontSearchIndex
# ---------------------------------------------------------------------------


class TestSearchIndex:
    def test_create_search_index(self):
        db = TestSession()
        try:
            sample = _make_sample(db, font_name="Bodoni", style="Serif", era="1800s")
            sample.tags = ["elegant", "classic"]
            db.commit()
            repo = SearchIndexRepository(db)
            index = repo.upsert(sample, glyph_count=26)
            db.commit()
            assert index.id is not None
            assert index.font_name == "Bodoni"
            assert index.style == "Serif"
            assert index.era == "1800s"
            assert index.glyph_count == 26
            assert "elegant" in index.tags
        finally:
            db.close()

    def test_search_index_text_blob(self):
        db = TestSession()
        try:
            sample = _make_sample(db, font_name="Futura", style="Sans-Serif")
            sample.notes = "Geometric sans designed by Paul Renner"
            db.commit()
            index = SearchIndexRepository(db).upsert(sample)
            db.commit()
            assert "Futura" in (index.search_text or "")
            assert "Geometric" in (index.search_text or "")
        finally:
            db.close()

    def test_search_index_feature_vector(self):
        db = TestSession()
        try:
            sample = _make_sample(db, font_name="Gill Sans", style="Sans-Serif")
            sample.moods = ["Clean", "Friendly"]
            db.commit()
            index = SearchIndexRepository(db).upsert(sample)
            db.commit()
            fv = index.feature_vector
            assert fv["style"] == "Sans-Serif"
            assert isinstance(fv["moods"], list)
        finally:
            db.close()

    def test_search_index_upsert_is_idempotent(self):
        db = TestSession()
        try:
            sample = _make_sample(db, font_name="Helvetica")
            repo = SearchIndexRepository(db)
            repo.upsert(sample)
            db.commit()
            repo.upsert(sample)
            db.commit()
            count = db.query(FontSearchIndex).filter_by(sample_id=sample.id).count()
            assert count == 1
        finally:
            db.close()

    def test_search_index_cascade_delete(self):
        db = TestSession()
        try:
            sample = _make_sample(db, font_name="Caslon")
            repo = SearchIndexRepository(db)
            repo.upsert(sample)
            db.commit()
            db.delete(sample)
            db.commit()
            count = db.query(FontSearchIndex).count()
            assert count == 0
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #47 – FontSampleRepository
# ---------------------------------------------------------------------------


class TestFontSampleRepository:
    def test_get_existing(self):
        db = TestSession()
        try:
            sample = _make_sample(db, font_name="Arial")
            repo = FontSampleRepository(db)
            found = repo.get(sample.id)
            assert found is not None
            assert found.font_name == "Arial"
        finally:
            db.close()

    def test_get_missing_returns_none(self):
        db = TestSession()
        try:
            repo = FontSampleRepository(db)
            assert repo.get(99999) is None
        finally:
            db.close()

    def test_list_with_style_filter(self):
        db = TestSession()
        try:
            _make_sample(db, "Helvetica", style="Sans-Serif")
            _make_sample(db, "Garamond", style="Serif")
            repo = FontSampleRepository(db)
            results = repo.list(style="Sans-Serif")
            assert len(results) == 1
            assert results[0].font_name == "Helvetica"
        finally:
            db.close()

    def test_search_freetext(self):
        db = TestSession()
        try:
            _make_sample(db, "Windsor", era="Victorian")
            _make_sample(db, "Helvetica", era="1950s")
            repo = FontSampleRepository(db)
            items, total = repo.search("Victorian")
            assert total == 1
            assert items[0].font_name == "Windsor"
        finally:
            db.close()

    def test_add_and_delete(self):
        db = TestSession()
        try:
            repo = FontSampleRepository(db)
            sample = FontSample(
                filename="test.png", original_filename="test.png", font_name="Test"
            )
            repo.add(sample)
            db.commit()
            assert sample.id is not None
            repo.delete(sample)
            db.commit()
            assert repo.get(sample.id) is None
        finally:
            db.close()

    def test_add_auto_generates_slug(self):
        """FontSampleRepository.add() generates a slug from font_name (issue #51)."""
        db = TestSession()
        try:
            repo = FontSampleRepository(db)
            sample = FontSample(
                filename="auto_slug.png",
                original_filename="auto_slug.png",
                font_name="Times New Roman",
            )
            repo.add(sample)
            db.commit()
            assert sample.slug == "times-new-roman"
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #50 – Validation rules and integrity constraints
# ---------------------------------------------------------------------------


class TestSlugAndArchive:
    def test_slug_unique_constraint(self):
        """Duplicate slugs on different samples raise IntegrityError (issue #50, #51)."""
        from sqlalchemy.exc import IntegrityError

        db = TestSession()
        try:
            s1 = _make_sample(db, "Garamond")
            s1.slug = "garamond"
            db.commit()
            s2 = _make_sample(db, "Garamond Classic")
            s2.slug = "garamond"
            with pytest.raises(IntegrityError):
                db.commit()
        finally:
            db.rollback()
            db.close()

    def test_slug_lookup_via_repository(self):
        """get_by_slug returns the correct FontSample (issue #51 slug index)."""
        db = TestSession()
        try:
            sample = _make_sample(db, "Bodoni")
            # Slug is auto-generated by FontSampleRepository.add() when font_name is set.
            # _make_sample uses FontSample directly, so set slug manually for this test.
            sample.slug = "bodoni"
            db.commit()
            repo = FontSampleRepository(db)
            found = repo.get_by_slug("bodoni")
            assert found is not None
            assert found.id == sample.id
        finally:
            db.close()

    def test_get_by_slug_missing_returns_none(self):
        db = TestSession()
        try:
            repo = FontSampleRepository(db)
            assert repo.get_by_slug("does-not-exist") is None
        finally:
            db.close()

    def test_archive_sets_flags(self):
        """archive() sets is_archived=True and records archived_at (issue #50)."""
        db = TestSession()
        try:
            sample = _make_sample(db, "OldFont")
            assert sample.is_archived is False
            assert sample.archived_at is None
            repo = FontSampleRepository(db)
            repo.archive(sample)
            db.commit()
            db.refresh(sample)
            assert sample.is_archived is True
            assert sample.archived_at is not None
        finally:
            db.close()

    def test_list_excludes_archived_by_default(self):
        """list() hides archived samples unless include_archived=True (issue #50)."""
        db = TestSession()
        try:
            active = _make_sample(db, "ActiveFont")
            archived = _make_sample(db, "ArchivedFont")
            repo = FontSampleRepository(db)
            repo.archive(archived)
            db.commit()
            visible = repo.list()
            names = [s.font_name for s in visible]
            assert "ActiveFont" in names
            assert "ArchivedFont" not in names
            all_samples = repo.list(include_archived=True)
            all_names = [s.font_name for s in all_samples]
            assert "ArchivedFont" in all_names
        finally:
            db.close()

    def test_search_excludes_archived_by_default(self):
        """search() excludes archived samples by default (issue #50)."""
        db = TestSession()
        try:
            _make_sample(db, "VisibleFont")
            archived = _make_sample(db, "HiddenFont")
            repo = FontSampleRepository(db)
            repo.archive(archived)
            db.commit()
            items, total = repo.search("Font")
            names = [s.font_name for s in items]
            assert "VisibleFont" in names
            assert "HiddenFont" not in names
        finally:
            db.close()

    def test_review_status_defaults_to_pending(self):
        """FontSample.review_status defaults to 'pending' (issue #50)."""
        db = TestSession()
        try:
            sample = _make_sample(db, "PendingFont")
            assert sample.review_status == "pending"
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #51 – Indexing strategy (search index enhancements)
# ---------------------------------------------------------------------------


class TestSearchIndexEnhancements:
    def test_review_status_synced_to_search_index(self):
        """upsert() copies review_status to FontSearchIndex (issue #51, #52)."""
        db = TestSession()
        try:
            sample = _make_sample(db, "ApprovedFont")
            sample.review_status = "approved"
            db.commit()
            repo = SearchIndexRepository(db)
            index = repo.upsert(sample)
            db.commit()
            assert index.review_status == "approved"
        finally:
            db.close()

    def test_search_index_composite_indexes_exist(self):
        """Composite indexes on font_search_index are reflected in table metadata."""
        from sqlalchemy import inspect as sa_inspect
        from tests.conftest import test_engine

        insp = sa_inspect(test_engine)
        index_names = {idx["name"] for idx in insp.get_indexes("font_search_index")}
        assert "ix_search_category_style" in index_names
        assert "ix_search_restoration_rights" in index_names
        assert "ix_search_confidence_completeness" in index_names
        assert "ix_search_review_status_glyph_count" in index_names


# ---------------------------------------------------------------------------
# Issue #52 – Audit trail for curation and restoration changes
# ---------------------------------------------------------------------------


class TestCurationAuditLog:
    def test_create_audit_entry(self):
        """CurationAuditLog entries can be created and queried (issue #52)."""
        db = TestSession()
        try:
            sample = _make_sample(db, "AuditedFont")
            entry = CurationAuditLog(
                sample_id=sample.id,
                actor="curator@example.com",
                action="metadata_edit",
                entity_type="sample",
                entity_id=sample.id,
                field_name="font_name",
                old_value='"OldName"',
                new_value='"AuditedFont"',
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            assert entry.id is not None
            assert entry.action == "metadata_edit"
            assert entry.field_name == "font_name"
        finally:
            db.close()

    def test_audit_repository_log_helper(self):
        """CurationAuditLogRepository.log() serialises values to JSON (issue #52)."""
        db = TestSession()
        try:
            sample = _make_sample(db, "LogFont")
            repo = CurationAuditLogRepository(db)
            entry = repo.log(
                sample_id=sample.id,
                actor="system",
                action="review_action",
                entity_type="sample",
                entity_id=sample.id,
                field_name="review_status",
                old_value="pending",
                new_value="approved",
            )
            db.commit()
            assert entry.old_value == '"pending"'
            assert entry.new_value == '"approved"'
        finally:
            db.close()

    def test_list_for_sample(self):
        """list_for_sample returns entries ordered by creation time (issue #52)."""
        db = TestSession()
        try:
            sample = _make_sample(db, "MultiAuditFont")
            repo = CurationAuditLogRepository(db)
            repo.log(
                sample_id=sample.id,
                actor="user1",
                action="metadata_edit",
                field_name="style",
                old_value="Serif",
                new_value="Sans-Serif",
            )
            repo.log(
                sample_id=sample.id,
                actor="user2",
                action="review_action",
                field_name="review_status",
                old_value="pending",
                new_value="approved",
            )
            db.commit()
            entries = repo.list_for_sample(sample.id)
            assert len(entries) == 2
            assert entries[0].action == "metadata_edit"
            assert entries[1].action == "review_action"
        finally:
            db.close()

    def test_list_by_action(self):
        """list_by_action filters by action type (issue #52)."""
        db = TestSession()
        try:
            s1 = _make_sample(db, "Font1")
            s2 = _make_sample(db, "Font2")
            repo = CurationAuditLogRepository(db)
            repo.log(sample_id=s1.id, actor="a", action="review_action")
            repo.log(sample_id=s2.id, actor="a", action="metadata_edit")
            repo.log(sample_id=s1.id, actor="a", action="review_action")
            db.commit()
            review_entries = repo.list_by_action("review_action")
            assert len(review_entries) == 2
            assert all(e.action == "review_action" for e in review_entries)
        finally:
            db.close()

    def test_audit_log_survives_sample_deletion(self):
        """Audit rows remain after the FontSample is deleted (issue #52).

        The FK uses ``ON DELETE SET NULL`` so audit rows are kept even when
        the source sample is hard-deleted.  In SQLite (tests) FK enforcement
        is disabled by default, so we assert only that the row still exists
        and that no cascade-delete removes it.
        """
        db = TestSession()
        try:
            sample = _make_sample(db, "DeletedFont")
            repo = CurationAuditLogRepository(db)
            repo.log(
                sample_id=sample.id,
                actor="curator",
                action="publication_status",
                new_value="published",
            )
            db.commit()
            db.delete(sample)
            db.commit()
            # The audit row must still exist regardless of what happened to sample_id.
            all_entries = db.query(CurationAuditLog).all()
            assert len(all_entries) == 1
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Issue #54 – Database migration chain
# ---------------------------------------------------------------------------


class TestMigrationChain:
    def test_upgrade_head_creates_all_tables(self):
        """alembic upgrade head runs cleanly on a fresh database (issue #54).

        Applies both migration revisions and checks every expected table is
        present in the resulting schema.
        """
        import tempfile
        import os
        from alembic.config import Config
        from alembic import command
        from sqlalchemy import create_engine, inspect

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            db_url = f"sqlite:///{db_path}"
            cfg = Config("alembic.ini")
            cfg.set_main_option("sqlalchemy.url", db_url)
            command.upgrade(cfg, "head")

            engine = create_engine(db_url)
            table_names = set(inspect(engine).get_table_names())
            engine.dispose()

            expected = {
                "font_samples",
                "glyphs",
                "api_keys",
                "font_variants",
                "font_aliases",
                "font_files",
                "preview_assets",
                "glyph_coverage_summaries",
                "source_artifacts",
                "provenance_records",
                "taxonomy_dimensions",
                "taxonomy_terms",
                "font_sample_taxonomy",
                "font_search_index",
                "curation_audit_log",
            }
            assert expected.issubset(table_names), (
                f"Missing tables after upgrade: {expected - table_names}"
            )
        finally:
            os.unlink(db_path)

    def test_downgrade_base_removes_app_tables(self):
        """alembic downgrade base cleanly removes all application tables (issue #54)."""
        import tempfile
        import os
        from alembic.config import Config
        from alembic import command
        from sqlalchemy import create_engine, inspect

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            db_url = f"sqlite:///{db_path}"
            cfg = Config("alembic.ini")
            cfg.set_main_option("sqlalchemy.url", db_url)
            command.upgrade(cfg, "head")
            command.downgrade(cfg, "base")

            engine = create_engine(db_url)
            table_names = set(inspect(engine).get_table_names())
            engine.dispose()

            app_tables = {
                "font_samples", "glyphs", "api_keys", "font_variants",
                "font_aliases", "font_files", "preview_assets",
                "glyph_coverage_summaries", "source_artifacts",
                "provenance_records", "taxonomy_dimensions", "taxonomy_terms",
                "font_sample_taxonomy", "font_search_index", "curation_audit_log",
            }
            remaining = app_tables & table_names
            assert not remaining, f"Tables not removed by downgrade: {remaining}"
        finally:
            os.unlink(db_path)


# ---------------------------------------------------------------------------
# Issue #56 – Seed taxonomy and sample data
# ---------------------------------------------------------------------------


class TestTaxonomySeed:
    def test_seed_populates_all_dimensions(self):
        """seed() inserts all expected taxonomy dimensions (issue #56)."""
        db = TestSession()
        try:
            from scripts.seed_taxonomy import seed, DIMENSION_DATA
            seed(db)
            dims = db.query(TaxonomyDimension).all()
            dim_names = {d.name for d in dims}
            assert dim_names == set(DIMENSION_DATA.keys())
        finally:
            db.close()

    def test_seed_populates_terms(self):
        """seed() inserts vocabulary terms for each dimension (issue #56)."""
        db = TestSession()
        try:
            from scripts.seed_taxonomy import seed
            seed(db)
            total_terms = db.query(TaxonomyTerm).count()
            assert total_terms > 0, "No taxonomy terms were seeded"
        finally:
            db.close()

    def test_seed_is_idempotent(self):
        """Running seed() twice does not create duplicate rows (issue #56)."""
        db = TestSession()
        try:
            from scripts.seed_taxonomy import seed
            seed(db)
            count_after_first = db.query(TaxonomyDimension).count()
            terms_after_first = db.query(TaxonomyTerm).count()
            seed(db)
            count_after_second = db.query(TaxonomyDimension).count()
            terms_after_second = db.query(TaxonomyTerm).count()
            assert count_after_first == count_after_second
            assert terms_after_first == terms_after_second
        finally:
            db.close()

