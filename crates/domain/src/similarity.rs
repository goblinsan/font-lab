use crate::entities::FontSample;
use std::collections::HashSet;

/// Weights for similarity scoring between two font samples.
const STYLE_WEIGHT: f64 = 0.25;
const GENRE_WEIGHT: f64 = 0.10;
const THEME_WEIGHT: f64 = 0.20;
const CATEGORY_WEIGHT: f64 = 0.15;
const ERA_WEIGHT: f64 = 0.05;
const TAGS_WEIGHT: f64 = 0.10;
const MOODS_WEIGHT: f64 = 0.05;
const VISUAL_TRAITS_WEIGHT: f64 = 0.10;

fn str_eq_ci(a: &Option<String>, b: &Option<String>) -> bool {
    match (a, b) {
        (Some(a), Some(b)) => a.eq_ignore_ascii_case(b),
        _ => false,
    }
}

fn jaccard(a: &[String], b: &[String]) -> f64 {
    if a.is_empty() && b.is_empty() {
        return 0.0;
    }
    let set_a: HashSet<&str> = a.iter().map(|s| s.as_str()).collect();
    let set_b: HashSet<&str> = b.iter().map(|s| s.as_str()).collect();
    let intersection = set_a.intersection(&set_b).count() as f64;
    let union = set_a.union(&set_b).count() as f64;
    if union == 0.0 { 0.0 } else { intersection / union }
}

/// Compute a similarity score between two font samples. Returns a value in [0, 1].
pub fn similarity_score(target: &FontSample, candidate: &FontSample) -> f64 {
    let mut score = 0.0;

    if str_eq_ci(&target.style, &candidate.style) {
        score += STYLE_WEIGHT;
    }
    if str_eq_ci(&target.genre, &candidate.genre) {
        score += GENRE_WEIGHT;
    }
    if str_eq_ci(&target.theme, &candidate.theme) {
        score += THEME_WEIGHT;
    }
    if str_eq_ci(&target.font_category, &candidate.font_category) {
        score += CATEGORY_WEIGHT;
    }
    if str_eq_ci(&target.era, &candidate.era) {
        score += ERA_WEIGHT;
    }

    score += TAGS_WEIGHT * jaccard(&target.tags, &candidate.tags);
    score += MOODS_WEIGHT * jaccard(&target.moods, &candidate.moods);
    score += VISUAL_TRAITS_WEIGHT * jaccard(&target.visual_traits, &candidate.visual_traits);

    (score * 10000.0).round() / 10000.0
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_sample() -> FontSample {
        FontSample {
            id: 0,
            filename: String::new(),
            original_filename: String::new(),
            slug: None,
            font_name: None,
            font_category: Some("Headline".into()),
            style: Some("Serif".into()),
            genre: Some("Old Style".into()),
            theme: Some("Vintage".into()),
            era: Some("1800s".into()),
            provenance: None,
            confidence: None,
            notes: None,
            source: None,
            restoration_notes: None,
            tags: vec!["classic".into(), "elegant".into()],
            file_size: None,
            content_type: None,
            uploaded_at: chrono::Utc::now(),
            origin_context: None,
            source_type: None,
            restoration_status: None,
            rights_status: None,
            rights_notes: None,
            completeness: None,
            moods: vec!["warm".into()],
            use_cases: vec![],
            construction_traits: vec![],
            visual_traits: vec!["high-contrast".into()],
            review_status: None,
            is_archived: false,
            archived_at: None,
        }
    }

    #[test]
    fn test_identical_samples_max_score() {
        let a = make_sample();
        let b = a.clone();
        let score = similarity_score(&a, &b);
        assert!((score - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_completely_different_samples() {
        let a = make_sample();
        let mut b = make_sample();
        b.style = Some("Sans-Serif".into());
        b.genre = Some("Geometric Sans".into());
        b.theme = Some("Modern".into());
        b.font_category = Some("Body Text".into());
        b.era = Some("2000s".into());
        b.tags = vec!["minimal".into()];
        b.moods = vec!["cold".into()];
        b.visual_traits = vec!["low-contrast".into()];
        let score = similarity_score(&a, &b);
        assert!(score < 0.01);
    }
}
