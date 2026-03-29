use crate::error::AppError;
use crate::state::AppState;
use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::Json;
use font_lab_application::keys as key_svc;
use font_lab_domain::entities::ApiKey;
use serde::{Deserialize, Serialize};
use std::sync::Arc;

#[derive(Debug, Deserialize)]
pub struct CreateKeyRequest {
    pub owner: String,
    pub scope: Option<String>,
    pub rate_limit: Option<i32>,
}

#[derive(Debug, Serialize)]
pub struct ApiKeyResponse {
    pub id: i64,
    pub key: String,
    pub owner: String,
    pub scope: String,
    pub is_active: bool,
    pub rate_limit: i32,
    pub created_at: String,
}

impl From<ApiKey> for ApiKeyResponse {
    fn from(k: ApiKey) -> Self {
        Self {
            id: k.id,
            key: k.key,
            owner: k.owner,
            scope: k.scope,
            is_active: k.is_active,
            rate_limit: k.rate_limit,
            created_at: k.created_at.to_rfc3339(),
        }
    }
}

/// POST /api/v1/keys — Create a new API key
pub async fn create_key(
    State(state): State<Arc<AppState>>,
    Json(req): Json<CreateKeyRequest>,
) -> Result<(StatusCode, Json<ApiKeyResponse>), AppError> {
    let scope = req.scope.unwrap_or_else(|| "read".into());
    let rate_limit = req.rate_limit.unwrap_or(1000).clamp(1, 100_000);

    let key = key_svc::create_key(&state.pool, &req.owner, &scope, rate_limit).await?;
    Ok((StatusCode::CREATED, Json(ApiKeyResponse::from(key))))
}

/// GET /api/v1/keys — List all API keys
pub async fn list_keys(
    State(state): State<Arc<AppState>>,
) -> Result<Json<Vec<ApiKeyResponse>>, AppError> {
    let keys = key_svc::list_keys(&state.pool).await?;
    Ok(Json(keys.into_iter().map(ApiKeyResponse::from).collect()))
}

/// DELETE /api/v1/keys/:key_id — Revoke an API key
pub async fn revoke_key(
    State(state): State<Arc<AppState>>,
    Path(key_id): Path<i64>,
) -> Result<StatusCode, AppError> {
    key_svc::revoke_key(&state.pool, key_id).await?;
    Ok(StatusCode::NO_CONTENT)
}
