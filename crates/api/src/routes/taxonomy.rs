use crate::error::AppError;
use crate::state::AppState;
use axum::extract::State;
use axum::Json;
use font_lab_db::repo::taxonomy as tax_repo;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::Arc;

/// GET /api/v1/taxonomy — List all taxonomy dimensions and terms
pub async fn list_taxonomy(
    State(state): State<Arc<AppState>>,
) -> Result<Json<Value>, AppError> {
    let dimensions = tax_repo::list_dimensions(&state.pool)
        .await
        .map_err(|e| AppError(font_lab_domain::errors::DomainError::Internal(e.to_string())))?;

    let mut result = HashMap::new();
    for dim in &dimensions {
        let terms = tax_repo::list_terms(&state.pool, dim.id)
            .await
            .map_err(|e| {
                AppError(font_lab_domain::errors::DomainError::Internal(e.to_string()))
            })?;
        let values: Vec<String> = terms.iter().map(|t| t.value.clone()).collect();
        result.insert(dim.name.clone(), values);
    }

    Ok(Json(json!(result)))
}
