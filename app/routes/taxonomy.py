"""Taxonomy routes – expose predefined font styles, themes, and categories."""

from fastapi import APIRouter

from app.taxonomy import get_taxonomy

router = APIRouter(prefix="/api/taxonomy", tags=["taxonomy"])


@router.get("/", summary="Get font taxonomy")
def taxonomy() -> dict[str, list[str]]:
    """Return the predefined lists of styles, themes, and categories."""
    return get_taxonomy()
