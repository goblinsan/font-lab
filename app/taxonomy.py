"""Font taxonomy: predefined dimensions, hierarchies, and controlled vocabularies.

Dimensions
----------
STYLES           – primary visual family class (single-select)
GENRES           – secondary genre within a style family (single-select)
THEMES           – aesthetic/mood descriptors (multi-select)
MOODS            – emotional/expressive tone (multi-select)
CATEGORIES       – primary intended use case (single-select)
USE_CASES        – more specific use contexts (multi-select)
ERAS             – historical or cultural period (single-select)
ORIGIN_CONTEXTS  – geographic or cultural provenance category (single-select)
CONSTRUCTION_TRAITS – structural/formal construction features (multi-select)
VISUAL_TRAITS    – machine-usable visual trait vocabulary (multi-select)
RESTORATION_STATUSES – workflow stage for digitisation/restoration (single-select)
SOURCE_TYPES     – physical or digital artifact category (single-select)
RIGHTS_STATUSES  – licensing or rights classification (single-select)

HIERARCHY        – parent→children relationships for style/genre browsing
SYNONYMS         – canonical form → list of accepted synonyms
FIELD_CONFIG     – cardinality metadata (single-select vs multi-select)
"""

# ---------------------------------------------------------------------------
# Primary style family (single-select)
# ---------------------------------------------------------------------------

STYLES: list[str] = [
    "Serif",
    "Sans-Serif",
    "Monospace",
    "Display",
    "Script",
    "Decorative",
    "Blackletter",
    "Slab Serif",
]

# ---------------------------------------------------------------------------
# Secondary genre within a style family (single-select)
# ---------------------------------------------------------------------------

GENRES: list[str] = [
    # Serif genres
    "Old Style",
    "Transitional",
    "Neoclassical",
    "Modern",
    "Slab Serif",
    "Clarendon",
    "Glyphic",
    # Sans-Serif genres
    "Grotesque",
    "Neo-Grotesque",
    "Geometric Sans",
    "Humanist Sans",
    "Superellipse",
    # Script genres
    "Casual Script",
    "Formal Script",
    "Calligraphic",
    "Brush Script",
    # Display / Decorative genres
    "Inline",
    "Outline",
    "Shadow",
    "Three-Dimensional",
    "Stencil",
    "Grunge",
    "Pixel",
    "Wood Type",
    # Blackletter genres
    "Textura",
    "Fraktur",
    "Rotunda",
    "Schwabacher",
]

# ---------------------------------------------------------------------------
# Aesthetic / mood themes (multi-select)
# ---------------------------------------------------------------------------

THEMES: list[str] = [
    "Modern",
    "Vintage",
    "Elegant",
    "Playful",
    "Bold",
    "Minimal",
    "Technical",
    "Handcrafted",
    "Retro",
    "Geometric",
]

# ---------------------------------------------------------------------------
# Expressive mood / emotional tone (multi-select)
# ---------------------------------------------------------------------------

MOODS: list[str] = [
    "Authoritative",
    "Casual",
    "Classic",
    "Clean",
    "Cold",
    "Corporate",
    "Decorative",
    "Dynamic",
    "Elegant",
    "Expressive",
    "Formal",
    "Friendly",
    "Fun",
    "Grunge",
    "Heavy",
    "Historic",
    "Industrial",
    "Legible",
    "Luxurious",
    "Mysterious",
    "Natural",
    "Nostalgic",
    "Ornate",
    "Playful",
    "Quirky",
    "Refined",
    "Romantic",
    "Rustic",
    "Serious",
    "Sophisticated",
    "Sporty",
    "Technical",
    "Warm",
    "Whimsical",
]

# ---------------------------------------------------------------------------
# Primary intended use category (single-select)
# ---------------------------------------------------------------------------

CATEGORIES: list[str] = [
    "Body Text",
    "Headline",
    "Logo",
    "UI",
    "Poster",
    "Signage",
    "Editorial",
]

# ---------------------------------------------------------------------------
# Specific use contexts (multi-select)
# ---------------------------------------------------------------------------

USE_CASES: list[str] = [
    "Body Text",
    "Caption",
    "Display Headline",
    "Drop Cap",
    "Editorial Layout",
    "Embroidery",
    "Engraving",
    "Environmental Signage",
    "Game Interface",
    "Greeting Card",
    "Iconography",
    "Invitation",
    "Label / Packaging",
    "Logo / Wordmark",
    "Mobile UI",
    "Monogram",
    "Motion / Kinetic",
    "Poster",
    "Pull Quote",
    "Social Media",
    "Subtitle / Caption",
    "T-Shirt / Merchandise",
    "Wayfinding",
    "Web Body",
    "Web Heading",
]

# ---------------------------------------------------------------------------
# Historical and cultural era (single-select)
# ---------------------------------------------------------------------------

ERAS: list[str] = [
    "Pre-1400",
    "1400s",
    "1500s",
    "1600s",
    "1700s",
    "1800s",
    "1890s–1910s",
    "1910s–1920s",
    "1920s–1930s",
    "1930s–1940s",
    "1940s–1950s",
    "1950s–1960s",
    "1960s–1970s",
    "1970s–1980s",
    "1980s–1990s",
    "1990s–2000s",
    "2000s–2010s",
    "2010s–present",
    "Art Nouveau",
    "Art Deco",
    "Bauhaus",
    "Victorian",
    "Edwardian",
    "Arts and Crafts",
    "Mid-Century Modern",
    "Psychedelic",
    "Post-Modern",
    "Digital",
]

# ---------------------------------------------------------------------------
# Geographic / cultural provenance context (single-select)
# ---------------------------------------------------------------------------

ORIGIN_CONTEXTS: list[str] = [
    "American",
    "British",
    "Central European",
    "Dutch",
    "East Asian",
    "French",
    "German",
    "International",
    "Italian",
    "Latin American",
    "Scandinavian",
    "South Asian",
    "Spanish",
    "Swiss",
    "Unknown",
]

# ---------------------------------------------------------------------------
# Structural / formal construction features (multi-select)
# ---------------------------------------------------------------------------

CONSTRUCTION_TRAITS: list[str] = [
    "Bicameral",
    "Condensed",
    "Extended",
    "High Contrast",
    "Low Contrast",
    "Monolinear",
    "Oblique Stress",
    "Optical Size Aware",
    "Variable Font",
    "Vertical Stress",
    "Wedge Serif",
    "Ball Terminal",
    "Bracketed Serif",
    "Hairline Serif",
    "Slab Serif",
    "Unbracketed Serif",
]

# ---------------------------------------------------------------------------
# Machine-usable visual trait vocabulary (multi-select)
# Used for similarity scoring and recommendation.
# ---------------------------------------------------------------------------

VISUAL_TRAITS: list[str] = [
    # Stroke contrast
    "Very Low Contrast",
    "Low Contrast",
    "Medium Contrast",
    "High Contrast",
    "Very High Contrast",
    # Stroke width / weight
    "Thin",
    "Light",
    "Regular",
    "Medium",
    "Bold",
    "Heavy",
    "Ultra Heavy",
    # Width
    "Ultra Condensed",
    "Condensed",
    "Normal Width",
    "Extended",
    "Ultra Extended",
    # Stress angle
    "Vertical Stress",
    "Diagonal Stress",
    "Oblique Stress",
    # Serif form
    "No Serif",
    "Hairline Serif",
    "Bracketed Serif",
    "Unbracketed Serif",
    "Wedge Serif",
    "Slab Serif",
    # Terminals
    "Ball Terminal",
    "Teardrop Terminal",
    "Flat Terminal",
    "Sheared Terminal",
    "Pointed Terminal",
    # Curvature
    "Geometric Curves",
    "Humanist Curves",
    "Mechanical Curves",
    "Organic Curves",
    # Geometric feel
    "Circular",
    "Square",
    "Triangular",
    "Irregular",
    # Novelty / ornamentation
    "Plain",
    "Lightly Ornamented",
    "Moderately Ornamented",
    "Heavily Ornamented",
    "Inline Detail",
    "Outline Detail",
    "Shadow Detail",
    "Texture Detail",
    # x-height
    "Low X-Height",
    "Medium X-Height",
    "High X-Height",
    # Aperture
    "Closed Aperture",
    "Open Aperture",
]

# ---------------------------------------------------------------------------
# Restoration / digitisation workflow status (single-select)
# ---------------------------------------------------------------------------

RESTORATION_STATUSES: list[str] = [
    "Raw Scan",
    "Cleaned",
    "Segmented",
    "Outlined",
    "Kerned",
    "Hinted",
    "Complete",
    "Published",
    "Archived",
]

# ---------------------------------------------------------------------------
# Physical or digital source artifact type (single-select)
# ---------------------------------------------------------------------------

SOURCE_TYPES: list[str] = [
    "Printed Specimen",
    "Type Catalogue",
    "Foundry Broadsheet",
    "Magazine / Periodical",
    "Book",
    "Poster / Ephemera",
    "Signage Photograph",
    "Vector / Digital File",
    "Existing Font File",
    "Hand-Drawn Original",
    "Unknown",
]

# ---------------------------------------------------------------------------
# Rights / licensing classification (single-select)
# ---------------------------------------------------------------------------

RIGHTS_STATUSES: list[str] = [
    "Public Domain",
    "Open Font License",
    "Commercial License",
    "Custom License",
    "Rights Unclear",
    "All Rights Reserved",
    "Orphan Work",
]

# ---------------------------------------------------------------------------
# Taxonomy hierarchy: parent → child genre/style relationships
# Powers browse navigation and filter menus.
# ---------------------------------------------------------------------------

HIERARCHY: dict[str, list[str]] = {
    "Serif": [
        "Old Style",
        "Transitional",
        "Neoclassical",
        "Modern",
        "Slab Serif",
        "Clarendon",
        "Glyphic",
    ],
    "Sans-Serif": [
        "Grotesque",
        "Neo-Grotesque",
        "Geometric Sans",
        "Humanist Sans",
        "Superellipse",
    ],
    "Script": [
        "Casual Script",
        "Formal Script",
        "Calligraphic",
        "Brush Script",
    ],
    "Display": [
        "Inline",
        "Outline",
        "Shadow",
        "Three-Dimensional",
        "Stencil",
        "Grunge",
        "Pixel",
        "Wood Type",
    ],
    "Blackletter": [
        "Textura",
        "Fraktur",
        "Rotunda",
        "Schwabacher",
    ],
}

# ---------------------------------------------------------------------------
# Synonym map: canonical value → accepted synonyms (for search expansion)
# ---------------------------------------------------------------------------

SYNONYMS: dict[str, list[str]] = {
    "Sans-Serif": ["sans serif", "sans", "grotesque", "gothic"],
    "Serif": ["roman"],
    "Blackletter": ["gothic", "old english", "textura"],
    "Script": ["cursive", "handwriting", "italic script"],
    "Slab Serif": ["egyptian", "mechanistic", "square serif", "antique"],
    "Monospace": ["fixed-width", "typewriter", "coding", "terminal"],
    "Display": ["titling", "decorative headline"],
    "Decorative": ["ornamental", "novelty"],
    "Old Style": ["humanist serif", "venetian", "garalde"],
    "Transitional": ["realist serif", "baroque"],
    "Modern": ["didone", "neoclassical serif", "rational"],
    "Geometric Sans": ["geometric", "constructivist"],
    "Humanist Sans": ["humanist"],
    "Grotesque": ["grotesk", "gothic sans"],
    "Neo-Grotesque": ["realist sans", "transitional sans"],
    "Casual Script": ["casual", "informal script"],
    "Formal Script": ["copperplate script", "engraved script"],
    "Victorian": ["victorian era", "19th century"],
    "Art Deco": ["art deco", "deco", "moderne"],
    "Art Nouveau": ["art nouveau", "jugendstil", "nouveau"],
    "Bauhaus": ["constructivism", "modernist"],
    "Mid-Century Modern": ["mid century", "mcm", "atomic age"],
    "Digital": ["computer age", "digital era"],
    "Public Domain": ["pd", "copyright free"],
    "Open Font License": ["ofl", "libre font", "free font"],
}

# ---------------------------------------------------------------------------
# Field configuration: cardinality metadata for each taxonomy dimension
# ---------------------------------------------------------------------------

FIELD_CONFIG: dict[str, dict] = {
    "style": {
        "label": "Style",
        "values": STYLES,
        "cardinality": "single",
        "required": False,
        "filterable": True,
        "sortable": True,
    },
    "genre": {
        "label": "Genre",
        "values": GENRES,
        "cardinality": "single",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
    "themes": {
        "label": "Themes",
        "values": THEMES,
        "cardinality": "multi",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
    "moods": {
        "label": "Moods",
        "values": MOODS,
        "cardinality": "multi",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
    "font_category": {
        "label": "Category",
        "values": CATEGORIES,
        "cardinality": "single",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
    "use_cases": {
        "label": "Use Cases",
        "values": USE_CASES,
        "cardinality": "multi",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
    "era": {
        "label": "Era",
        "values": ERAS,
        "cardinality": "single",
        "required": False,
        "filterable": True,
        "sortable": True,
    },
    "origin_context": {
        "label": "Origin Context",
        "values": ORIGIN_CONTEXTS,
        "cardinality": "single",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
    "construction_traits": {
        "label": "Construction Traits",
        "values": CONSTRUCTION_TRAITS,
        "cardinality": "multi",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
    "visual_traits": {
        "label": "Visual Traits",
        "values": VISUAL_TRAITS,
        "cardinality": "multi",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
    "restoration_status": {
        "label": "Restoration Status",
        "values": RESTORATION_STATUSES,
        "cardinality": "single",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
    "source_type": {
        "label": "Source Type",
        "values": SOURCE_TYPES,
        "cardinality": "single",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
    "rights_status": {
        "label": "Rights Status",
        "values": RIGHTS_STATUSES,
        "cardinality": "single",
        "required": False,
        "filterable": True,
        "sortable": False,
    },
}


def get_taxonomy() -> dict[str, list[str]]:
    """Return the full taxonomy as a dictionary.

    Includes all canonical dimension value lists for use in API responses,
    filter menus, and validation.
    """
    return {
        "styles": STYLES,
        "genres": GENRES,
        "themes": THEMES,
        "moods": MOODS,
        "categories": CATEGORIES,
        "use_cases": USE_CASES,
        "eras": ERAS,
        "origin_contexts": ORIGIN_CONTEXTS,
        "construction_traits": CONSTRUCTION_TRAITS,
        "visual_traits": VISUAL_TRAITS,
        "restoration_statuses": RESTORATION_STATUSES,
        "source_types": SOURCE_TYPES,
        "rights_statuses": RIGHTS_STATUSES,
    }


def get_hierarchy() -> dict[str, list[str]]:
    """Return the style→genre parent-child hierarchy."""
    return HIERARCHY


def get_synonyms() -> dict[str, list[str]]:
    """Return the synonym map for search expansion."""
    return SYNONYMS


def get_field_config() -> dict[str, dict]:
    """Return field configuration (cardinality, labels, filterability)."""
    return FIELD_CONFIG


def expand_synonyms(term: str) -> list[str]:
    """Return all known synonyms for *term* (case-insensitive lookup).

    The returned list includes the canonical form plus all synonyms so that
    callers can build OR-queries for search expansion.
    """
    term_lower = term.lower()
    for canonical, syns in SYNONYMS.items():
        if canonical.lower() == term_lower or term_lower in [s.lower() for s in syns]:
            return [canonical, *syns]
    return [term]
