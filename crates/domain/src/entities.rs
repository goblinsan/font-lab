use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use base64::Engine;

use crate::slug::make_slug;

// ── FontSample ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FontSample {
    pub id: i64,
    pub filename: String,
    pub original_filename: String,
    pub slug: Option<String>,
    pub font_name: Option<String>,
    pub font_category: Option<String>,
    pub style: Option<String>,
    pub genre: Option<String>,
    pub theme: Option<String>,
    pub era: Option<String>,
    pub provenance: Option<String>,
    pub confidence: Option<f64>,
    pub notes: Option<String>,
    pub source: Option<String>,
    pub restoration_notes: Option<String>,
    pub tags: Vec<String>,
    pub file_size: Option<i64>,
    pub content_type: Option<String>,
    pub uploaded_at: DateTime<Utc>,

    // Extended taxonomy
    pub origin_context: Option<String>,
    pub source_type: Option<String>,
    pub restoration_status: Option<String>,
    pub rights_status: Option<String>,
    pub rights_notes: Option<String>,
    pub completeness: Option<f64>,
    pub moods: Vec<String>,
    pub use_cases: Vec<String>,
    pub construction_traits: Vec<String>,
    pub visual_traits: Vec<String>,

    // Curation
    pub review_status: Option<String>,
    pub is_archived: bool,
    pub archived_at: Option<DateTime<Utc>>,
}

impl FontSample {
    pub fn generate_slug(&mut self) {
        if let Some(ref name) = self.font_name {
            if !name.is_empty() {
                self.slug = Some(make_slug(name));
            }
        }
    }
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct CreateSample {
    pub original_filename: String,
    pub content_type: Option<String>,
    pub file_size: Option<i64>,
    pub font_name: Option<String>,
    pub font_category: Option<String>,
    pub style: Option<String>,
    pub genre: Option<String>,
    pub theme: Option<String>,
    pub era: Option<String>,
    pub provenance: Option<String>,
    pub confidence: Option<f64>,
    pub notes: Option<String>,
    pub source: Option<String>,
    pub restoration_notes: Option<String>,
    pub tags: Vec<String>,
    pub origin_context: Option<String>,
    pub source_type: Option<String>,
    pub restoration_status: Option<String>,
    pub rights_status: Option<String>,
    pub rights_notes: Option<String>,
    pub completeness: Option<f64>,
    pub moods: Vec<String>,
    pub use_cases: Vec<String>,
    pub construction_traits: Vec<String>,
    pub visual_traits: Vec<String>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct UpdateSample {
    pub font_name: Option<String>,
    pub font_category: Option<String>,
    pub style: Option<String>,
    pub genre: Option<String>,
    pub theme: Option<String>,
    pub era: Option<String>,
    pub provenance: Option<String>,
    pub confidence: Option<f64>,
    pub notes: Option<String>,
    pub source: Option<String>,
    pub restoration_notes: Option<String>,
    pub tags: Option<Vec<String>>,
    pub origin_context: Option<String>,
    pub source_type: Option<String>,
    pub restoration_status: Option<String>,
    pub rights_status: Option<String>,
    pub rights_notes: Option<String>,
    pub completeness: Option<f64>,
    pub moods: Option<Vec<String>>,
    pub use_cases: Option<Vec<String>>,
    pub construction_traits: Option<Vec<String>>,
    pub visual_traits: Option<Vec<String>>,
    pub review_status: Option<String>,
}

// ── Glyph ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Glyph {
    pub id: i64,
    pub sample_id: i64,
    pub filename: String,
    pub bbox_x: i32,
    pub bbox_y: i32,
    pub bbox_w: i32,
    pub bbox_h: i32,
    pub label: Option<String>,
    pub advance_width: Option<i32>,
    pub left_bearing: Option<i32>,
    pub verified: bool,
    pub synthesized: bool,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct UpdateGlyph {
    pub label: Option<String>,
    pub bbox_x: Option<i32>,
    pub bbox_y: Option<i32>,
    pub bbox_w: Option<i32>,
    pub bbox_h: Option<i32>,
    pub advance_width: Option<i32>,
    pub left_bearing: Option<i32>,
    pub verified: Option<bool>,
}

// ── FontVariant ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FontVariant {
    pub id: i64,
    pub sample_id: i64,
    pub variant_name: String,
    pub weight: Option<String>,
    pub width: Option<String>,
    pub slope: Option<String>,
    pub optical_size: Option<String>,
    pub lifecycle_state: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

// ── FontAlias ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FontAlias {
    pub id: i64,
    pub sample_id: i64,
    pub alias: String,
    pub locale: Option<String>,
    pub created_at: DateTime<Utc>,
}

// ── FontFile ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FontFile {
    pub id: i64,
    pub sample_id: i64,
    pub variant_id: Option<i64>,
    pub filename: String,
    pub file_format: String,
    pub file_size: Option<i64>,
    pub sha256: Option<String>,
    pub is_primary: bool,
    pub created_at: DateTime<Utc>,
}

// ── PreviewAsset ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PreviewAsset {
    pub id: i64,
    pub sample_id: i64,
    pub variant_id: Option<i64>,
    pub asset_type: String,
    pub filename: String,
    pub width: Option<i32>,
    pub height: Option<i32>,
    pub created_at: DateTime<Utc>,
}

// ── GlyphCoverageSummary ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlyphCoverageSummary {
    pub id: i64,
    pub sample_id: i64,
    pub total_glyphs: i32,
    pub verified_glyphs: i32,
    pub latin_basic_count: i32,
    pub latin_extended_count: i32,
    pub digits_count: i32,
    pub punctuation_count: i32,
    pub coverage_percent: f64,
    pub updated_at: DateTime<Utc>,
}

// ── Taxonomy ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaxonomyDimension {
    pub id: i64,
    pub name: String,
    pub label: String,
    pub cardinality: String,
    pub filterable: bool,
    pub sortable: bool,
    pub required: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaxonomyTerm {
    pub id: i64,
    pub dimension_id: i64,
    pub value: String,
    pub parent_id: Option<i64>,
    pub sort_order: i32,
    pub synonyms: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FontSampleTaxonomy {
    pub id: i64,
    pub sample_id: i64,
    pub term_id: i64,
    pub assigned_at: DateTime<Utc>,
}

// ── Provenance ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceArtifact {
    pub id: i64,
    pub sample_id: i64,
    pub artifact_type: String,
    pub title: Option<String>,
    pub publisher: Option<String>,
    pub publication_date: Option<String>,
    pub repository: Option<String>,
    pub identifier: Option<String>,
    pub scan_filename: Option<String>,
    pub scan_resolution_dpi: Option<i32>,
    pub rights_statement: Option<String>,
    pub rights_uri: Option<String>,
    pub notes: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceRecord {
    pub id: i64,
    pub sample_id: i64,
    pub artifact_id: Option<i64>,
    pub event_type: String,
    pub actor: Option<String>,
    pub outcome: Option<String>,
    pub confidence: Option<f64>,
    pub completeness: Option<f64>,
    pub notes: Option<String>,
    pub created_at: DateTime<Utc>,
}

// ── Audit ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CurationAuditLog {
    pub id: i64,
    pub sample_id: Option<i64>,
    pub actor: Option<String>,
    pub action: String,
    pub entity_type: Option<String>,
    pub entity_id: Option<i64>,
    pub field_name: Option<String>,
    pub old_value: Option<String>,
    pub new_value: Option<String>,
    pub created_at: DateTime<Utc>,
}

// ── API Keys ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiKey {
    pub id: i64,
    pub key: String,
    pub owner: String,
    pub scope: String,
    pub is_active: bool,
    pub rate_limit: i32,
    pub created_at: DateTime<Utc>,
}

impl ApiKey {
    pub fn generate_key() -> String {
        use rand::Rng;
        let bytes: [u8; 32] = rand::rng().random();
        base64::engine::general_purpose::URL_SAFE_NO_PAD.encode(bytes)
    }

    pub fn has_write_access(&self) -> bool {
        self.scope == "write" || self.scope == "admin"
    }

    pub fn has_admin_access(&self) -> bool {
        self.scope == "admin"
    }
}

// ── Job ──

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum JobStatus {
    Queued,
    Running,
    Succeeded,
    Failed,
    Canceled,
}

impl std::fmt::Display for JobStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Queued => write!(f, "queued"),
            Self::Running => write!(f, "running"),
            Self::Succeeded => write!(f, "succeeded"),
            Self::Failed => write!(f, "failed"),
            Self::Canceled => write!(f, "canceled"),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum JobKind {
    Segmentation,
    Ocr,
    Export,
    Validation,
}

impl std::fmt::Display for JobKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Segmentation => write!(f, "segmentation"),
            Self::Ocr => write!(f, "ocr"),
            Self::Export => write!(f, "export"),
            Self::Validation => write!(f, "validation"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Job {
    pub id: i64,
    pub kind: JobKind,
    pub status: JobStatus,
    pub sample_id: Option<i64>,
    pub input_params: Option<String>,
    pub engine_version: String,
    pub error_detail: Option<String>,
    pub started_at: Option<DateTime<Utc>>,
    pub finished_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}

// ── FontBuild ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FontBuild {
    pub id: i64,
    pub sample_id: i64,
    pub job_id: Option<i64>,
    pub format: String,
    pub filename: String,
    pub file_size: Option<i64>,
    pub sha256: Option<String>,
    pub source_package_id: Option<i64>,
    pub created_at: DateTime<Utc>,
}
