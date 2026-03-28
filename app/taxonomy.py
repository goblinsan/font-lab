"""Font taxonomy: predefined styles, themes, and categories."""

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

CATEGORIES: list[str] = [
    "Body Text",
    "Headline",
    "Logo",
    "UI",
    "Poster",
    "Signage",
    "Editorial",
]


def get_taxonomy() -> dict[str, list[str]]:
    """Return the full taxonomy as a dictionary."""
    return {
        "styles": STYLES,
        "themes": THEMES,
        "categories": CATEGORIES,
    }
