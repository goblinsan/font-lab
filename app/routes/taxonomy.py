"""Taxonomy routes – expose predefined font styles, themes, and categories."""

from fastapi import APIRouter

from app.taxonomy import get_field_config, get_hierarchy, get_synonyms, get_taxonomy

router = APIRouter(prefix="/api/taxonomy", tags=["taxonomy"])


@router.get("/", summary="Get font taxonomy")
def taxonomy() -> dict[str, list[str]]:
    """Return all predefined taxonomy dimension value lists."""
    return get_taxonomy()


@router.get("/hierarchy", summary="Get taxonomy style-genre hierarchy")
def taxonomy_hierarchy() -> dict[str, list[str]]:
    """Return the parent-child hierarchy of style families and their genres.

    Use this to build navigation menus and filter trees.
    """
    return get_hierarchy()


@router.get("/synonyms", summary="Get taxonomy synonym map")
def taxonomy_synonyms() -> dict[str, list[str]]:
    """Return the synonym map for search-term expansion.

    Keys are canonical taxonomy values; values are lists of accepted synonyms.
    """
    return get_synonyms()


@router.get("/fields", summary="Get taxonomy field configuration")
def taxonomy_fields() -> dict[str, dict]:
    """Return field configuration for all taxonomy dimensions.

    Each entry includes ``label``, ``values``, ``cardinality``
    (``single`` or ``multi``), ``filterable``, and ``sortable``.
    """
    return get_field_config()
