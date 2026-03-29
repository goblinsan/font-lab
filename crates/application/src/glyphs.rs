use font_lab_blob_store::BlobStore;
use font_lab_db::repo::glyphs as glyph_repo;
use font_lab_domain::entities::{Glyph, UpdateGlyph};
use font_lab_domain::errors::DomainError;
use font_lab_segmentation::{segment_image, SegmentParams};
use sqlx::SqlitePool;
use std::path::PathBuf;

/// Run segmentation on a sample image, replacing any existing glyphs.
pub async fn segment_sample(
    pool: &SqlitePool,
    blobs: &BlobStore,
    sample_id: i64,
    sample_filename: &str,
) -> Result<Vec<Glyph>, DomainError> {
    // Delete existing glyphs
    let existing = glyph_repo::list_for_sample(pool, sample_id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;

    for g in &existing {
        let _ = blobs.delete("glyphs", &g.filename).await;
    }
    glyph_repo::delete_for_sample(pool, sample_id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;

    // Run segmentation
    let image_path = blobs.path("samples", sample_filename);
    let output_dir = PathBuf::from(blobs.base_dir()).join("glyphs");

    let glyph_infos = tokio::task::spawn_blocking(move || {
        segment_image(&image_path, &output_dir, &SegmentParams::default())
    })
    .await
    .map_err(|e| DomainError::Processing(e.to_string()))?
    .map_err(|e| DomainError::Processing(e.to_string()))?;

    // Insert glyph records
    let mut glyphs = Vec::new();
    for info in &glyph_infos {
        let glyph_id = glyph_repo::insert(
            pool,
            sample_id,
            &info.filename,
            info.bbox_x as i32,
            info.bbox_y as i32,
            info.bbox_w as i32,
            info.bbox_h as i32,
            None, // label assigned later
            false,
        )
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;

        if let Some(glyph) = glyph_repo::get_by_id(pool, glyph_id)
            .await
            .map_err(|e| DomainError::Internal(e.to_string()))?
        {
            glyphs.push(glyph);
        }
    }

    Ok(glyphs)
}

/// Get glyphs for a sample.
pub async fn list_glyphs(
    pool: &SqlitePool,
    sample_id: i64,
) -> Result<Vec<Glyph>, DomainError> {
    glyph_repo::list_for_sample(pool, sample_id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))
}

/// Get a single glyph by ID.
pub async fn get_glyph(pool: &SqlitePool, id: i64) -> Result<Glyph, DomainError> {
    glyph_repo::get_by_id(pool, id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?
        .ok_or(DomainError::NotFound {
            entity: "Glyph",
            id,
        })
}

/// Update a glyph.
pub async fn update_glyph(
    pool: &SqlitePool,
    id: i64,
    update: &UpdateGlyph,
) -> Result<Glyph, DomainError> {
    glyph_repo::update(pool, id, update)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;

    get_glyph(pool, id).await
}

/// Delete a glyph and its crop file.
pub async fn delete_glyph(
    pool: &SqlitePool,
    blobs: &BlobStore,
    id: i64,
) -> Result<(), DomainError> {
    let glyph = get_glyph(pool, id).await?;
    let _ = blobs.delete("glyphs", &glyph.filename).await;
    glyph_repo::delete(pool, id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;
    Ok(())
}
