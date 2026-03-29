use crate::error::AppError;
use crate::state::AppState;
use axum::extract::{Path, State};
use axum::http::{header, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::Json;
use font_lab_application::glyphs as glyph_svc;
use font_lab_application::samples as sample_svc;
use font_lab_domain::entities::{Glyph, UpdateGlyph};
use font_lab_font_engine::vectorize;
use serde::Serialize;
use std::sync::Arc;

#[derive(Debug, Serialize)]
pub struct GlyphResponse {
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
    pub crop_url: String,
}

impl From<Glyph> for GlyphResponse {
    fn from(g: Glyph) -> Self {
        Self {
            crop_url: format!("/uploads/glyphs/{}", g.filename),
            id: g.id,
            sample_id: g.sample_id,
            filename: g.filename,
            bbox_x: g.bbox_x,
            bbox_y: g.bbox_y,
            bbox_w: g.bbox_w,
            bbox_h: g.bbox_h,
            label: g.label,
            advance_width: g.advance_width,
            left_bearing: g.left_bearing,
            verified: g.verified,
            synthesized: g.synthesized,
        }
    }
}

/// POST /api/v1/samples/:sample_id/segment — Run segmentation
pub async fn segment_sample(
    State(state): State<Arc<AppState>>,
    Path(sample_id): Path<i64>,
) -> Result<(StatusCode, Json<Vec<GlyphResponse>>), AppError> {
    let sample = sample_svc::get_sample(&state.pool, sample_id).await?;
    let glyphs =
        glyph_svc::segment_sample(&state.pool, &state.blobs, sample_id, &sample.filename).await?;
    Ok((
        StatusCode::CREATED,
        Json(glyphs.into_iter().map(GlyphResponse::from).collect()),
    ))
}

/// GET /api/v1/samples/:sample_id/glyphs — List glyphs for a sample
pub async fn list_glyphs(
    State(state): State<Arc<AppState>>,
    Path(sample_id): Path<i64>,
) -> Result<Json<Vec<GlyphResponse>>, AppError> {
    let glyphs = glyph_svc::list_glyphs(&state.pool, sample_id).await?;
    Ok(Json(glyphs.into_iter().map(GlyphResponse::from).collect()))
}

/// GET /api/v1/glyphs/:glyph_id — Get a single glyph
pub async fn get_glyph(
    State(state): State<Arc<AppState>>,
    Path(glyph_id): Path<i64>,
) -> Result<Json<GlyphResponse>, AppError> {
    let glyph = glyph_svc::get_glyph(&state.pool, glyph_id).await?;
    Ok(Json(GlyphResponse::from(glyph)))
}

/// PATCH /api/v1/glyphs/:glyph_id — Update glyph
pub async fn update_glyph(
    State(state): State<Arc<AppState>>,
    Path(glyph_id): Path<i64>,
    Json(update): Json<UpdateGlyph>,
) -> Result<Json<GlyphResponse>, AppError> {
    let glyph = glyph_svc::update_glyph(&state.pool, glyph_id, &update).await?;
    Ok(Json(GlyphResponse::from(glyph)))
}

/// DELETE /api/v1/glyphs/:glyph_id — Delete glyph
pub async fn delete_glyph(
    State(state): State<Arc<AppState>>,
    Path(glyph_id): Path<i64>,
) -> Result<StatusCode, AppError> {
    glyph_svc::delete_glyph(&state.pool, &state.blobs, glyph_id).await?;
    Ok(StatusCode::NO_CONTENT)
}

/// GET /api/v1/glyphs/:glyph_id/outline — Get SVG outline
pub async fn glyph_outline(
    State(state): State<Arc<AppState>>,
    Path(glyph_id): Path<i64>,
) -> Result<Response, AppError> {
    let glyph = glyph_svc::get_glyph(&state.pool, glyph_id).await?;
    let glyph_path = state.blobs.path("glyphs", &glyph.filename);

    let svg = tokio::task::spawn_blocking(move || vectorize::glyph_to_svg(&glyph_path))
        .await
        .map_err(|e| {
            AppError(font_lab_domain::errors::DomainError::Processing(
                e.to_string(),
            ))
        })?
        .map_err(|e| {
            AppError(font_lab_domain::errors::DomainError::Processing(
                e.to_string(),
            ))
        })?;

    Ok((
        [(header::CONTENT_TYPE, "image/svg+xml")],
        svg,
    )
        .into_response())
}
