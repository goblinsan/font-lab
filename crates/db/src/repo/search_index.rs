use font_lab_domain::entities::FontSample;
use sqlx::SqlitePool;

pub async fn upsert(
    pool: &SqlitePool,
    sample: &FontSample,
    glyph_count: i32,
) -> Result<(), sqlx::Error> {
    let tags_json = serde_json::to_string(&sample.tags).unwrap_or_else(|_| "[]".into());
    let moods_json = serde_json::to_string(&sample.moods).unwrap_or_else(|_| "[]".into());
    let use_cases_json = serde_json::to_string(&sample.use_cases).unwrap_or_else(|_| "[]".into());
    let construction_json =
        serde_json::to_string(&sample.construction_traits).unwrap_or_else(|_| "[]".into());
    let visual_json =
        serde_json::to_string(&sample.visual_traits).unwrap_or_else(|_| "[]".into());

    // Build search text blob
    let search_parts: Vec<&str> = [
        sample.font_name.as_deref(),
        sample.font_category.as_deref(),
        sample.style.as_deref(),
        sample.genre.as_deref(),
        sample.theme.as_deref(),
        sample.era.as_deref(),
        sample.notes.as_deref(),
    ]
    .iter()
    .filter_map(|p| *p)
    .collect();
    let search_text = search_parts.join(" ");

    // Build feature vector
    let feature_vector = serde_json::json!({
        "style": sample.style,
        "genre": sample.genre,
        "theme": sample.theme,
        "font_category": sample.font_category,
        "era": sample.era,
        "tags": sample.tags,
        "moods": sample.moods,
        "visual_traits": sample.visual_traits,
    })
    .to_string();

    sqlx::query(
        r#"INSERT INTO font_search_index (
            sample_id, font_name, font_category, style, genre, era,
            origin_context, restoration_status, rights_status, review_status,
            confidence, completeness, glyph_count,
            tags, moods, use_cases, visual_traits, construction_traits,
            search_text, feature_vector
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sample_id) DO UPDATE SET
            font_name = excluded.font_name,
            font_category = excluded.font_category,
            style = excluded.style,
            genre = excluded.genre,
            era = excluded.era,
            origin_context = excluded.origin_context,
            restoration_status = excluded.restoration_status,
            rights_status = excluded.rights_status,
            review_status = excluded.review_status,
            confidence = excluded.confidence,
            completeness = excluded.completeness,
            glyph_count = excluded.glyph_count,
            tags = excluded.tags,
            moods = excluded.moods,
            use_cases = excluded.use_cases,
            visual_traits = excluded.visual_traits,
            construction_traits = excluded.construction_traits,
            search_text = excluded.search_text,
            feature_vector = excluded.feature_vector,
            indexed_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"#,
    )
    .bind(sample.id)
    .bind(&sample.font_name)
    .bind(&sample.font_category)
    .bind(&sample.style)
    .bind(&sample.genre)
    .bind(&sample.era)
    .bind(&sample.origin_context)
    .bind(&sample.restoration_status)
    .bind(&sample.rights_status)
    .bind(&sample.review_status)
    .bind(sample.confidence)
    .bind(sample.completeness)
    .bind(glyph_count)
    .bind(&tags_json)
    .bind(&moods_json)
    .bind(&use_cases_json)
    .bind(&visual_json)
    .bind(&construction_json)
    .bind(&search_text)
    .bind(&feature_vector)
    .execute(pool)
    .await?;

    Ok(())
}

pub async fn delete(pool: &SqlitePool, sample_id: i64) -> Result<(), sqlx::Error> {
    sqlx::query("DELETE FROM font_search_index WHERE sample_id = ?")
        .bind(sample_id)
        .execute(pool)
        .await?;
    Ok(())
}
