use font_lab_blob_store::BlobStore;
use sqlx::SqlitePool;

pub struct AppState {
    pub pool: SqlitePool,
    pub blobs: BlobStore,
}
