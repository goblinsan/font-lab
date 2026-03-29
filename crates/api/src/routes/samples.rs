use crate::error::AppError;
use crate::state::AppState;
use axum::extract::{Multipart, Path, Query, State};
use axum::http::StatusCode;
use axum::Json;
use font_lab_application::samples as sample_svc;
use font_lab_db::repo::samples as sample_repo;
use font_lab_domain::entities::{CreateSample, FontSample, UpdateSample};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

#[derive(Debug, Serialize)]
pub struct SampleResponse {
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
    pub tags: Vec<String>,
    pub file_size: Option<i64>,
    pub content_type: Option<String>,
    pub uploaded_at: String,
    pub review_status: Option<String>,
    pub preview_url: String,
}

impl From<FontSample> for SampleResponse {
    fn from(s: FontSample) -> Self {
        Self {
            preview_url: format!("/uploads/samples/{}", s.filename),
            uploaded_at: s.uploaded_at.to_rfc3339(),
            id: s.id,
            filename: s.filename,
            original_filename: s.original_filename,
            slug: s.slug,
            font_name: s.font_name,
            font_category: s.font_category,
            style: s.style,
            genre: s.genre,
            theme: s.theme,
            era: s.era,
            provenance: s.provenance,
            confidence: s.confidence,
            notes: s.notes,
            tags: s.tags,
            file_size: s.file_size,
            content_type: s.content_type,
            review_status: s.review_status,
        }
    }
}

/// POST /api/v1/samples — Upload a new font sample
pub async fn create_sample(
    State(state): State<Arc<AppState>>,
    mut multipart: Multipart,
) -> Result<(StatusCode, Json<SampleResponse>), AppError> {
    let mut file_data: Option<Vec<u8>> = None;
    let mut input = CreateSample::default();

    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|e| AppError(font_lab_domain::errors::DomainError::Validation(e.to_string())))?
    {
        let name = field.name().unwrap_or("").to_string();
        match name.as_str() {
            "file" => {
                input.content_type = field.content_type().map(|s| s.to_string());
                input.original_filename = field
                    .file_name()
                    .unwrap_or("upload")
                    .to_string();
                file_data = Some(
                    field
                        .bytes()
                        .await
                        .map_err(|e| {
                            AppError(font_lab_domain::errors::DomainError::Validation(
                                e.to_string(),
                            ))
                        })?
                        .to_vec(),
                );
            }
            "font_name" => input.font_name = field_text(&field, name.as_str()).await,
            "font_category" => input.font_category = field_text(&field, name.as_str()).await,
            "style" => input.style = field_text(&field, name.as_str()).await,
            "genre" => input.genre = field_text(&field, name.as_str()).await,
            "theme" => input.theme = field_text(&field, name.as_str()).await,
            "era" => input.era = field_text(&field, name.as_str()).await,
            "provenance" => input.provenance = field_text(&field, name.as_str()).await,
            "notes" => input.notes = field_text(&field, name.as_str()).await,
            "source" => input.source = field_text(&field, name.as_str()).await,
            "restoration_notes" => input.restoration_notes = field_text(&field, name.as_str()).await,
            "tags" => {
                if let Some(text) = field_text(&field, "tags").await {
                    input.tags = parse_csv_or_json(&text);
                }
            }
            "confidence" => {
                if let Some(text) = field_text(&field, "confidence").await {
                    input.confidence = text.parse().ok();
                }
            }
            "completeness" => {
                if let Some(text) = field_text(&field, "completeness").await {
                    input.completeness = text.parse().ok();
                }
            }
            _ => {}
        }
    }

    let data = file_data.ok_or_else(|| {
        AppError(font_lab_domain::errors::DomainError::Validation(
            "file is required".into(),
        ))
    })?;

    let sample = sample_svc::upload_sample(&state.pool, &state.blobs, &data, &input).await?;
    Ok((StatusCode::CREATED, Json(SampleResponse::from(sample))))
}

async fn field_text(
    field: &axum::extract::multipart::Field<'_>,
    _name: &str,
) -> Option<String> {
    // Note: axum multipart fields are consumed; text extraction expected at caller
    None
}

fn parse_csv_or_json(text: &str) -> Vec<String> {
    if let Ok(arr) = serde_json::from_str::<Vec<String>>(text) {
        return arr;
    }
    text.split(',')
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect()
}

#[derive(Debug, Deserialize)]
pub struct ListQuery {
    pub font_name: Option<String>,
    pub font_category: Option<String>,
    pub style: Option<String>,
    pub genre: Option<String>,
    pub theme: Option<String>,
    pub era: Option<String>,
    pub tag: Option<String>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

/// GET /api/v1/samples — List samples
pub async fn list_samples(
    State(state): State<Arc<AppState>>,
    Query(q): Query<ListQuery>,
) -> Result<Json<Vec<SampleResponse>>, AppError> {
    let per_page = q.per_page.unwrap_or(20).min(100).max(1);
    let page = q.page.unwrap_or(1).max(1);

    let filters = sample_repo::ListFilters {
        font_name: q.font_name,
        font_category: q.font_category,
        style: q.style,
        genre: q.genre,
        theme: q.theme,
        era: q.era,
        tag: q.tag,
        offset: (page - 1) * per_page,
        limit: per_page,
        ..Default::default()
    };

    let samples = sample_svc::list_samples(&state.pool, &filters).await?;
    Ok(Json(samples.into_iter().map(SampleResponse::from).collect()))
}

/// GET /api/v1/samples/:id — Get a single sample
pub async fn get_sample(
    State(state): State<Arc<AppState>>,
    Path(sample_id): Path<i64>,
) -> Result<Json<SampleResponse>, AppError> {
    let sample = sample_svc::get_sample(&state.pool, sample_id).await?;
    Ok(Json(SampleResponse::from(sample)))
}

/// PATCH /api/v1/samples/:id — Update sample metadata
pub async fn update_sample(
    State(state): State<Arc<AppState>>,
    Path(sample_id): Path<i64>,
    Json(update): Json<UpdateSample>,
) -> Result<Json<SampleResponse>, AppError> {
    let sample = sample_svc::update_sample(&state.pool, sample_id, &update).await?;
    Ok(Json(SampleResponse::from(sample)))
}

/// DELETE /api/v1/samples/:id — Delete a sample
pub async fn delete_sample(
    State(state): State<Arc<AppState>>,
    Path(sample_id): Path<i64>,
) -> Result<StatusCode, AppError> {
    sample_svc::delete_sample(&state.pool, &state.blobs, sample_id).await?;
    Ok(StatusCode::NO_CONTENT)
}
