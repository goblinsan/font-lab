"""FastAPI application entry point for font-lab."""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import create_tables
from app.routes.catalog import router as catalog_router
from app.routes.glyphs import router as glyphs_router
from app.routes.images import router as images_router
from app.routes.integrations import router as integrations_router
from app.routes.reconstruction import router as reconstruction_router
from app.routes.taxonomy import router as taxonomy_router
from app.routes.editor import router as editor_router
from app.routes.v1.catalog import router as v1_catalog_router
from app.routes.v1.keys import router as v1_keys_router

app = FastAPI(
    title="font-lab",
    description="Font sample ingestion and management API",
    version="1.0.0",
)

# Create DB tables on startup
create_tables()

# Mount static files (frontend) and uploaded images
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Register API routes
app.include_router(images_router)
app.include_router(glyphs_router)
app.include_router(reconstruction_router)
app.include_router(taxonomy_router)
app.include_router(catalog_router)
app.include_router(integrations_router)
app.include_router(editor_router)

# v1 versioned API
app.include_router(v1_catalog_router)
app.include_router(v1_keys_router)


@app.get("/", include_in_schema=False)
def index():
    """Serve the frontend SPA."""
    return FileResponse("app/static/index.html")
