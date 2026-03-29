use sqlx::SqlitePool;

pub async fn insert(
    pool: &SqlitePool,
    sample_id: i64,
    job_id: Option<i64>,
    format: &str,
    filename: &str,
    file_size: Option<i64>,
    sha256: Option<&str>,
    source_package_id: Option<i64>,
) -> Result<i64, sqlx::Error> {
    let result = sqlx::query(
        r#"INSERT INTO font_builds (sample_id, job_id, format, filename, file_size, sha256, source_package_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)"#,
    )
    .bind(sample_id)
    .bind(job_id)
    .bind(format)
    .bind(filename)
    .bind(file_size)
    .bind(sha256)
    .bind(source_package_id)
    .execute(pool)
    .await?;
    Ok(result.last_insert_rowid())
}

pub async fn list_for_sample(
    pool: &SqlitePool,
    sample_id: i64,
) -> Result<Vec<(i64, String, String, Option<i64>, Option<String>)>, sqlx::Error> {
    use sqlx::Row;
    let rows = sqlx::query(
        "SELECT id, format, filename, file_size, sha256 FROM font_builds WHERE sample_id = ? ORDER BY created_at DESC",
    )
    .bind(sample_id)
    .fetch_all(pool)
    .await?;

    Ok(rows
        .iter()
        .map(|r| {
            (
                r.get("id"),
                r.get("format"),
                r.get("filename"),
                r.get("file_size"),
                r.get("sha256"),
            )
        })
        .collect())
}
