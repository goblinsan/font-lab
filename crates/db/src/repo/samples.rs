use chrono::{DateTime, Utc};
use font_lab_domain::entities::FontSample;
use sqlx::SqlitePool;

fn parse_json_array(raw: &str) -> Vec<String> {
    serde_json::from_str(raw).unwrap_or_default()
}

fn parse_datetime(raw: &str) -> DateTime<Utc> {
    raw.parse::<DateTime<Utc>>().unwrap_or_default()
}

fn row_to_sample(row: &sqlx::sqlite::SqliteRow) -> FontSample {
    use sqlx::Row;
    FontSample {
        id: row.get("id"),
        filename: row.get("filename"),
        original_filename: row.get("original_filename"),
        slug: row.get("slug"),
        font_name: row.get("font_name"),
        font_category: row.get("font_category"),
        style: row.get("style"),
        genre: row.get("genre"),
        theme: row.get("theme"),
        era: row.get("era"),
        provenance: row.get("provenance"),
        confidence: row.get("confidence"),
        notes: row.get("notes"),
        source: row.get("source"),
        restoration_notes: row.get("restoration_notes"),
        tags: parse_json_array(row.get::<&str, _>("tags")),
        file_size: row.get("file_size"),
        content_type: row.get("content_type"),
        uploaded_at: parse_datetime(row.get::<&str, _>("uploaded_at")),
        origin_context: row.get("origin_context"),
        source_type: row.get("source_type"),
        restoration_status: row.get("restoration_status"),
        rights_status: row.get("rights_status"),
        rights_notes: row.get("rights_notes"),
        completeness: row.get("completeness"),
        moods: parse_json_array(row.get::<&str, _>("moods")),
        use_cases: parse_json_array(row.get::<&str, _>("use_cases")),
        construction_traits: parse_json_array(row.get::<&str, _>("construction_traits")),
        visual_traits: parse_json_array(row.get::<&str, _>("visual_traits")),
        review_status: row.get("review_status"),
        is_archived: row.get::<i32, _>("is_archived") != 0,
        archived_at: row
            .get::<Option<&str>, _>("archived_at")
            .map(|s| parse_datetime(s)),
    }
}

pub async fn get_by_id(pool: &SqlitePool, id: i64) -> Result<Option<FontSample>, sqlx::Error> {
    let row = sqlx::query("SELECT * FROM font_samples WHERE id = ?")
        .bind(id)
        .fetch_optional(pool)
        .await?;
    Ok(row.as_ref().map(row_to_sample))
}

pub async fn get_by_slug(
    pool: &SqlitePool,
    slug: &str,
) -> Result<Option<FontSample>, sqlx::Error> {
    let row = sqlx::query("SELECT * FROM font_samples WHERE slug = ?")
        .bind(slug)
        .fetch_optional(pool)
        .await?;
    Ok(row.as_ref().map(row_to_sample))
}

#[derive(Default)]
pub struct ListFilters {
    pub font_name: Option<String>,
    pub font_category: Option<String>,
    pub style: Option<String>,
    pub genre: Option<String>,
    pub theme: Option<String>,
    pub era: Option<String>,
    pub origin_context: Option<String>,
    pub source_type: Option<String>,
    pub restoration_status: Option<String>,
    pub rights_status: Option<String>,
    pub tag: Option<String>,
    pub include_archived: bool,
    pub offset: i64,
    pub limit: i64,
}

pub async fn list(pool: &SqlitePool, filters: &ListFilters) -> Result<Vec<FontSample>, sqlx::Error> {
    // Build dynamic query
    let mut sql = String::from("SELECT * FROM font_samples WHERE 1=1");
    let mut args: Vec<String> = Vec::new();

    if !filters.include_archived {
        sql.push_str(" AND is_archived = 0");
    }

    macro_rules! add_filter {
        ($field:ident) => {
            if let Some(ref val) = filters.$field {
                sql.push_str(concat!(" AND ", stringify!($field), " LIKE '%' || ? || '%'"));
                args.push(val.clone());
            }
        };
    }

    add_filter!(font_name);
    add_filter!(font_category);
    add_filter!(style);
    add_filter!(genre);
    add_filter!(theme);
    add_filter!(era);
    add_filter!(origin_context);
    add_filter!(source_type);
    add_filter!(restoration_status);
    add_filter!(rights_status);

    if let Some(ref tag) = filters.tag {
        sql.push_str(" AND tags LIKE '%' || ? || '%'");
        args.push(tag.clone());
    }

    sql.push_str(" ORDER BY uploaded_at DESC LIMIT ? OFFSET ?");

    let mut query = sqlx::query(&sql);
    for arg in &args {
        query = query.bind(arg);
    }
    query = query.bind(filters.limit).bind(filters.offset);

    let rows = query.fetch_all(pool).await?;
    Ok(rows.iter().map(row_to_sample).collect())
}

pub async fn count(pool: &SqlitePool, include_archived: bool) -> Result<i64, sqlx::Error> {
    let sql = if include_archived {
        "SELECT COUNT(*) as cnt FROM font_samples"
    } else {
        "SELECT COUNT(*) as cnt FROM font_samples WHERE is_archived = 0"
    };
    let row: (i64,) = sqlx::query_as(sql).fetch_one(pool).await?;
    Ok(row.0)
}

pub async fn insert(
    pool: &SqlitePool,
    filename: &str,
    original_filename: &str,
    slug: Option<&str>,
    font_name: Option<&str>,
    font_category: Option<&str>,
    style: Option<&str>,
    genre: Option<&str>,
    theme: Option<&str>,
    era: Option<&str>,
    provenance: Option<&str>,
    confidence: Option<f64>,
    notes: Option<&str>,
    source: Option<&str>,
    restoration_notes: Option<&str>,
    tags: &[String],
    file_size: Option<i64>,
    content_type: Option<&str>,
    origin_context: Option<&str>,
    source_type: Option<&str>,
    restoration_status: Option<&str>,
    rights_status: Option<&str>,
    rights_notes: Option<&str>,
    completeness: Option<f64>,
    moods: &[String],
    use_cases: &[String],
    construction_traits: &[String],
    visual_traits: &[String],
) -> Result<i64, sqlx::Error> {
    let tags_json = serde_json::to_string(tags).unwrap_or_else(|_| "[]".into());
    let moods_json = serde_json::to_string(moods).unwrap_or_else(|_| "[]".into());
    let use_cases_json = serde_json::to_string(use_cases).unwrap_or_else(|_| "[]".into());
    let construction_json =
        serde_json::to_string(construction_traits).unwrap_or_else(|_| "[]".into());
    let visual_json = serde_json::to_string(visual_traits).unwrap_or_else(|_| "[]".into());

    let result = sqlx::query(
        r#"INSERT INTO font_samples (
            filename, original_filename, slug, font_name, font_category, style, genre,
            theme, era, provenance, confidence, notes, source, restoration_notes,
            tags, file_size, content_type,
            origin_context, source_type, restoration_status, rights_status, rights_notes,
            completeness, moods, use_cases, construction_traits, visual_traits
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )"#,
    )
    .bind(filename)
    .bind(original_filename)
    .bind(slug)
    .bind(font_name)
    .bind(font_category)
    .bind(style)
    .bind(genre)
    .bind(theme)
    .bind(era)
    .bind(provenance)
    .bind(confidence)
    .bind(notes)
    .bind(source)
    .bind(restoration_notes)
    .bind(&tags_json)
    .bind(file_size)
    .bind(content_type)
    .bind(origin_context)
    .bind(source_type)
    .bind(restoration_status)
    .bind(rights_status)
    .bind(rights_notes)
    .bind(completeness)
    .bind(&moods_json)
    .bind(&use_cases_json)
    .bind(&construction_json)
    .bind(&visual_json)
    .execute(pool)
    .await?;

    Ok(result.last_insert_rowid())
}

pub async fn update(
    pool: &SqlitePool,
    id: i64,
    update: &font_lab_domain::entities::UpdateSample,
) -> Result<bool, sqlx::Error> {
    let mut sets = Vec::new();
    let mut args: Vec<String> = Vec::new();

    macro_rules! set_field {
        ($field:ident) => {
            if let Some(ref val) = update.$field {
                sets.push(concat!(stringify!($field), " = ?").to_string());
                args.push(val.clone());
            }
        };
    }

    set_field!(font_name);
    set_field!(font_category);
    set_field!(style);
    set_field!(genre);
    set_field!(theme);
    set_field!(era);
    set_field!(provenance);
    set_field!(notes);
    set_field!(source);
    set_field!(restoration_notes);
    set_field!(origin_context);
    set_field!(source_type);
    set_field!(restoration_status);
    set_field!(rights_status);
    set_field!(rights_notes);
    set_field!(review_status);

    if let Some(c) = update.confidence {
        sets.push("confidence = ?".into());
        args.push(c.to_string());
    }
    if let Some(c) = update.completeness {
        sets.push("completeness = ?".into());
        args.push(c.to_string());
    }

    macro_rules! set_json_field {
        ($field:ident) => {
            if let Some(ref val) = update.$field {
                sets.push(concat!(stringify!($field), " = ?").to_string());
                args.push(serde_json::to_string(val).unwrap_or_else(|_| "[]".into()));
            }
        };
    }

    set_json_field!(tags);
    set_json_field!(moods);
    set_json_field!(use_cases);
    set_json_field!(construction_traits);
    set_json_field!(visual_traits);

    if sets.is_empty() {
        return Ok(false);
    }

    // Update slug if font_name changed
    if let Some(ref name) = update.font_name {
        let slug = font_lab_domain::slug::make_slug(name);
        sets.push("slug = ?".into());
        args.push(slug);
    }

    let sql = format!("UPDATE font_samples SET {} WHERE id = ?", sets.join(", "));
    let mut query = sqlx::query(&sql);
    for arg in &args {
        query = query.bind(arg);
    }
    query = query.bind(id);

    let result = query.execute(pool).await?;
    Ok(result.rows_affected() > 0)
}

pub async fn archive(pool: &SqlitePool, id: i64) -> Result<bool, sqlx::Error> {
    let now = Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();
    let result = sqlx::query(
        "UPDATE font_samples SET is_archived = 1, archived_at = ? WHERE id = ? AND is_archived = 0",
    )
    .bind(&now)
    .bind(id)
    .execute(pool)
    .await?;
    Ok(result.rows_affected() > 0)
}

pub async fn delete(pool: &SqlitePool, id: i64) -> Result<bool, sqlx::Error> {
    let result = sqlx::query("DELETE FROM font_samples WHERE id = ?")
        .bind(id)
        .execute(pool)
        .await?;
    Ok(result.rows_affected() > 0)
}
