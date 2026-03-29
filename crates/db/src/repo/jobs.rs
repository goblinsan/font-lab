use chrono::{DateTime, Utc};
use font_lab_domain::entities::{Job, JobKind, JobStatus};
use sqlx::SqlitePool;

fn parse_datetime(raw: &str) -> DateTime<Utc> {
    raw.parse::<DateTime<Utc>>().unwrap_or_default()
}

fn row_to_job(row: &sqlx::sqlite::SqliteRow) -> Job {
    use sqlx::Row;
    let kind_str: &str = row.get("kind");
    let status_str: &str = row.get("status");

    Job {
        id: row.get("id"),
        kind: match kind_str {
            "segmentation" => JobKind::Segmentation,
            "ocr" => JobKind::Ocr,
            "export" => JobKind::Export,
            "validation" => JobKind::Validation,
            _ => JobKind::Segmentation,
        },
        status: match status_str {
            "queued" => JobStatus::Queued,
            "running" => JobStatus::Running,
            "succeeded" => JobStatus::Succeeded,
            "failed" => JobStatus::Failed,
            "canceled" => JobStatus::Canceled,
            _ => JobStatus::Queued,
        },
        sample_id: row.get("sample_id"),
        input_params: row.get("input_params"),
        engine_version: row.get("engine_version"),
        error_detail: row.get("error_detail"),
        started_at: row
            .get::<Option<&str>, _>("started_at")
            .map(|s| parse_datetime(s)),
        finished_at: row
            .get::<Option<&str>, _>("finished_at")
            .map(|s| parse_datetime(s)),
        created_at: parse_datetime(row.get::<&str, _>("created_at")),
    }
}

pub async fn create(
    pool: &SqlitePool,
    kind: JobKind,
    sample_id: Option<i64>,
    input_params: Option<&str>,
    engine_version: &str,
) -> Result<i64, sqlx::Error> {
    let result = sqlx::query(
        r#"INSERT INTO jobs (kind, status, sample_id, input_params, engine_version)
           VALUES (?, 'queued', ?, ?, ?)"#,
    )
    .bind(kind.to_string())
    .bind(sample_id)
    .bind(input_params)
    .bind(engine_version)
    .execute(pool)
    .await?;
    Ok(result.last_insert_rowid())
}

pub async fn get_by_id(pool: &SqlitePool, id: i64) -> Result<Option<Job>, sqlx::Error> {
    let row = sqlx::query("SELECT * FROM jobs WHERE id = ?")
        .bind(id)
        .fetch_optional(pool)
        .await?;
    Ok(row.as_ref().map(row_to_job))
}

pub async fn claim_next(pool: &SqlitePool, kind: JobKind) -> Result<Option<Job>, sqlx::Error> {
    let now = Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();
    let row = sqlx::query(
        r#"UPDATE jobs SET status = 'running', started_at = ?
           WHERE id = (
               SELECT id FROM jobs WHERE status = 'queued' AND kind = ?
               ORDER BY created_at ASC LIMIT 1
           )
           RETURNING *"#,
    )
    .bind(&now)
    .bind(kind.to_string())
    .fetch_optional(pool)
    .await?;
    Ok(row.as_ref().map(row_to_job))
}

pub async fn complete(
    pool: &SqlitePool,
    id: i64,
    success: bool,
    error_detail: Option<&str>,
) -> Result<(), sqlx::Error> {
    let now = Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();
    let status = if success { "succeeded" } else { "failed" };
    sqlx::query("UPDATE jobs SET status = ?, finished_at = ?, error_detail = ? WHERE id = ?")
        .bind(status)
        .bind(&now)
        .bind(error_detail)
        .bind(id)
        .execute(pool)
        .await?;
    Ok(())
}

pub async fn cancel(pool: &SqlitePool, id: i64) -> Result<bool, sqlx::Error> {
    let result =
        sqlx::query("UPDATE jobs SET status = 'canceled' WHERE id = ? AND status IN ('queued', 'running')")
            .bind(id)
            .execute(pool)
            .await?;
    Ok(result.rows_affected() > 0)
}
