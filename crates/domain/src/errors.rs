use thiserror::Error;

#[derive(Debug, Error)]
pub enum DomainError {
    #[error("entity not found: {entity} with id {id}")]
    NotFound { entity: &'static str, id: i64 },

    #[error("entity not found: {entity} with slug {slug}")]
    NotFoundBySlug { entity: &'static str, slug: String },

    #[error("duplicate: {0}")]
    Duplicate(String),

    #[error("validation error: {0}")]
    Validation(String),

    #[error("invalid file type: {0}")]
    InvalidFileType(String),

    #[error("unauthorized")]
    Unauthorized,

    #[error("forbidden: {0}")]
    Forbidden(String),

    #[error("rate limit exceeded")]
    RateLimited,

    #[error("invalid state transition: {0}")]
    InvalidStateTransition(String),

    #[error("processing error: {0}")]
    Processing(String),

    #[error("storage error: {0}")]
    Storage(String),

    #[error("internal error: {0}")]
    Internal(String),
}

pub const ALLOWED_CONTENT_TYPES: &[&str] = &[
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/tiff",
];

pub fn validate_content_type(content_type: &str) -> Result<(), DomainError> {
    if ALLOWED_CONTENT_TYPES.contains(&content_type) {
        Ok(())
    } else {
        Err(DomainError::InvalidFileType(format!(
            "'{content_type}' is not allowed. Accepted: {}",
            ALLOWED_CONTENT_TYPES.join(", ")
        )))
    }
}

pub fn validate_confidence(value: f64) -> Result<(), DomainError> {
    if !(0.0..=1.0).contains(&value) {
        return Err(DomainError::Validation(
            "confidence must be between 0.0 and 1.0".into(),
        ));
    }
    Ok(())
}

pub fn validate_completeness(value: f64) -> Result<(), DomainError> {
    if !(0.0..=1.0).contains(&value) {
        return Err(DomainError::Validation(
            "completeness must be between 0.0 and 1.0".into(),
        ));
    }
    Ok(())
}
