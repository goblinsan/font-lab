pub mod samples;
pub mod glyphs;
pub mod catalog;
pub mod keys;
pub mod taxonomy;

use crate::state::AppState;
use axum::{Router, routing::{get, post, patch, delete}};
use std::sync::Arc;
use tower_http::services::ServeDir;

pub fn router(state: Arc<AppState>) -> Router {
    let api_v1 = Router::new()
        // Samples
        .route("/samples", post(samples::create_sample))
        .route("/samples", get(samples::list_samples))
        .route("/samples/{sample_id}", get(samples::get_sample))
        .route("/samples/{sample_id}", patch(samples::update_sample))
        .route("/samples/{sample_id}", delete(samples::delete_sample))
        // Segmentation
        .route(
            "/samples/{sample_id}/segment",
            post(glyphs::segment_sample),
        )
        // Glyphs
        .route(
            "/samples/{sample_id}/glyphs",
            get(glyphs::list_glyphs),
        )
        .route("/glyphs/{glyph_id}", get(glyphs::get_glyph))
        .route("/glyphs/{glyph_id}", patch(glyphs::update_glyph))
        .route("/glyphs/{glyph_id}", delete(glyphs::delete_glyph))
        .route("/glyphs/{glyph_id}/outline", get(glyphs::glyph_outline))
        // Catalog
        .route("/catalog", get(catalog::list_catalog))
        .route("/catalog/search", get(catalog::search_catalog))
        .route("/fonts/{font_id}/similar", get(catalog::similar_fonts))
        // Keys
        .route("/keys", post(keys::create_key))
        .route("/keys", get(keys::list_keys))
        .route("/keys/{key_id}", delete(keys::revoke_key))
        // Taxonomy
        .route("/taxonomy", get(taxonomy::list_taxonomy))
        .with_state(state.clone());

    Router::new()
        .nest("/api/v1", api_v1)
        .nest_service(
            "/uploads",
            ServeDir::new(state.blobs.base_dir()),
        )
}
