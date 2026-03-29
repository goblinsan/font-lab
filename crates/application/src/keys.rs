use font_lab_db::repo::api_keys as key_repo;
use font_lab_domain::entities::ApiKey;
use font_lab_domain::errors::DomainError;
use sqlx::SqlitePool;

pub async fn create_key(
    pool: &SqlitePool,
    owner: &str,
    scope: &str,
    rate_limit: i32,
) -> Result<ApiKey, DomainError> {
    let key_value = ApiKey::generate_key();

    let id = key_repo::insert(pool, &key_value, owner, scope, rate_limit)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;

    key_repo::get_by_key(pool, &key_value)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?
        .ok_or(DomainError::Internal("failed to read back inserted key".into()))
}

pub async fn list_keys(pool: &SqlitePool) -> Result<Vec<ApiKey>, DomainError> {
    key_repo::list(pool)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))
}

pub async fn revoke_key(pool: &SqlitePool, id: i64) -> Result<(), DomainError> {
    let revoked = key_repo::revoke(pool, id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;

    if !revoked {
        return Err(DomainError::NotFound {
            entity: "ApiKey",
            id,
        });
    }
    Ok(())
}

pub async fn validate_key(pool: &SqlitePool, key: &str) -> Result<Option<ApiKey>, DomainError> {
    key_repo::get_by_key(pool, key)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))
}
