use crate::entities::{Glyph, GlyphCoverageSummary};
use chrono::Utc;
use std::collections::HashSet;

const STANDARD_ASCII_COUNT: f64 = 95.0;

/// Compute glyph coverage statistics from a list of glyphs.
pub fn compute_coverage(sample_id: i64, glyphs: &[Glyph]) -> GlyphCoverageSummary {
    let total = glyphs.len() as i32;
    let verified = glyphs.iter().filter(|g| g.verified).count() as i32;

    let mut latin_basic = 0i32;
    let mut latin_extended = 0i32;
    let mut digits = 0i32;
    let mut punctuation = 0i32;
    let mut unique_labels = HashSet::new();

    for g in glyphs {
        if let Some(ref label) = g.label {
            if label.len() != 1 {
                continue;
            }
            let ch = label.chars().next().unwrap();
            unique_labels.insert(ch);

            if ch.is_ascii_alphabetic() {
                latin_basic += 1;
            } else if ch.is_alphabetic() && !ch.is_ascii() {
                latin_extended += 1;
            } else if ch.is_ascii_digit() {
                digits += 1;
            } else if !ch.is_alphanumeric() {
                punctuation += 1;
            }
        }
    }

    let coverage_percent = if total > 0 {
        unique_labels.len() as f64 / STANDARD_ASCII_COUNT
    } else {
        0.0
    };

    GlyphCoverageSummary {
        id: 0,
        sample_id,
        total_glyphs: total,
        verified_glyphs: verified,
        latin_basic_count: latin_basic,
        latin_extended_count: latin_extended,
        digits_count: digits,
        punctuation_count: punctuation,
        coverage_percent,
        updated_at: Utc::now(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_glyph(sample_id: i64, label: Option<&str>, verified: bool) -> Glyph {
        Glyph {
            id: 0,
            sample_id,
            filename: String::new(),
            bbox_x: 0,
            bbox_y: 0,
            bbox_w: 10,
            bbox_h: 10,
            label: label.map(|s| s.to_string()),
            advance_width: None,
            left_bearing: None,
            verified,
            synthesized: false,
            created_at: Utc::now(),
        }
    }

    #[test]
    fn test_empty_glyphs() {
        let cov = compute_coverage(1, &[]);
        assert_eq!(cov.total_glyphs, 0);
        assert!((cov.coverage_percent - 0.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_basic_coverage() {
        let glyphs = vec![
            make_glyph(1, Some("A"), true),
            make_glyph(1, Some("B"), false),
            make_glyph(1, Some("1"), false),
            make_glyph(1, Some("!"), true),
        ];
        let cov = compute_coverage(1, &glyphs);
        assert_eq!(cov.total_glyphs, 4);
        assert_eq!(cov.verified_glyphs, 2);
        assert_eq!(cov.latin_basic_count, 2);
        assert_eq!(cov.digits_count, 1);
        assert_eq!(cov.punctuation_count, 1);
        assert!((cov.coverage_percent - 4.0 / 95.0).abs() < 0.001);
    }
}
