use image::GrayImage;

/// Compute the optimal binarization threshold using Otsu's method.
///
/// Maximizes between-class variance to find the threshold that best separates
/// foreground (glyphs) from background.
pub fn otsu_threshold(hist: &[u64; 256], total_pixels: u64) -> u8 {
    if total_pixels == 0 {
        return 128;
    }

    let mut sum_total: f64 = 0.0;
    for (i, &count) in hist.iter().enumerate() {
        sum_total += i as f64 * count as f64;
    }

    let mut sum_bg: f64 = 0.0;
    let mut weight_bg: f64 = 0.0;
    let mut max_variance: f64 = 0.0;
    let mut best_threshold: u8 = 0;

    for (t, &count) in hist.iter().enumerate() {
        weight_bg += count as f64;
        if weight_bg == 0.0 {
            continue;
        }
        let weight_fg = total_pixels as f64 - weight_bg;
        if weight_fg == 0.0 {
            break;
        }

        sum_bg += t as f64 * count as f64;

        let mean_bg = sum_bg / weight_bg;
        let mean_fg = (sum_total - sum_bg) / weight_fg;

        let between_variance = weight_bg * weight_fg * (mean_bg - mean_fg).powi(2);

        if between_variance > max_variance {
            max_variance = between_variance;
            best_threshold = t as u8;
        }
    }

    best_threshold
}

/// Binarize a grayscale image: foreground (below threshold) → 255, background → 0.
/// This follows the Python convention where dark pixels are foreground.
pub fn binarize(img: &GrayImage, threshold: u8) -> GrayImage {
    let (w, h) = img.dimensions();
    let mut out = GrayImage::new(w, h);
    for y in 0..h {
        for x in 0..w {
            let val = img.get_pixel(x, y).0[0];
            out.put_pixel(
                x,
                y,
                image::Luma([if val <= threshold { 255 } else { 0 }]),
            );
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_otsu_bimodal() {
        let mut hist = [0u64; 256];
        // Two clusters: around 50 and 200
        for i in 40..60 {
            hist[i] = 100;
        }
        for i in 190..210 {
            hist[i] = 100;
        }
        let total: u64 = hist.iter().sum();
        let t = otsu_threshold(&hist, total);
        // Threshold should be between the two clusters
        assert!(t >= 59 && t < 190, "threshold was {t}");
    }

    #[test]
    fn test_binarize_simple() {
        let img = GrayImage::from_raw(3, 1, vec![10, 128, 250]).unwrap();
        let bin = binarize(&img, 128);
        assert_eq!(bin.get_pixel(0, 0).0[0], 255); // dark → foreground
        assert_eq!(bin.get_pixel(1, 0).0[0], 255); // equal to threshold → foreground
        assert_eq!(bin.get_pixel(2, 0).0[0], 0); // bright → background
    }
}
