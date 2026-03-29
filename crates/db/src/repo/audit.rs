use sqlx::SqlitePool;

pub async fn log(
    pool: &SqlitePool,
    sample_id: Option<i64>,
    actor: Option<&str>,
    action: &str,
    entity_type: Option<&str>,
    entity_id: Option<i64>,
    field_name: Option<&str>,
    old_value: Option<&serde_json::Value>,
    new_value: Option<&serde_json::Value>,
) -> Result<i64, sqlx::Error> {
    let old_str = old_value.map(|v| v.to_string());
    let new_str = new_value.map(|v| v.to_string());

    let result = sqlx::query(
        r#"INSERT INTO curation_audit_log
           (sample_id, actor, action, entity_type, entity_id, field_name, old_value, new_value)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)"#,
    )
    .bind(sample_id)
    .bind(actor)
    .bind(action)
    .bind(entity_type)
    .bind(entity_id)
    .bind(field_name)
    .bind(old_str.as_deref())
    .bind(new_str.as_deref())
    .execute(pool)
    .await?;

    Ok(result.last_insert_rowid())
}

pub async fn list_for_sample(
    pool: &SqlitePool,
    sample_id: i64,
) -> Result<Vec<serde_json::Value>, sqlx::Error> {
    use sqlx::Row;
    let rows = sqlx::query(
        "SELECT * FROM curation_audit_log WHERE sample_id = ? ORDER BY created_at DESC",
    )
    .bind(sample_id)
    .fetch_all(pool)
    .await?;

    Ok(rows
        .iter()
        .map(|r| {
            serde_json::json!({
                "id": r.get::<i64, _>("id"),
                "sample_id": r.get::<Option<i64>, _>("sample_id"),
                "actor": r.get::<Option<String>, _>("actor"),
                "action": r.get::<String, _>("action"),
                "entity_type": r.get::<Option<String>, _>("entity_type"),
                "field_name": r.get::<Option<String>, _>("field_name"),
                "old_value": r.get::<Option<String>, _>("old_value"),
                "new_value": r.get::<Option<String>, _>("new_value"),
                "created_at": r.get::<String, _>("created_at"),
            })
        })
        .collect())
}
