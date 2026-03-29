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
