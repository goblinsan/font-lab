use chrono::{DateTime, Utc};
use font_lab_domain::entities::Glyph;
use sqlx::SqlitePool;

fn parse_datetime(raw: &str) -> DateTime<Utc> {
    raw.parse::<DateTime<Utc>>().unwrap_or_default()
}

fn row_to_glyph(row: &sqlx::sqlite::SqliteRow) -> Glyph {
    use sqlx::Row;
    Glyph {
        id: row.get("id"),
        sample_id: row.get("sample_id"),
        filename: row.get("filename"),
        bbox_x: row.get("bbox_x"),
        bbox_y: row.get("bbox_y"),
        bbox_w: row.get("bbox_w"),
        bbox_h: row.get("bbox_h"),
        label: row.get("label"),
        advance_width: row.get("advance_width"),
        left_bearing: row.get("left_bearing"),
        verified: row.get::<i32, _>("verified") != 0,
        synthesized: row.get::<i32, _>("synthesized") != 0,
        created_at: parse_datetime(row.get::<&str, _>("created_at")),
    }
}

pub async fn list_for_sample(
    pool: &SqlitePool,
    sample_id: i64,
) -> Result<Vec<Glyph>, sqlx::Error> {
    let rows = sqlx::query(
        "SELECT * FROM glyphs WHERE sample_id = ? ORDER BY bbox_y, bbox_x",
    )
    .bind(sample_id)
    .fetch_all(pool)
    .await?;
    Ok(rows.iter().map(row_to_glyph).collect())
}

pub async fn get_by_id(pool: &SqlitePool, id: i64) -> Result<Option<Glyph>, sqlx::Error> {
    let row = sqlx::query("SELECT * FROM glyphs WHERE id = ?")
        .bind(id)
        .fetch_optional(pool)
        .await?;
    Ok(row.as_ref().map(row_to_glyph))
}

pub async fn insert(
    pool: &SqlitePool,
    sample_id: i64,
    filename: &str,
    bbox_x: i32,
    bbox_y: i32,
    bbox_w: i32,
    bbox_h: i32,
    label: Option<&str>,
    synthesized: bool,
) -> Result<i64, sqlx::Error> {
    let result = sqlx::query(
        r#"INSERT INTO glyphs (sample_id, filename, bbox_x, bbox_y, bbox_w, bbox_h, label, synthesized)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)"#,
    )
    .bind(sample_id)
    .bind(filename)
    .bind(bbox_x)
    .bind(bbox_y)
    .bind(bbox_w)
    .bind(bbox_h)
    .bind(label)
    .bind(synthesized as i32)
    .execute(pool)
    .await?;
    Ok(result.last_insert_rowid())
}

pub async fn update(
    pool: &SqlitePool,
    id: i64,
    update: &font_lab_domain::entities::UpdateGlyph,
) -> Result<bool, sqlx::Error> {
    let mut sets = Vec::new();

    macro_rules! set_i32 {
        ($field:ident) => {
            if let Some(val) = update.$field {
                sets.push((concat!(stringify!($field), " = ?").to_string(), val.to_string()));
            }
        };
    }

    if let Some(ref label) = update.label {
        sets.push(("label = ?".to_string(), label.clone()));
    }
    set_i32!(bbox_x);
    set_i32!(bbox_y);
    set_i32!(bbox_w);
    set_i32!(bbox_h);
    set_i32!(advance_width);
    set_i32!(left_bearing);
    if let Some(verified) = update.verified {
        sets.push(("verified = ?".to_string(), (verified as i32).to_string()));
    }

    if sets.is_empty() {
        return Ok(false);
    }

    let set_clause: Vec<&str> = sets.iter().map(|(s, _)| s.as_str()).collect();
    let sql = format!("UPDATE glyphs SET {} WHERE id = ?", set_clause.join(", "));
    let mut query = sqlx::query(&sql);
    for (_, val) in &sets {
        query = query.bind(val);
    }
    query = query.bind(id);

    let result = query.execute(pool).await?;
    Ok(result.rows_affected() > 0)
}

pub async fn delete(pool: &SqlitePool, id: i64) -> Result<bool, sqlx::Error> {
    let result = sqlx::query("DELETE FROM glyphs WHERE id = ?")
        .bind(id)
        .execute(pool)
        .await?;
    Ok(result.rows_affected() > 0)
}

pub async fn delete_for_sample(pool: &SqlitePool, sample_id: i64) -> Result<u64, sqlx::Error> {
    let result = sqlx::query("DELETE FROM glyphs WHERE sample_id = ?")
        .bind(sample_id)
        .execute(pool)
        .await?;
    Ok(result.rows_affected())
}
