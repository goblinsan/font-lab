use image::GrayImage;

/// Extract a rectangular crop from a grayscale image with padding.
pub fn extract_crop(
    img: &GrayImage,
    x: u32,
    y: u32,
    w: u32,
    h: u32,
    padding: u32,
) -> GrayImage {
    let (img_w, img_h) = img.dimensions();

    let x0 = x.saturating_sub(padding);
    let y0 = y.saturating_sub(padding);
    let x1 = (x + w + padding).min(img_w);
    let y1 = (y + h + padding).min(img_h);

    let crop_w = x1 - x0;
    let crop_h = y1 - y0;

    let mut out = GrayImage::new(crop_w, crop_h);
    for cy in 0..crop_h {
        for cx in 0..crop_w {
            let pixel = img.get_pixel(x0 + cx, y0 + cy);
            out.put_pixel(cx, cy, *pixel);
        }
    }
    out
}
