use font_lab_image_core::{
    load_grayscale_file,
    threshold::{binarize, otsu_threshold},
};
use image::GrayImage;
use std::path::Path;

/// A filled rectangle in pixel coordinates (x0, y, x1, y+1).
#[derive(Debug, Clone, Copy)]
pub struct PixelRect {
    pub x0: u32,
    pub y: u32,
    pub x1: u32,
}

/// Extract filled rectangles from a glyph crop using scanline analysis.
///
/// For each row, contiguous foreground pixels become a filled rectangle.
pub fn get_glyph_rects(img: &GrayImage) -> Vec<PixelRect> {
    let (w, h) = img.dimensions();
    let hist = crate::vectorize::image_histogram(img);
    let total = w as u64 * h as u64;
    let threshold = otsu_threshold(&hist, total);
    let binary = binarize(img, threshold);

    let mut rects = Vec::new();

    for y in 0..h {
        let mut x = 0u32;
        while x < w {
            if binary.get_pixel(x, y).0[0] > 0 {
                let x0 = x;
                while x < w && binary.get_pixel(x, y).0[0] > 0 {
                    x += 1;
                }
                rects.push(PixelRect { x0, y, x1: x });
            } else {
                x += 1;
            }
        }
    }

    rects
}

fn image_histogram(img: &GrayImage) -> [u64; 256] {
    let mut hist = [0u64; 256];
    for pixel in img.pixels() {
        hist[pixel.0[0] as usize] += 1;
    }
    hist
}

/// Extract rectangles from a glyph crop file, returning (rects, width, height).
pub fn get_glyph_rects_from_file(
    path: &Path,
) -> Result<(Vec<PixelRect>, u32, u32), font_lab_image_core::ImageError> {
    let gray = load_grayscale_file(path)?;
    let (w, h) = gray.dimensions();
    let rects = get_glyph_rects(&gray);
    Ok((rects, w, h))
}

/// Generate an SVG document from a glyph crop image.
pub fn glyph_to_svg(path: &Path) -> Result<String, font_lab_image_core::ImageError> {
    let (rects, w, h) = get_glyph_rects_from_file(path)?;

    let mut path_data = String::new();
    for r in &rects {
        use std::fmt::Write;
        write!(
            &mut path_data,
            "M {} {} H {} V {} H {} Z ",
            r.x0,
            r.y,
            r.x1,
            r.y + 1,
            r.x0
        )
        .unwrap();
    }

    Ok(format!(
        r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"><path fill="#000000" d="{path_data}"/></svg>"##
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_glyph_rects_simple() {
        // 3x2 image: row 0 = [black, black, white], row 1 = [white, black, black]
        let img = GrayImage::from_raw(3, 2, vec![0, 0, 255, 255, 0, 0]).unwrap();
        let rects = get_glyph_rects(&img);
        assert_eq!(rects.len(), 2);
    }
}
