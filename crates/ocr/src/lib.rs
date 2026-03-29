use std::path::Path;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum OcrError {
    #[error("ocr engine not available: {0}")]
    Unavailable(String),

    #[error("ocr processing failed: {0}")]
    Processing(String),
}

/// A single OCR recognition suggestion.
#[derive(Debug, Clone)]
pub struct OcrSuggestion {
    pub text: String,
    pub confidence: f64,
}

/// Trait for OCR adapters. Implementations can wrap Tesseract, cloud APIs, etc.
pub trait OcrEngine: Send + Sync {
    /// Recognize text in a glyph crop image. Returns suggestions sorted by
    /// confidence descending.
    fn recognize(&self, image_path: &Path) -> Result<Vec<OcrSuggestion>, OcrError>;
}

/// Stub OCR engine that always returns an error.
/// Replace with a Tesseract adapter when ready.
pub struct StubOcrEngine;

impl OcrEngine for StubOcrEngine {
    fn recognize(&self, _image_path: &Path) -> Result<Vec<OcrSuggestion>, OcrError> {
        Err(OcrError::Unavailable(
            "No OCR engine configured. Install Tesseract and enable the tesseract adapter.".into(),
        ))
    }
}

/// Normalize OCR confidence to [0, 1].
pub fn normalize_confidence(raw: f64, max: f64) -> f64 {
    if max <= 0.0 {
        return 0.0;
    }
    (raw / max).clamp(0.0, 1.0)
}
