use chrono::{DateTime, Utc};
use font_lab_domain::entities::{TaxonomyDimension, TaxonomyTerm};
use sqlx::SqlitePool;

fn parse_datetime(raw: &str) -> DateTime<Utc> {
    raw.parse::<DateTime<Utc>>().unwrap_or_default()
}

fn row_to_dimension(row: &sqlx::sqlite::SqliteRow) -> TaxonomyDimension {
    use sqlx::Row;
    TaxonomyDimension {
        id: row.get("id"),
        name: row.get("name"),
        label: row.get("label"),
        cardinality: row.get("cardinality"),
        filterable: row.get::<i32, _>("filterable") != 0,
        sortable: row.get::<i32, _>("sortable") != 0,
        required: row.get::<i32, _>("required") != 0,
    }
}

fn row_to_term(row: &sqlx::sqlite::SqliteRow) -> TaxonomyTerm {
    use sqlx::Row;
    TaxonomyTerm {
        id: row.get("id"),
        dimension_id: row.get("dimension_id"),
        value: row.get("value"),
        parent_id: row.get("parent_id"),
        sort_order: row.get("sort_order"),
        synonyms: serde_json::from_str(row.get::<&str, _>("synonyms")).unwrap_or_default(),
    }
}

pub async fn list_dimensions(pool: &SqlitePool) -> Result<Vec<TaxonomyDimension>, sqlx::Error> {
    let rows = sqlx::query("SELECT * FROM taxonomy_dimensions ORDER BY name")
        .fetch_all(pool)
        .await?;
    Ok(rows.iter().map(row_to_dimension).collect())
}

pub async fn get_dimension_by_name(
    pool: &SqlitePool,
    name: &str,
) -> Result<Option<TaxonomyDimension>, sqlx::Error> {
    let row = sqlx::query("SELECT * FROM taxonomy_dimensions WHERE name = ?")
        .bind(name)
        .fetch_optional(pool)
        .await?;
    Ok(row.as_ref().map(row_to_dimension))
}

pub async fn upsert_dimension(
    pool: &SqlitePool,
    name: &str,
    label: &str,
    cardinality: &str,
    filterable: bool,
    sortable: bool,
    required: bool,
) -> Result<i64, sqlx::Error> {
    let result = sqlx::query(
        r#"INSERT INTO taxonomy_dimensions (name, label, cardinality, filterable, sortable, required)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(name) DO UPDATE SET
             label = excluded.label,
             cardinality = excluded.cardinality,
             filterable = excluded.filterable,
             sortable = excluded.sortable,
             required = excluded.required"#,
    )
    .bind(name)
    .bind(label)
    .bind(cardinality)
    .bind(filterable as i32)
    .bind(sortable as i32)
    .bind(required as i32)
    .execute(pool)
    .await?;
    Ok(result.last_insert_rowid())
}

pub async fn list_terms(
    pool: &SqlitePool,
    dimension_id: i64,
) -> Result<Vec<TaxonomyTerm>, sqlx::Error> {
    let rows =
        sqlx::query("SELECT * FROM taxonomy_terms WHERE dimension_id = ? ORDER BY sort_order, value")
            .bind(dimension_id)
            .fetch_all(pool)
            .await?;
    Ok(rows.iter().map(row_to_term).collect())
}

pub async fn upsert_term(
    pool: &SqlitePool,
    dimension_id: i64,
    value: &str,
    sort_order: i32,
    synonyms: &[String],
    parent_id: Option<i64>,
) -> Result<i64, sqlx::Error> {
    let synonyms_json = serde_json::to_string(synonyms).unwrap_or_else(|_| "[]".into());
    let result = sqlx::query(
        r#"INSERT INTO taxonomy_terms (dimension_id, value, sort_order, synonyms, parent_id)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(dimension_id, value) DO UPDATE SET
             sort_order = excluded.sort_order,
             synonyms = excluded.synonyms,
             parent_id = excluded.parent_id"#,
    )
    .bind(dimension_id)
    .bind(value)
    .bind(sort_order)
    .bind(&synonyms_json)
    .bind(parent_id)
    .execute(pool)
    .await?;
    Ok(result.last_insert_rowid())
}

pub async fn assign_term(
    pool: &SqlitePool,
    sample_id: i64,
    term_id: i64,
) -> Result<(), sqlx::Error> {
    sqlx::query(
        r#"INSERT INTO font_sample_taxonomy (sample_id, term_id) VALUES (?, ?)
           ON CONFLICT(sample_id, term_id) DO NOTHING"#,
    )
    .bind(sample_id)
    .bind(term_id)
    .execute(pool)
    .await?;
    Ok(())
}

pub async fn remove_term(
    pool: &SqlitePool,
    sample_id: i64,
    term_id: i64,
) -> Result<(), sqlx::Error> {
    sqlx::query("DELETE FROM font_sample_taxonomy WHERE sample_id = ? AND term_id = ?")
        .bind(sample_id)
        .bind(term_id)
        .execute(pool)
        .await?;
    Ok(())
}

pub async fn facet_counts(
    pool: &SqlitePool,
    dimension_name: &str,
) -> Result<Vec<(String, i64)>, sqlx::Error> {
    use sqlx::Row;
    let rows = sqlx::query(
        r#"SELECT t.value, COUNT(fst.id) as cnt
           FROM taxonomy_terms t
           JOIN taxonomy_dimensions d ON d.id = t.dimension_id
           LEFT JOIN font_sample_taxonomy fst ON fst.term_id = t.id
           WHERE d.name = ?
           GROUP BY t.value
           ORDER BY cnt DESC"#,
    )
    .bind(dimension_name)
    .fetch_all(pool)
    .await?;

    Ok(rows
        .iter()
        .map(|r| (r.get::<String, _>("value"), r.get::<i64, _>("cnt")))
        .collect())
}
