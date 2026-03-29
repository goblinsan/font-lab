use norad::Font as UfoFont;
use std::path::Path;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum SourceError {
    #[error("norad error: {0}")]
    Norad(#[from] norad::error::FontWriteError),

    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    #[error("no approved glyphs")]
    NoGlyphs,
}

/// Generate a UFO package from approved glyph data.
///
/// This is the canonical editable font source format. The UFO package
/// is written to `output_dir` and can be versioned in blob storage.
pub fn generate_ufo(
    font_name: &str,
    glyphs: &[(char, Vec<(f64, f64, f64, f64)>)],
    output_dir: &Path,
) -> Result<(), SourceError> {
    if glyphs.is_empty() {
        return Err(SourceError::NoGlyphs);
    }

    let mut font = UfoFont::new();

    // Set font info via the public field
    font.font_info.family_name = Some(font_name.to_string());
    font.font_info.units_per_em =
        norad::fontinfo::NonNegativeIntegerOrFloat::new(1000.0);
    font.font_info.ascender = Some(800.0);
    font.font_info.descender = Some(-200.0);

    // Add glyphs to the default layer
    let default_layer = font.default_layer_mut();
    for (ch, rects) in glyphs {
        let glyph_name_str = format!("uni{:04X}", *ch as u32);

        let mut glyph = norad::Glyph::new(&glyph_name_str);
        glyph.codepoints = norad::Codepoints::new([*ch]);

        // Build contour from rectangles
        for (x0, y0, x1, y1) in rects {
            let mut contour = norad::Contour::default();
            contour.points.push(norad::ContourPoint::new(
                *x0, *y0, norad::PointType::Line, false, None, None,
            ));
            contour.points.push(norad::ContourPoint::new(
                *x1, *y0, norad::PointType::Line, false, None, None,
            ));
            contour.points.push(norad::ContourPoint::new(
                *x1, *y1, norad::PointType::Line, false, None, None,
            ));
            contour.points.push(norad::ContourPoint::new(
                *x0, *y1, norad::PointType::Line, false, None, None,
            ));
            glyph.contours.push(contour);
        }

        let _ = default_layer.insert_glyph(glyph);
    }

    font.save(output_dir)?;

    Ok(())
}
