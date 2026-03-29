use font_lab_blob_store::BlobStore;
use font_lab_db::repo::{samples as sample_repo, search_index};
use font_lab_domain::entities::{CreateSample, FontSample, UpdateSample};
use font_lab_domain::errors::{validate_completeness, validate_confidence, validate_content_type, DomainError};
use font_lab_domain::slug::make_slug;
use sqlx::SqlitePool;
use uuid::Uuid;

/// Upload a new font sample image with metadata.
pub async fn upload_sample(
    pool: &SqlitePool,
    blobs: &BlobStore,
    data: &[u8],
    input: &CreateSample,
) -> Result<FontSample, DomainError> {
    // Validate
    if let Some(ref ct) = input.content_type {
        validate_content_type(ct)?;
    }
    if let Some(c) = input.confidence {
        validate_confidence(c)?;
    }
    if let Some(c) = input.completeness {
        validate_completeness(c)?;
    }

    // Determine extension from content type
    let ext = match input.content_type.as_deref() {
        Some("image/jpeg") => "jpg",
        Some("image/png") => "png",
        Some("image/gif") => "gif",
        Some("image/webp") => "webp",
        Some("image/tiff") => "tiff",
        _ => "png",
    };

    // Store blob
    let filename = blobs
        .put("samples", ext, data)
        .await
        .map_err(|e| DomainError::Storage(e.to_string()))?;

    // Generate slug
    let slug = input.font_name.as_ref().map(|n| make_slug(n));

    let id = sample_repo::insert(
        pool,
        &filename,
        &input.original_filename,
        slug.as_deref(),
        input.font_name.as_deref(),
        input.font_category.as_deref(),
        input.style.as_deref(),
        input.genre.as_deref(),
        input.theme.as_deref(),
        input.era.as_deref(),
        input.provenance.as_deref(),
        input.confidence,
        input.notes.as_deref(),
        input.source.as_deref(),
        input.restoration_notes.as_deref(),
        &input.tags,
        Some(data.len() as i64),
        input.content_type.as_deref(),
        input.origin_context.as_deref(),
        input.source_type.as_deref(),
        input.restoration_status.as_deref(),
        input.rights_status.as_deref(),
        input.rights_notes.as_deref(),
        input.completeness,
        &input.moods,
        &input.use_cases,
        &input.construction_traits,
        &input.visual_traits,
    )
    .await
    .map_err(|e| DomainError::Internal(e.to_string()))?;

    let sample = sample_repo::get_by_id(pool, id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?
        .ok_or(DomainError::Internal("failed to read back inserted sample".into()))?;

    // Update search index
    let _ = search_index::upsert(pool, &sample, 0).await;

    Ok(sample)
}

/// Update sample metadata.
pub async fn update_sample(
    pool: &SqlitePool,
    id: i64,
    update: &UpdateSample,
) -> Result<FontSample, DomainError> {
    if let Some(c) = update.confidence {
        validate_confidence(c)?;
    }
    if let Some(c) = update.completeness {
        validate_completeness(c)?;
    }

    sample_repo::update(pool, id, update)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;

    let sample = sample_repo::get_by_id(pool, id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?
        .ok_or(DomainError::NotFound {
            entity: "FontSample",
            id,
        })?;

    // Update search index
    let _ = search_index::upsert(pool, &sample, 0).await;

    Ok(sample)
}

/// Delete a sample and its associated blob.
pub async fn delete_sample(
    pool: &SqlitePool,
    blobs: &BlobStore,
    id: i64,
) -> Result<(), DomainError> {
    let sample = sample_repo::get_by_id(pool, id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?
        .ok_or(DomainError::NotFound {
            entity: "FontSample",
            id,
        })?;

    // Delete blob
    let _ = blobs.delete("samples", &sample.filename).await;

    // Delete search index
    let _ = search_index::delete(pool, id).await;

    // Delete DB record (cascades to glyphs, etc.)
    sample_repo::delete(pool, id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?;

    Ok(())
}

/// Get a sample by ID.
pub async fn get_sample(pool: &SqlitePool, id: i64) -> Result<FontSample, DomainError> {
    sample_repo::get_by_id(pool, id)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))?
        .ok_or(DomainError::NotFound {
            entity: "FontSample",
            id,
        })
}

/// List samples with filters.
pub async fn list_samples(
    pool: &SqlitePool,
    filters: &sample_repo::ListFilters,
) -> Result<Vec<FontSample>, DomainError> {
    sample_repo::list(pool, filters)
        .await
        .map_err(|e| DomainError::Internal(e.to_string()))
}
