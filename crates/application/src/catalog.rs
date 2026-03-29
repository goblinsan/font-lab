use font_lab_db::repo::samples as sample_repo;
use font_lab_db::repo::glyphs as glyph_repo;
use font_lab_domain::entities::FontSample;
use font_lab_domain::errors::DomainError;
use font_lab_domain::similarity::similarity_score;
use sqlx::SqlitePool;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct CatalogEntry {
    pub id: i64,
    pub font_name: Option<String>,
    pub font_category: Option<String>,
    pub style: Option<String>,
    pub genre: Option<String>,
    pub theme: Option<String>,
    pub era: Option<String>,
    pub tags: Vec<String>,
    pub preview_url: String,
    pub glyph_count: i64,
    pub confidence: Option<f64>,
    pub review_status: Option<String>,
}

pub async fn list_catalog(pool: &SqlitePool) -> Result<Vec<CatalogEntry>, DomainError> {
    let filters = sample_repo::ListFilters {
        limit: 1000,
        ..Default::default()
    };
    let samples = sample_repo::list(pool, &filters)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;

    let mut entries = Vec::new();
    for s in samples {
        let glyph_count = glyph_repo::list_for_sample(pool, s.id)
            .await
            .map(|g| g.len() as i64)
            .unwrap_or(0);

        entries.push(CatalogEntry {
            id: s.id,
            preview_url: format!("/uploads/samples/{}", s.filename),
            glyph_count,
            font_name: s.font_name,
            font_category: s.font_category,
            style: s.style,
            genre: s.genre,
            theme: s.theme,
            era: s.era,
            tags: s.tags,
            confidence: s.confidence,
            review_status: s.review_status,
        });
    }
    Ok(entries)
}

#[derive(Debug, Serialize)]
pub struct SimilarEntry {
    pub id: i64,
    pub font_name: Option<String>,
    pub score: f64,
    pub preview_url: String,
}

pub async fn find_similar(
    pool: &SqlitePool,
    sample_id: i64,
    limit: usize,
    min_score: f64,
) -> Result<Vec<SimilarEntry>, DomainError> {
    let target = sample_repo::get_by_id(pool, sample_id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?
        .ok_or(DomainError::NotFound {
            entity: "FontSample",
            id: sample_id,
        })?;

    let filters = sample_repo::ListFilters {
        limit: 10000,
        ..Default::default()
    };
    let all = sample_repo::list(pool, &filters)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;

    let mut scored: Vec<SimilarEntry> = all
        .iter()
        .filter(|s| s.id != sample_id)
        .filter_map(|s| {
            let score = similarity_score(&target, s);
            if score >= min_score {
                Some(SimilarEntry {
                    id: s.id,
                    font_name: s.font_name.clone(),
                    score,
                    preview_url: format!("/uploads/samples/{}", s.filename),
                })
            } else {
                None
            }
        })
        .collect();

    scored.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
    scored.truncate(limit);

    Ok(scored)
}
