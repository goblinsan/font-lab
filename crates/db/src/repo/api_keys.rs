use chrono::{DateTime, Utc};
use font_lab_domain::entities::ApiKey;
use sqlx::SqlitePool;

fn parse_datetime(raw: &str) -> DateTime<Utc> {
    raw.parse::<DateTime<Utc>>().unwrap_or_default()
}

fn row_to_api_key(row: &sqlx::sqlite::SqliteRow) -> ApiKey {
    use sqlx::Row;
    ApiKey {
        id: row.get("id"),
        key: row.get("key"),
        owner: row.get("owner"),
        scope: row.get("scope"),
        is_active: row.get::<i32, _>("is_active") != 0,
        rate_limit: row.get("rate_limit"),
        created_at: parse_datetime(row.get::<&str, _>("created_at")),
    }
}

pub async fn get_by_key(pool: &SqlitePool, key: &str) -> Result<Option<ApiKey>, sqlx::Error> {
    let row = sqlx::query("SELECT * FROM api_keys WHERE key = ? AND is_active = 1")
        .bind(key)
        .fetch_optional(pool)
        .await?;
    Ok(row.as_ref().map(row_to_api_key))
}

pub async fn list(pool: &SqlitePool) -> Result<Vec<ApiKey>, sqlx::Error> {
    let rows = sqlx::query("SELECT * FROM api_keys ORDER BY created_at DESC")
        .fetch_all(pool)
        .await?;
    Ok(rows.iter().map(row_to_api_key).collect())
}

pub async fn insert(
    pool: &SqlitePool,
    key: &str,
    owner: &str,
    scope: &str,
    rate_limit: i32,
) -> Result<i64, sqlx::Error> {
    let result = sqlx::query(
        "INSERT INTO api_keys (key, owner, scope, rate_limit) VALUES (?, ?, ?, ?)",
    )
    .bind(key)
    .bind(owner)
    .bind(scope)
    .bind(rate_limit)
    .execute(pool)
    .await?;
    Ok(result.last_insert_rowid())
}

pub async fn revoke(pool: &SqlitePool, id: i64) -> Result<bool, sqlx::Error> {
    let result = sqlx::query("UPDATE api_keys SET is_active = 0 WHERE id = ?")
        .bind(id)
        .execute(pool)
        .await?;
    Ok(result.rows_affected() > 0)
}
