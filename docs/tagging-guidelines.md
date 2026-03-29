# font-lab Tagging and Curation Guidelines

This document describes how to classify fonts consistently using the font-lab
taxonomy, handle ambiguous cases, apply synonym expansion, and review
community or internal submissions.

---

## Table of Contents

1. [Taxonomy overview](#1-taxonomy-overview)
2. [Core classification workflow](#2-core-classification-workflow)
3. [Dimension-by-dimension guidance](#3-dimension-by-dimension-guidance)
4. [Handling ambiguous cases](#4-handling-ambiguous-cases)
5. [Applying synonyms](#5-applying-synonyms)
6. [Provenance and rights classification](#6-provenance-and-rights-classification)
7. [Restoration status workflow](#7-restoration-status-workflow)
8. [Community submission review](#8-community-submission-review)
9. [Quality checklist](#9-quality-checklist)

---

## 1. Taxonomy overview

The font-lab taxonomy is a controlled vocabulary organised across 13 dimensions.
Each dimension has a defined **cardinality** (single-select or multi-select) and
an authoritative list of allowed values.  Retrieve the current values via:

```http
GET /api/taxonomy/
```

| Dimension            | Cardinality  | Purpose                                          |
|----------------------|--------------|--------------------------------------------------|
| `style`              | single       | Primary visual family (Serif, Sans-Serif, …)     |
| `genre`              | single       | Sub-genre within the style family                |
| `theme`              | multi        | Aesthetic theme descriptors                      |
| `moods`              | multi        | Emotional/expressive tone                        |
| `font_category`      | single       | Primary intended use (Body Text, Headline, …)    |
| `use_cases`          | multi        | Specific use contexts (Poster, Logo, …)          |
| `era`                | single       | Historical or cultural period                    |
| `origin_context`     | single       | Geographic or cultural provenance                |
| `construction_traits`| multi        | Structural features (High Contrast, Slab Serif…) |
| `visual_traits`      | multi        | Machine-usable visual trait vocabulary           |
| `restoration_status` | single       | Digitisation/restoration workflow stage          |
| `source_type`        | single       | Physical or digital artifact category            |
| `rights_status`      | single       | Licensing/rights classification                  |

---

## 2. Core classification workflow

Apply dimensions in the following order to ensure consistency:

1. **Identify the style family** (`style`) — this is the most important field.
   Pick exactly one value from the canonical list.
2. **Assign a genre** (`genre`) — choose the sub-genre that best matches the
   typeface's structural characteristics within the style family.  Use the
   hierarchy (`GET /api/taxonomy/hierarchy`) to navigate parent → child
   relationships.
3. **Tag themes and moods** (`theme`, `moods`) — add all values that clearly
   apply; avoid speculative tags.
4. **Set the use category and use cases** (`font_category`, `use_cases`) —
   `font_category` is the primary intended use; `use_cases` lists all
   practical contexts.
5. **Set the era** (`era`) — use the most specific canonical period that
   applies.  Prefer decade ranges for documented historical typefaces; use
   named cultural periods (Art Deco, Bauhaus) only when strongly associated.
6. **Set origin context** (`origin_context`) — reflect foundry or designer
   geography, not the language the typeface supports.
7. **Add construction and visual traits** — these drive similarity and
   recommendation; accuracy here directly affects search quality.
8. **Record provenance and rights** — required for any font used commercially.

---

## 3. Dimension-by-dimension guidance

### 3.1 Style

- Choose the **dominant** visual family.  A font can only have one `style`.
- If a typeface is simultaneously slab-serif and display-oriented, prefer
  `Slab Serif` for the style and add `Display` context in `use_cases`.
- `Script` covers both formal (copperplate) and casual (brush) scripts; use
  `genre` to distinguish.

### 3.2 Genre

- Genre must be consistent with the style hierarchy.  An `Old Style` genre
  requires a `Serif` style.
- Leave `genre` null rather than choosing a poor fit.
- When a typeface is a hybrid (e.g. a slab with strong display personality),
  use the genre that reflects its design origin, not its marketing name.

### 3.3 Themes and Moods

- `theme` values are broader aesthetic labels (Vintage, Modern).
- `mood` values are emotional/expressive descriptors (Nostalgic, Technical).
- Both are multi-select; add every value that clearly applies to the design,
  but avoid padding — each tag should reflect a deliberate design choice.
- A single font may reasonably carry both `Vintage` (theme) and `Nostalgic`
  (mood) without contradiction.

### 3.4 Era

- Use decade ranges (e.g. `1920s–1930s`) for typefaces with a documented
  design date in that range.
- Use cultural-period labels (Art Deco, Bauhaus) only for typefaces strongly
  identified with that movement.
- If a revival was released later but closely follows a historical model, tag
  the **original design era**, not the revival date.  Note the revival in
  `notes` or `provenance`.

### 3.5 Construction and Visual Traits

- `construction_traits` captures formal/structural properties (Condensed,
  High Contrast, Ball Terminal).
- `visual_traits` is the machine-usable vocabulary for similarity ranking;
  apply values from each sub-group (contrast, weight, width, serif form,
  terminals, curvature, etc.) as applicable.
- Be precise with contrast: measure visually against the stroke thickness
  ratio, not subjective impression.

### 3.6 Origin Context

- Reflects the geographic origin of the foundry or designer, not the
  typeface's language support.
- Use `International` for typefaces designed collaboratively across regions or
  by designers without a clear national affiliation.
- Use `Unknown` only when provenance is genuinely unresolved.

---

## 4. Handling ambiguous cases

### Hybrid style families

When a typeface does not fit cleanly into one family, apply these rules:

1. Choose the style that governs the **lowercase** design (lowercase carries
   more stylistic information than uppercase or display characters).
2. Reflect the secondary character in `construction_traits` (e.g.
   `Slab Serif` in construction_traits for a display sans with slab accents).
3. Note the hybrid nature in `notes`.

### Revivals and digitisations

- Tag the **original historical design era**, not the revival date.
- Record the revival context in `provenance` (e.g. "2003 revival of 1920s
  foundry original").
- Set `restoration_status` to reflect the current digitisation stage.

### Display vs. Text

- A typeface designed for both display and body text (e.g. Garamond) should
  have `font_category` = the **primary** use and `use_cases` listing all
  practical contexts.
- Do not force a display-only font into `Body Text` use case.

### Era overlap

When a typeface spans multiple decade ranges (e.g. was designed in 1928 and
re-cut in 1935), choose the era of the **original design**.

---

## 5. Applying synonyms

The synonym map (`GET /api/taxonomy/synonyms`) maps canonical values to their
accepted aliases.  Use it to:

- **Normalise incoming tags** from community submissions (e.g. convert
  `"grotesque"` → `"Sans-Serif"`).
- **Expand queries** in search (e.g. a search for `"egyptian"` should also
  match `"Slab Serif"`).
- **Validate** submissions — a value that matches a known synonym should be
  silently converted to its canonical form, not rejected.

When reviewing a submission that uses a recognised synonym, convert to the
canonical value and note the change in the review log.

---

## 6. Provenance and rights classification

### Source type

`source_type` documents the physical or digital artifact from which the font
was digitised.  This is not the same as `provenance` (which is free text).

| Source Type              | When to use                                            |
|--------------------------|--------------------------------------------------------|
| Printed Specimen         | A bound or loose specimen sheet from the foundry       |
| Type Catalogue           | A bound catalogue with multiple specimens              |
| Foundry Broadsheet       | A single-sheet advertisement or announcement           |
| Magazine / Periodical    | A typeface sampled from a magazine typeset in the font |
| Book                     | A typeface sampled from book pages                     |
| Poster / Ephemera        | Signage, posters, labels, or other ephemeral print     |
| Signage Photograph       | A photograph of physical signage                       |
| Vector / Digital File    | An existing vector/EPS/SVG file                        |
| Existing Font File       | An existing .otf/.ttf/.woff file                       |
| Hand-Drawn Original      | Artist's original hand-drawn artwork                   |
| Unknown                  | Source cannot be determined                            |

### Rights status

Always confirm rights before assigning `Public Domain` or `Open Font License`.
Use these rules:

- **Public Domain**: use only when the typeface was published before 1928
  (US) or before the applicable local copyright expiry, or when the rights
  holder has explicitly released it.
- **Open Font License**: confirm that the font file is distributed under the
  SIL OFL or equivalent.
- **Commercial License**: the font is under a paid or restricted licence held
  by the organisation.
- **Rights Unclear**: investigation is ongoing.  Do not distribute externally
  until resolved.
- **Orphan Work**: the rights holder cannot be identified or contacted.

Record any supporting detail in `rights_notes`.

---

## 7. Restoration status workflow

Move a font through the restoration pipeline in order:

```
Raw Scan → Cleaned → Segmented → Outlined → Kerned → Hinted → Complete → Published
```

- **Raw Scan**: the image has been uploaded but no processing has occurred.
- **Cleaned**: noise, stains, and artifacts have been removed.
- **Segmented**: glyphs have been extracted and labelled.
- **Outlined**: vector outlines have been generated for each glyph.
- **Kerned**: spacing and kerning pairs have been defined.
- **Hinted**: screen-rendering hints have been applied.
- **Complete**: the font file has been assembled and passes quality checks.
- **Published**: the font is available for download or integration.
- **Archived**: the font has been preserved in long-term storage; no further
  active work is planned.

Never skip stages for fonts intended for commercial or public distribution.
For internal research samples, `Segmented` or `Outlined` may be sufficient.

---

## 8. Community submission review

When reviewing a community-submitted font record:

1. **Validate required fields**: `style` must be set.  If missing, request it.
2. **Check canonical values**: each taxonomy field value must exactly match
   (or be a recognised synonym of) a canonical value.  Convert synonyms;
   reject unrecognised values with an explanation.
3. **Verify era plausibility**: cross-reference the stated era against the
   `provenance` notes and known design history.
4. **Audit rights**: any `Public Domain` or `Open Font License` claim must be
   supported by a reference in `rights_notes`.
5. **Review visual traits**: spot-check `visual_traits` against the preview
   image.  Remove values that are clearly inaccurate; flag uncertain values
   with a note.
6. **Check completeness score**: the `completeness` field (0.0–1.0) should
   reflect the proportion of the full character set that has been digitised.
7. **Log decisions**: record any substantive change made during review in
   `notes`, crediting the reviewer.

---

## 9. Quality checklist

Before marking a font record as `Complete`:

- [ ] `style` is set and matches the visual design
- [ ] `genre` is consistent with the style hierarchy
- [ ] At least one `theme` or `mood` value is set
- [ ] `font_category` and at least one `use_case` are set
- [ ] `era` is set and plausibly sourced
- [ ] `origin_context` is set
- [ ] `construction_traits` has at least two values
- [ ] `visual_traits` covers contrast, weight, width, and serif form
- [ ] `source_type` is set
- [ ] `rights_status` is set; `rights_notes` is present if rights are unclear
- [ ] `provenance` has a reference to the source material
- [ ] `completeness` reflects the actual glyph coverage (0.0–1.0)
- [ ] `restoration_status` reflects the current digitisation stage
- [ ] Preview image clearly shows the font at a readable size
