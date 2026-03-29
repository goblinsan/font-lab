use font_lab_image_core::{
    histogram, load_grayscale_file,
    threshold::{binarize, otsu_threshold},
    crop::extract_crop,
};
use image::GrayImage;
use std::path::{Path, PathBuf};
use thiserror::Error;
use uuid::Uuid;

#[derive(Debug, Error)]
pub enum SegmentError {
    #[error("image error: {0}")]
    Image(#[from] font_lab_image_core::ImageError),

    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    #[error("image encoding error: {0}")]
    ImageWrite(#[from] image::ImageError),
}

/// Information about a detected glyph region.
#[derive(Debug, Clone)]
pub struct GlyphInfo {
    pub filename: String,
    pub bbox_x: u32,
    pub bbox_y: u32,
    pub bbox_w: u32,
    pub bbox_h: u32,
}

/// Parameters controlling segmentation behavior.
#[derive(Debug, Clone)]
pub struct SegmentParams {
    pub min_glyph_w: u32,
    pub min_glyph_h: u32,
    pub padding: u32,
    pub intra_glyph_gap: u32,
}

impl Default for SegmentParams {
    fn default() -> Self {
        Self {
            min_glyph_w: 4,
            min_glyph_h: 4,
            padding: 2,
            intra_glyph_gap: 2,
        }
    }
}

/// Find contiguous non-zero runs in a 1-D histogram, with gap tolerance.
fn find_runs(histogram: &[u32], min_gap: u32) -> Vec<(u32, u32)> {
    let mut runs = Vec::new();
    let mut in_run = false;
    let mut start = 0u32;
    let mut gap_count = 0u32;

    for (i, &val) in histogram.iter().enumerate() {
        if val > 0 {
            if !in_run {
                start = i as u32;
                in_run = true;
            }
            gap_count = 0;
        } else if in_run {
            gap_count += 1;
            if gap_count > min_gap {
                // End is exclusive: one past the last non-zero
                runs.push((start, i as u32 - gap_count + 1));
                in_run = false;
                gap_count = 0;
            }
        }
    }
    if in_run {
        let end = histogram.len() as u32;
        runs.push((start, end - gap_count));
    }
    runs
}

/// Compute row projection: for each row, count the foreground pixels.
fn row_projection(binary: &GrayImage) -> Vec<u32> {
    let (w, h) = binary.dimensions();
    let mut proj = vec![0u32; h as usize];
    for y in 0..h {
        for x in 0..w {
            if binary.get_pixel(x, y).0[0] > 0 {
                proj[y as usize] += 1;
            }
        }
    }
    proj
}

/// Compute column projection for a row-slice of the image.
fn col_projection(binary: &GrayImage, y_start: u32, y_end: u32) -> Vec<u32> {
    let (w, _) = binary.dimensions();
    let mut proj = vec![0u32; w as usize];
    for y in y_start..y_end {
        for x in 0..w {
            if binary.get_pixel(x, y).0[0] > 0 {
                proj[x as usize] += 1;
            }
        }
    }
    proj
}

/// Segment a font sample image into individual glyph crops.
///
/// Algorithm:
/// 1. Load image, convert to grayscale
/// 2. Compute Otsu threshold and binarize
/// 3. Row projection to detect text lines
/// 4. For each line: column projection to isolate characters
/// 5. For each character: crop with padding, save as PNG
pub fn segment_image(
    image_path: &Path,
    output_dir: &Path,
    params: &SegmentParams,
) -> Result<Vec<GlyphInfo>, SegmentError> {
    let gray = load_grayscale_file(image_path)?;
    let hist = histogram(&gray);
    let total_pixels = gray.width() as u64 * gray.height() as u64;
    let threshold = otsu_threshold(&hist, total_pixels);
    let binary = binarize(&gray, threshold);

    let row_proj = row_projection(&binary);
    let lines = find_runs(&row_proj, params.intra_glyph_gap);

    let mut glyphs = Vec::new();

    std::fs::create_dir_all(output_dir)?;

    for (line_y_start, line_y_end) in &lines {
        let col_proj = col_projection(&binary, *line_y_start, *line_y_end);
        let chars = find_runs(&col_proj, params.intra_glyph_gap);

        for (char_x_start, char_x_end) in &chars {
            let w = char_x_end - char_x_start;
            let h = line_y_end - line_y_start;

            if w < params.min_glyph_w || h < params.min_glyph_h {
                continue;
            }

            let crop = extract_crop(
                &gray,
                *char_x_start,
                *line_y_start,
                w,
                h,
                params.padding,
            );

            let filename = format!("{}.png", Uuid::new_v4());
            let crop_path = output_dir.join(&filename);
            crop.save(&crop_path)?;

            glyphs.push(GlyphInfo {
                filename,
                bbox_x: *char_x_start,
                bbox_y: *line_y_start,
                bbox_w: w,
                bbox_h: h,
            });
        }
    }

    Ok(glyphs)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_find_runs_simple() {
        let hist = vec![0, 0, 5, 3, 0, 0, 0, 8, 2, 0];
        let runs = find_runs(&hist, 0);
        assert_eq!(runs.len(), 2);
        assert_eq!(runs[0], (2, 4));
        assert_eq!(runs[1], (7, 9));
    }

    #[test]
    fn test_find_runs_with_gap_tolerance() {
        let hist = vec![5, 3, 0, 0, 8, 2];
        let runs = find_runs(&hist, 2);
        assert_eq!(runs.len(), 1);
        assert_eq!(runs[0], (0, 6));
    }

    #[test]
    fn test_find_runs_empty() {
        let hist = vec![0, 0, 0];
        let runs = find_runs(&hist, 0);
        assert!(runs.is_empty());
    }
}
