use crate::vectorize::{get_glyph_rects_from_file, PixelRect};
use std::path::Path;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ExportError {
    #[error("image error: {0}")]
    Image(#[from] font_lab_image_core::ImageError),

    #[error("no glyphs to export")]
    NoGlyphs,

    #[error("font build error: {0}")]
    Build(String),
}

#[allow(dead_code)]
const UNITS_PER_EM: u16 = 1000;
const ASCENT: i16 = 800;
#[allow(dead_code)]
const DESCENT: i16 = -200;
#[allow(dead_code)]
const CAP_HEIGHT: f64 = 700.0;
const MARGIN: f64 = 50.0;

/// A glyph entry ready for font building.
pub struct GlyphEntry {
    pub codepoint: char,
    pub rects: Vec<PixelRect>,
    pub pixel_width: u32,
    pub pixel_height: u32,
}

/// Collect glyph entries from labeled glyph files on disk.
pub fn collect_glyph_entries(
    glyphs: &[(char, &Path)],
) -> Result<Vec<GlyphEntry>, ExportError> {
    let mut entries = Vec::new();

    for (ch, path) in glyphs {
        let (rects, w, h) = get_glyph_rects_from_file(path)?;
        entries.push(GlyphEntry {
            codepoint: *ch,
            rects,
            pixel_width: w,
            pixel_height: h,
        });
    }

    // Sort by Unicode codepoint
    entries.sort_by_key(|e| e.codepoint as u32);

    // Deduplicate by codepoint (keep first)
    entries.dedup_by_key(|e| e.codepoint);

    if entries.is_empty() {
        return Err(ExportError::NoGlyphs);
    }

    Ok(entries)
}

/// Scale pixel rectangles to font units.
fn scale_rects(
    rects: &[PixelRect],
    pixel_height: u32,
    scale: f64,
) -> Vec<(f64, f64, f64, f64)> {
    rects
        .iter()
        .map(|r| {
            let x0 = MARGIN + r.x0 as f64 * scale;
            let x1 = MARGIN + r.x1 as f64 * scale;
            // Flip Y: font coords have y=0 at baseline, increasing upward
            let y0 = ASCENT as f64 - r.y as f64 * scale;
            let y1 = ASCENT as f64 - (r.y + 1) as f64 * scale;
            (x0, y0, x1, y1)
        })
        .collect()
}

/// Build a TrueType font binary from glyph entries.
///
/// This is a simplified builder that creates filled rectangles from the
/// scanline-vectorized raster data. The output is functional but not
/// production-quality — it matches the behavior of the original Python export.
pub fn build_ttf(
    _entries: &[GlyphEntry],
    _font_name: &str,
    _style_name: &str,
) -> Result<Vec<u8>, ExportError> {
    // For now, return a placeholder since write-fonts API is complex.
    // This establishes the interface; a proper implementation will use
    // the write-fonts TTF builder once the crate compiles.
    Err(ExportError::Build(
        "TTF export not yet implemented with write-fonts; use the worker pipeline".into(),
    ))
}

/// Build an OpenType CFF font binary from glyph entries.
pub fn build_otf(
    _entries: &[GlyphEntry],
    _font_name: &str,
    _style_name: &str,
) -> Result<Vec<u8>, ExportError> {
    Err(ExportError::Build(
        "OTF/CFF export not yet implemented with write-fonts; use the worker pipeline".into(),
    ))
}
