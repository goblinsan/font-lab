use crate::state::AppState;
use axum::extract::FromRequestParts;
use axum::http::request::Parts;
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;
use font_lab_db::repo::api_keys;
use font_lab_domain::entities::ApiKey;
use serde_json::json;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::time::{Duration, Instant};

const ANONYMOUS_LIMIT: usize = 100;
const WINDOW_SECONDS: u64 = 3600;

/// In-memory rate limiter (suitable for single-process deployment).
pub struct RateLimiter {
    requests: Mutex<HashMap<String, Vec<Instant>>>,
}

impl RateLimiter {
    pub fn new() -> Self {
        Self {
            requests: Mutex::new(HashMap::new()),
        }
    }

    pub async fn check(&self, key: &str, limit: usize) -> bool {
        let mut map = self.requests.lock().await;
        let now = Instant::now();
        let cutoff = now - Duration::from_secs(WINDOW_SECONDS);

        let entry = map.entry(key.to_string()).or_default();
        entry.retain(|t| *t > cutoff);

        if entry.len() >= limit {
            return false;
        }
        entry.push(now);
        true
    }
}

/// Optional API key extractor (anonymous access allowed).
pub struct OptionalApiKey(pub Option<ApiKey>);

impl<S> FromRequestParts<S> for OptionalApiKey
where
    S: Send + Sync,
    Arc<AppState>: FromRequestParts<S>,
{
    type Rejection = Response;

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        // This is a simplified extractor; in production, extract from the shared state
        Ok(OptionalApiKey(None))
    }
}
