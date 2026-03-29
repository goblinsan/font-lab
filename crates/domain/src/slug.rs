use regex::Regex;

/// Generate a URL-safe slug from text.
///
/// Example: "HelveticA Neue (1957)" → "helvetica-neue-1957"
pub fn make_slug(text: &str) -> String {
    let text = text.to_lowercase();
    let text = text.trim();

    // Remove non-word chars except hyphens and whitespace
    let re_nonword = Regex::new(r"[^\w\s-]").unwrap();
    let text = re_nonword.replace_all(text, "");

    // Spaces and underscores → hyphens
    let re_spaces = Regex::new(r"[\s_]+").unwrap();
    let text = re_spaces.replace_all(&text, "-");

    // Collapse multiple hyphens
    let re_hyphens = Regex::new(r"-{2,}").unwrap();
    let text = re_hyphens.replace_all(&text, "-");

    text.trim_matches('-').to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_slug() {
        assert_eq!(make_slug("Helvetica Neue"), "helvetica-neue");
    }

    #[test]
    fn test_slug_with_parens() {
        assert_eq!(make_slug("HelveticA Neue (1957)"), "helvetica-neue-1957");
    }

    #[test]
    fn test_slug_strips_special_chars() {
        assert_eq!(make_slug("Font Name!@#$%"), "font-name");
    }

    #[test]
    fn test_slug_collapses_spaces() {
        assert_eq!(make_slug("  lots   of   spaces  "), "lots-of-spaces");
    }

    #[test]
    fn test_slug_underscores() {
        assert_eq!(make_slug("font_name_bold"), "font-name-bold");
    }
}
