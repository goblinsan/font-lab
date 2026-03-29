use std::collections::HashMap;
use std::path::{Path, PathBuf};
use image::GrayImage;

/// Mapping of characters to visually similar "donor" characters for synthesis.
fn similar_map() -> HashMap<char, char> {
    let pairs = [
        ('a', 'o'), ('b', 'd'), ('c', 'o'), ('d', 'b'), ('e', 'o'),
        ('g', 'q'), ('h', 'n'), ('i', 'l'), ('j', 'i'), ('k', 'h'),
        ('m', 'n'), ('n', 'h'), ('o', 'c'), ('p', 'q'), ('q', 'p'),
        ('r', 'n'), ('s', 'o'), ('t', 'l'), ('u', 'n'), ('v', 'u'),
        ('w', 'v'), ('x', 'k'), ('y', 'v'), ('z', 's'),
        ('A', 'H'), ('B', 'D'), ('C', 'G'), ('D', 'B'), ('E', 'F'),
        ('F', 'E'), ('G', 'C'), ('H', 'A'), ('I', 'L'), ('J', 'I'),
        ('K', 'H'), ('L', 'I'), ('M', 'N'), ('N', 'M'), ('O', 'Q'),
        ('P', 'R'), ('Q', 'O'), ('R', 'P'), ('S', 'O'), ('T', 'I'),
        ('U', 'V'), ('V', 'U'), ('W', 'V'), ('X', 'K'), ('Y', 'V'),
        ('Z', 'S'),
        ('0', 'O'), ('1', 'I'), ('2', 'Z'), ('3', 'B'), ('4', 'A'),
        ('5', 'S'), ('6', 'G'), ('7', 'T'), ('8', 'B'), ('9', 'P'),
    ];
    pairs.into_iter().collect()
}

/// Synthesize missing glyphs for a target charset.
///
/// For each missing character, attempts to find a similar donor glyph and copy
/// its crop file. Falls back to creating a blank white crop of average dimensions.
///
/// Returns a list of (character, filename) pairs for newly created glyphs.
pub fn reconstruct_missing(
    existing: &HashMap<char, PathBuf>,
    target_charset: &str,
    output_dir: &Path,
    avg_w: u32,
    avg_h: u32,
) -> Vec<(char, String)> {
    let sim = similar_map();
    let mut created = Vec::new();

    for ch in target_charset.chars() {
        if existing.contains_key(&ch) {
            continue;
        }

        let filename = format!("{}.png", uuid::Uuid::new_v4());
        let dst_path = output_dir.join(&filename);

        let copied = if let Some(&donor_ch) = sim.get(&ch) {
            if let Some(donor_path) = existing.get(&donor_ch) {
                if donor_path.exists() {
                    std::fs::copy(donor_path, &dst_path).is_ok()
                } else {
                    false
                }
            } else {
                false
            }
        } else {
            false
        };

        if !copied {
            // Create a blank white crop
            let blank = GrayImage::from_fn(avg_w, avg_h, |_, _| image::Luma([255u8]));
            let _ = blank.save(&dst_path);
        }

        created.push((ch, filename));
    }

    created
}
