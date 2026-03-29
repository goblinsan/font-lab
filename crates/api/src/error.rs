use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;
use font_lab_domain::errors::DomainError;
use serde_json::json;

pub struct AppError(pub DomainError);

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match &self.0 {
            DomainError::NotFound { .. } | DomainError::NotFoundBySlug { .. } => {
                (StatusCode::NOT_FOUND, self.0.to_string())
            }
            DomainError::Duplicate(_) => (StatusCode::CONFLICT, self.0.to_string()),
            DomainError::Validation(_) | DomainError::InvalidFileType(_) => {
                (StatusCode::BAD_REQUEST, self.0.to_string())
            }
            DomainError::Unauthorized => (StatusCode::UNAUTHORIZED, self.0.to_string()),
            DomainError::Forbidden(_) => (StatusCode::FORBIDDEN, self.0.to_string()),
            DomainError::RateLimited => {
                (StatusCode::TOO_MANY_REQUESTS, self.0.to_string())
            }
            DomainError::Processing(_) => {
                (StatusCode::UNPROCESSABLE_ENTITY, self.0.to_string())
            }
            _ => (StatusCode::INTERNAL_SERVER_ERROR, "internal error".into()),
        };

        (status, Json(json!({ "error": message }))).into_response()
    }
}

impl From<DomainError> for AppError {
    fn from(err: DomainError) -> Self {
        Self(err)
    }
}
