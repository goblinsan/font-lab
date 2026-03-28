"""API key management endpoints – v1.

Exposes:

* ``POST /api/v1/keys``       — provision a new API key
* ``GET  /api/v1/keys``       — list all keys (admin)
* ``DELETE /api/v1/keys/{id}`` — revoke a key
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiKey
from app.schemas import ApiKeyCreate, ApiKeyResponse

router = APIRouter(prefix="/api/v1/keys", tags=["v1 auth"])


@router.post(
    "",
    response_model=ApiKeyResponse,
    status_code=201,
    summary="Provision a new API key",
)
def create_api_key(payload: ApiKeyCreate, db: Session = Depends(get_db)):
    """Create and store a new API key for *owner* with the given *scope*.

    Scopes:
    - ``read``  — read-only access to catalog, search, preview, and similarity
    - ``write`` — read + ability to upload and modify font records
    - ``admin`` — full access including key management
    """
    raw_key = ApiKey.generate()
    api_key = ApiKey(
        key=raw_key,
        owner=payload.owner,
        scope=payload.scope,
        rate_limit=payload.rate_limit,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


@router.get(
    "",
    response_model=list[ApiKeyResponse],
    summary="List all API keys (admin)",
)
def list_api_keys(db: Session = Depends(get_db)):
    """Return all provisioned API keys."""
    return db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()


@router.delete(
    "/{key_id}",
    status_code=204,
    summary="Revoke an API key",
)
def revoke_api_key(key_id: int, db: Session = Depends(get_db)):
    """Deactivate the API key identified by *key_id*."""
    api_key = db.get(ApiKey, key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    api_key.is_active = False
    db.commit()
