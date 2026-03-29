use std::path::{Path, PathBuf};
use thiserror::Error;
use uuid::Uuid;

#[derive(Debug, Error)]
pub enum BlobError {
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    #[error("blob not found: {0}")]
    NotFound(String),
}

/// Abstraction over binary asset storage.
/// Starts with local filesystem; interface is compatible with S3-style storage.
pub struct BlobStore {
    base_dir: PathBuf,
}

impl BlobStore {
    pub fn new(base_dir: impl AsRef<Path>) -> Self {
        Self {
            base_dir: base_dir.as_ref().to_path_buf(),
        }
    }

    /// Ensure all required subdirectories exist.
    pub async fn init(&self) -> Result<(), BlobError> {
        for sub in &["samples", "glyphs", "exports", "sources", "previews"] {
            tokio::fs::create_dir_all(self.base_dir.join(sub)).await?;
        }
        Ok(())
    }

    /// Store bytes under a given category, returning the generated filename.
    pub async fn put(
        &self,
        category: &str,
        extension: &str,
        data: &[u8],
    ) -> Result<String, BlobError> {
        let filename = format!("{}.{}", Uuid::new_v4(), extension);
        let path = self.base_dir.join(category).join(&filename);
        tokio::fs::write(&path, data).await?;
        Ok(filename)
    }

    /// Store bytes under a specific filename in a category.
    pub async fn put_named(
        &self,
        category: &str,
        filename: &str,
        data: &[u8],
    ) -> Result<PathBuf, BlobError> {
        let path = self.base_dir.join(category).join(filename);
        tokio::fs::write(&path, data).await?;
        Ok(path)
    }

    /// Read bytes from storage.
    pub async fn get(&self, category: &str, filename: &str) -> Result<Vec<u8>, BlobError> {
        let path = self.base_dir.join(category).join(filename);
        if !path.exists() {
            return Err(BlobError::NotFound(format!("{category}/{filename}")));
        }
        let data = tokio::fs::read(&path).await?;
        Ok(data)
    }

    /// Delete a blob. Returns true if the file existed and was deleted.
    pub async fn delete(&self, category: &str, filename: &str) -> Result<bool, BlobError> {
        let path = self.base_dir.join(category).join(filename);
        if path.exists() {
            tokio::fs::remove_file(&path).await?;
            Ok(true)
        } else {
            Ok(false)
        }
    }

    /// Check if a blob exists.
    pub async fn exists(&self, category: &str, filename: &str) -> bool {
        self.base_dir.join(category).join(filename).exists()
    }

    /// Get the absolute filesystem path for a blob (for serving static files).
    pub fn path(&self, category: &str, filename: &str) -> PathBuf {
        self.base_dir.join(category).join(filename)
    }

    /// Get the base directory path.
    pub fn base_dir(&self) -> &Path {
        &self.base_dir
    }

    /// Copy a blob within the same category under a new name.
    pub async fn copy(
        &self,
        category: &str,
        src_filename: &str,
        dst_filename: &str,
    ) -> Result<(), BlobError> {
        let src = self.base_dir.join(category).join(src_filename);
        let dst = self.base_dir.join(category).join(dst_filename);
        tokio::fs::copy(&src, &dst).await?;
        Ok(())
    }
}
