pub mod threshold;
pub mod crop;

use image::GrayImage;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ImageError {
    #[error("image error: {0}")]
    Image(#[from] image::ImageError),

    #[error("empty image")]
    EmptyImage,
}

/// Load an image from bytes and convert to grayscale.
pub fn load_grayscale(data: &[u8]) -> Result<GrayImage, ImageError> {
    let img = image::load_from_memory(data)?;
    Ok(img.to_luma8())
}

/// Load a grayscale image from a file path.
pub fn load_grayscale_file(path: &std::path::Path) -> Result<GrayImage, ImageError> {
    let img = image::open(path)?;
    Ok(img.to_luma8())
}

/// Build a 256-bin histogram from a grayscale image.
pub fn histogram(img: &GrayImage) -> [u64; 256] {
    let mut hist = [0u64; 256];
    for pixel in img.pixels() {
        hist[pixel.0[0] as usize] += 1;
    }
    hist
}
