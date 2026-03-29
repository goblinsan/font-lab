use font_lab_blob_store::BlobStore;
use font_lab_db::repo::jobs as job_repo;
use font_lab_db::run_migrations;
use font_lab_domain::entities::{JobKind, JobStatus};
use sqlx::sqlite::SqlitePoolOptions;
use std::time::Duration;
use tracing_subscriber::EnvFilter;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .init();

    let database_url =
        std::env::var("DATABASE_URL").unwrap_or_else(|_| "sqlite:./font_lab.db?mode=rwc".into());
    let upload_dir = std::env::var("UPLOAD_DIR").unwrap_or_else(|_| "uploads".into());

    let pool = SqlitePoolOptions::new()
        .max_connections(2)
        .connect(&database_url)
        .await?;

    sqlx::query("PRAGMA journal_mode=WAL")
        .execute(&pool)
        .await?;
    sqlx::query("PRAGMA foreign_keys=ON")
        .execute(&pool)
        .await?;

    run_migrations(&pool).await?;

    let blobs = BlobStore::new(&upload_dir);
    blobs.init().await?;

    tracing::info!("font-lab worker started, polling for jobs...");

    loop {
        // Try each job kind in priority order
        for kind in &[
            JobKind::Segmentation,
            JobKind::Export,
            JobKind::Ocr,
            JobKind::Validation,
        ] {
            if let Some(job) = job_repo::claim_next(&pool, *kind).await? {
                tracing::info!(job_id = job.id, kind = %job.kind, "processing job");

                let result = match job.kind {
                    JobKind::Segmentation => process_segmentation(&pool, &blobs, &job).await,
                    JobKind::Export => process_export(&pool, &blobs, &job).await,
                    JobKind::Ocr => {
                        tracing::warn!("OCR not yet implemented");
                        Err("OCR not yet implemented".into())
                    }
                    JobKind::Validation => {
                        tracing::warn!("Validation not yet implemented");
                        Err("Validation not yet implemented".into())
                    }
                };

                match result {
                    Ok(()) => {
                        job_repo::complete(&pool, job.id, true, None).await?;
                        tracing::info!(job_id = job.id, "job succeeded");
                    }
                    Err(e) => {
                        let err_msg = e.to_string();
                        job_repo::complete(&pool, job.id, false, Some(&err_msg)).await?;
                        tracing::error!(job_id = job.id, error = %err_msg, "job failed");
                    }
                }
            }
        }

        tokio::time::sleep(Duration::from_secs(2)).await;
    }
}

async fn process_segmentation(
    pool: &sqlx::SqlitePool,
    blobs: &BlobStore,
    job: &font_lab_domain::entities::Job,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let sample_id = job
        .sample_id
        .ok_or("segmentation job requires sample_id")?;

    let sample = font_lab_db::repo::samples::get_by_id(pool, sample_id)
        .await?
        .ok_or("sample not found")?;

    font_lab_application::glyphs::segment_sample(pool, blobs, sample_id, &sample.filename).await?;

    Ok(())
}

async fn process_export(
    _pool: &sqlx::SqlitePool,
    _blobs: &BlobStore,
    _job: &font_lab_domain::entities::Job,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // Export implementation will use font_engine::export
    Err("Export not yet fully implemented".into())
}
