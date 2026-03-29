use crate::error::AppError;
use crate::state::AppState;
use axum::extract::{Path, Query, State};
use axum::Json;
use font_lab_application::catalog as catalog_svc;
use serde::Deserialize;
use std::sync::Arc;

#[derive(Debug, Deserialize)]
pub struct SearchQuery {
    pub q: Option<String>,
    pub font_name: Option<String>,
    pub font_category: Option<String>,
    pub style: Option<String>,
    pub theme: Option<String>,
    pub tag: Option<String>,
}

/// GET /api/v1/catalog — List catalog entries
pub async fn list_catalog(
    State(state): State<Arc<AppState>>,
) -> Result<Json<Vec<catalog_svc::CatalogEntry>>, AppError> {
    let entries = catalog_svc::list_catalog(&state.pool).await?;
    Ok(Json(entries))
}

/// GET /api/v1/catalog/search — Search catalog
pub async fn search_catalog(
    State(state): State<Arc<AppState>>,
    Query(_q): Query<SearchQuery>,
) -> Result<Json<Vec<catalog_svc::CatalogEntry>>, AppError> {
    // For now, return full catalog; full-text search to be implemented
    let entries = catalog_svc::list_catalog(&state.pool).await?;
    Ok(Json(entries))
}

#[derive(Debug, Deserialize)]
pub struct SimilarQuery {
    pub limit: Option<usize>,
    pub min_score: Option<f64>,
}

/// GET /api/v1/fonts/:font_id/similar — Find similar fonts
pub async fn similar_fonts(
    State(state): State<Arc<AppState>>,
    Path(font_id): Path<i64>,
    Query(q): Query<SimilarQuery>,
) -> Result<Json<Vec<catalog_svc::SimilarEntry>>, AppError> {
    let limit = q.limit.unwrap_or(10).min(50);
    let min_score = q.min_score.unwrap_or(0.0);
    let entries = catalog_svc::find_similar(&state.pool, font_id, limit, min_score).await?;
    Ok(Json(entries))
}
