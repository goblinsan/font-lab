mod routes;
mod auth;
mod state;
mod error;

use font_lab_blob_store::BlobStore;
use font_lab_db::run_migrations;
use sqlx::sqlite::SqlitePoolOptions;
use std::sync::Arc;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use tracing_subscriber::EnvFilter;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .init();

    let database_url =
        std::env::var("DATABASE_URL").unwrap_or_else(|_| "sqlite:./font_lab.db?mode=rwc".into());
    let upload_dir = std::env::var("UPLOAD_DIR").unwrap_or_else(|_| "uploads".into());
    let bind_addr = std::env::var("BIND_ADDR").unwrap_or_else(|_| "0.0.0.0:8000".into());

    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await?;

    // Enable WAL mode for better concurrency
    sqlx::query("PRAGMA journal_mode=WAL")
        .execute(&pool)
        .await?;
    sqlx::query("PRAGMA foreign_keys=ON")
        .execute(&pool)
        .await?;

    run_migrations(&pool).await?;

    let blobs = BlobStore::new(&upload_dir);
    blobs.init().await?;

    let state = Arc::new(state::AppState { pool, blobs });

    let app = routes::router(state)
        .layer(TraceLayer::new_for_http())
        .layer(CorsLayer::permissive());

    let listener = tokio::net::TcpListener::bind(&bind_addr).await?;
    tracing::info!("font-lab API listening on {bind_addr}");
    axum::serve(listener, app).await?;

    Ok(())
}
