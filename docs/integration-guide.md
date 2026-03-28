# font-lab Developer Platform — Integration Guide

This document describes how to integrate with the **font-lab** API v1 to search
fonts, fetch metadata, render previews, and resolve font assets from external
applications such as **Vizail** and **kulrs**.

---

## Table of Contents

1. [Base URL and versioning](#1-base-url-and-versioning)
2. [Authentication and API keys](#2-authentication-and-api-keys)
3. [Rate limiting](#3-rate-limiting)
4. [Error model](#4-error-model)
5. [Font discovery](#5-font-discovery)
6. [Semantic search and similarity](#6-semantic-search-and-similarity)
7. [Preview and specimen rendering](#7-preview-and-specimen-rendering)
8. [Metadata schema reference](#8-metadata-schema-reference)
9. [Integration adapters (Vizail and kulrs)](#9-integration-adapters-vizail-and-kulrs)
10. [SDK starter examples](#10-sdk-starter-examples)
11. [Compatibility and deprecation policy](#11-compatibility-and-deprecation-policy)

---

## 1. Base URL and versioning

All v1 endpoints are prefixed with `/api/v1/`.  Older unversioned routes
(`/api/catalog/`, `/api/integrations/`) remain available for backward
compatibility.

```
https://<host>/api/v1/
```

The API version is communicated via the URL path, not via HTTP headers, so
clients can hardcode the version segment in their base URL.

---

## 2. Authentication and API keys

### Provisioning a key

```http
POST /api/v1/keys
Content-Type: application/json

{
  "owner": "my-app",
  "scope": "read",
  "rate_limit": 1000
}
```

**Response** (201 Created):

```json
{
  "id": 1,
  "key": "abc123...",
  "owner": "my-app",
  "scope": "read",
  "is_active": true,
  "rate_limit": 1000,
  "created_at": "2026-03-28T12:00:00Z"
}
```

Store the `key` value securely — it is only shown once.

### Sending the key

Include the key in every request via the `X-API-Key` header:

```http
GET /api/v1/fonts
X-API-Key: abc123...
```

### Scopes

| Scope   | Permissions                                                   |
|---------|---------------------------------------------------------------|
| `read`  | Read-only: catalog, search, preview, similarity               |
| `write` | Read + upload and modify font records                         |
| `admin` | Full access including key management (`/api/v1/keys`)         |

### Revoking a key

```http
DELETE /api/v1/keys/{key_id}
```

Returns `204 No Content`.  The key's `is_active` flag is set to `false`.

---

## 3. Rate limiting

Each API key has a configurable hourly quota (`rate_limit`, default 1 000
requests/hour).  Unauthenticated callers share a pool of 100 requests/hour.

When the quota is exceeded the API returns:

```http
HTTP/1.1 429 Too Many Requests

{
  "detail": "Rate limit exceeded. Maximum 1000 requests per hour."
}
```

Use exponential back-off and retry after waiting until the rolling 1-hour
window resets.

---

## 4. Error model

All API errors follow a consistent JSON envelope:

```json
{
  "detail": "Font not found"
}
```

| Status | Meaning                                |
|--------|----------------------------------------|
| 400    | Invalid request parameters             |
| 401    | Missing or revoked API key             |
| 403    | Insufficient scope                     |
| 404    | Resource not found                     |
| 422    | Validation error (request body)        |
| 429    | Rate limit exceeded                    |
| 500    | Internal server error                  |

---

## 5. Font discovery

### List all fonts (paginated)

```http
GET /api/v1/fonts
    ?page=1
    &per_page=20
    &sort=font_name
    &order=asc
    &style=Serif
    &theme=Vintage
    &era=1920s
X-API-Key: <key>
```

**Query parameters:**

| Parameter      | Type    | Default      | Description                                    |
|----------------|---------|--------------|------------------------------------------------|
| `page`         | int ≥ 1 | `1`          | Page number                                    |
| `per_page`     | 1–100   | `20`         | Items per page                                 |
| `sort`         | string  | `uploaded_at`| `font_name`, `uploaded_at`, `style`, `theme`, `era`, `confidence` |
| `order`        | string  | `desc`       | `asc` or `desc`                                |
| `font_category`| string  | –            | Partial, case-insensitive match                |
| `style`        | string  | –            | Partial, case-insensitive match                |
| `theme`        | string  | –            | Partial, case-insensitive match                |
| `era`          | string  | –            | Partial, case-insensitive match                |

**Response:**

```json
{
  "total": 42,
  "page": 1,
  "per_page": 20,
  "items": [
    {
      "id": 1,
      "font_name": "Helvetica",
      "font_category": "Sans-Serif",
      "style": "Sans-Serif",
      "theme": "Modern",
      "era": "1950s",
      "provenance": "Swiss foundry",
      "confidence": 0.95,
      "tags": ["clean", "corporate"],
      "preview_url": "/uploads/abc123.png",
      "glyph_count": 52,
      ...
    }
  ]
}
```

### Get a single font

```http
GET /api/v1/fonts/{id}
X-API-Key: <key>
```

Returns the full metadata record including `era`, `provenance`, `confidence`,
`preview_url`, and `glyph_count`.

---

## 6. Semantic search and similarity

### Text and trait search

```http
GET /api/v1/fonts/search
    ?q=geometric+modern
    &style=Sans-Serif
    &tag=minimal
    &era=1960s
    &page=1
    &per_page=10
X-API-Key: <key>
```

`q` is matched against `font_name`, `font_category`, `style`, `theme`, `era`,
and `notes`.  Additional narrow filters may be combined with `q`.

The response uses the same paginated envelope as `/api/v1/fonts`.

### Similarity ranking

```http
GET /api/v1/fonts/{id}/similar
    ?limit=10
    &min_score=0.2
X-API-Key: <key>
```

Returns an array of fonts ranked by similarity to `{id}`.  Similarity is
computed from:

| Dimension         | Weight |
|-------------------|--------|
| Style match       | 30 %   |
| Theme match       | 25 %   |
| Category match    | 20 %   |
| Era match         | 10 %   |
| Tag Jaccard       | 15 %   |

**Response:**

```json
[
  {
    "id": 7,
    "font_name": "Arial",
    "style": "Sans-Serif",
    "theme": "Modern",
    "era": "1980s",
    "tags": ["corporate"],
    "preview_url": "/uploads/def456.png",
    "similarity_score": 0.75
  }
]
```

**Parameters:**

| Parameter   | Default | Description                          |
|-------------|---------|--------------------------------------|
| `limit`     | 10      | Maximum number of results (max 50)   |
| `min_score` | 0.0     | Minimum similarity threshold [0, 1]  |

---

## 7. Preview and specimen rendering

### Embeddable preview config

```http
GET /api/v1/fonts/{id}/preview
X-API-Key: <key>
```

**Response:**

```json
{
  "sample_id": 1,
  "font_name": "Helvetica",
  "preview_url": "/uploads/abc123.png",
  "specimen_url": "/api/samples/1/print-preview",
  "embed_url": "/api/samples/1/print-preview?font_size=48",
  "available_chars": ["A", "B", "C", ...],
  "suggested_text": "The quick brown fox"
}
```

### HTML print preview

```http
GET /api/samples/{id}/print-preview
    ?text=Hello+World
    &font_size=64
```

Returns a fully-rendered HTML page showing the font in three contexts:
white background, dark background (decal), and kraft background (packaging).

### Embed in an iframe

```html
<iframe
  src="https://<host>/api/samples/1/print-preview?text=Brand+Name&font_size=72"
  width="800"
  height="400"
  style="border:none">
</iframe>
```

---

## 8. Metadata schema reference

### FontSample fields

| Field               | Type            | Description                                           |
|---------------------|-----------------|-------------------------------------------------------|
| `id`                | int             | Auto-incremented primary key                          |
| `font_name`         | string \| null  | Human-readable font name                              |
| `font_category`     | string \| null  | Intended use category (e.g. Body Text, Headline)      |
| `style`             | string \| null  | Visual style (e.g. Serif, Sans-Serif, Display)        |
| `theme`             | string \| null  | Aesthetic theme (e.g. Modern, Vintage, Playful)       |
| `era`               | string \| null  | Historical period (e.g. 1920s, Art Deco, Digital)     |
| `provenance`        | string \| null  | Origin or attribution notes                           |
| `confidence`        | float \| null   | Identification confidence score [0.0 – 1.0]           |
| `tags`              | string[]        | Free-form labels                                      |
| `notes`             | string \| null  | Free-text notes                                       |
| `source`            | string \| null  | Source reference or URL                               |
| `restoration_notes` | string \| null  | Notes about digitisation or restoration               |
| `preview_url`       | string          | URL of the uploaded image                             |
| `glyph_count`       | int             | Number of extracted glyphs                            |
| `uploaded_at`       | ISO 8601 string | Upload timestamp (UTC)                                |

### Taxonomy values

Retrieve canonical taxonomy values:

```http
GET /api/taxonomy/
```

Returns:

```json
{
  "styles": ["Serif", "Sans-Serif", "Monospace", "Display", ...],
  "themes": ["Modern", "Vintage", "Elegant", "Playful", ...],
  "categories": ["Body Text", "Headline", "Logo", "UI", ...]
}
```

---

## 9. Integration adapters (Vizail and kulrs)

font-lab ships with purpose-built adapters for Vizail and kulrs that expose
the catalog in partner-specific formats.

### Vizail adapter

```http
GET /api/integrations/vizail
```

```json
{
  "fonts": [
    {
      "id": 1,
      "name": "Helvetica",
      "category": "Sans-Serif",
      "style": "Sans-Serif",
      "theme": "Modern",
      "tags": ["clean"],
      "preview_url": "/uploads/abc123.png",
      "glyph_count": 52
    }
  ]
}
```

### kulrs adapter

```http
GET /api/integrations/kulrs
```

```json
[
  {
    "id": 1,
    "name": "Helvetica",
    "traits": {
      "category": "Sans-Serif",
      "style": "Sans-Serif",
      "theme": "Modern"
    },
    "tags": ["clean"],
    "preview_url": "/uploads/abc123.png"
  }
]
```

---

## 10. SDK starter examples

### Python

```python
import httpx

BASE_URL = "https://fontlab.example.com"
API_KEY = "your-api-key-here"

headers = {"X-API-Key": API_KEY}


def search_fonts(q: str, style: str | None = None, era: str | None = None):
    """Search the font catalog by free-text query and optional filters."""
    params: dict = {"q": q}
    if style:
        params["style"] = style
    if era:
        params["era"] = era
    resp = httpx.get(f"{BASE_URL}/api/v1/fonts/search", params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()["items"]


def get_similar_fonts(font_id: int, min_score: float = 0.3, limit: int = 5):
    """Fetch fonts similar to the given font_id."""
    resp = httpx.get(
        f"{BASE_URL}/api/v1/fonts/{font_id}/similar",
        params={"min_score": min_score, "limit": limit},
        headers=headers,
    )
    resp.raise_for_status()
    return resp.json()


def get_preview_config(font_id: int):
    """Retrieve the embeddable preview configuration for a font."""
    resp = httpx.get(f"{BASE_URL}/api/v1/fonts/{font_id}/preview", headers=headers)
    resp.raise_for_status()
    return resp.json()


# --- Example usage ---
if __name__ == "__main__":
    fonts = search_fonts("geometric", style="Sans-Serif", era="1960s")
    for font in fonts:
        print(f"{font['font_name']} – score: {font.get('confidence')}")

    if fonts:
        similar = get_similar_fonts(fonts[0]["id"])
        print("Similar fonts:", [s["font_name"] for s in similar])

        config = get_preview_config(fonts[0]["id"])
        print("Embed URL:", config["embed_url"])
```

### JavaScript / TypeScript

```typescript
const BASE_URL = "https://fontlab.example.com";
const API_KEY = "your-api-key-here";

const headers = { "X-API-Key": API_KEY };

async function searchFonts(
  q: string,
  style?: string,
  era?: string
): Promise<FontEntry[]> {
  const params = new URLSearchParams({ q });
  if (style) params.append("style", style);
  if (era) params.append("era", era);

  const resp = await fetch(
    `${BASE_URL}/api/v1/fonts/search?${params}`,
    { headers }
  );
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const data = await resp.json();
  return data.items as FontEntry[];
}

async function getSimilarFonts(
  fontId: number,
  minScore = 0.3,
  limit = 5
): Promise<SimilarFontEntry[]> {
  const params = new URLSearchParams({
    min_score: String(minScore),
    limit: String(limit),
  });
  const resp = await fetch(
    `${BASE_URL}/api/v1/fonts/${fontId}/similar?${params}`,
    { headers }
  );
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

async function getPreviewConfig(fontId: number): Promise<PreviewConfig> {
  const resp = await fetch(
    `${BASE_URL}/api/v1/fonts/${fontId}/preview`,
    { headers }
  );
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

// --- Example usage ---
(async () => {
  const fonts = await searchFonts("vintage", "Serif", "1930s");
  console.log("Found:", fonts.map((f) => f.font_name));

  if (fonts.length > 0) {
    const similar = await getSimilarFonts(fonts[0].id);
    console.log("Similar:", similar.map((s) => s.font_name));

    const config = await getPreviewConfig(fonts[0].id);
    console.log("Embed URL:", config.embed_url);
  }
})();
```

### Vizail integration

```javascript
// Fetch the full Vizail-formatted catalog and register fonts
const resp = await fetch(`${BASE_URL}/api/integrations/vizail`, { headers });
const { fonts } = await resp.json();

vizail.registerFonts(fonts.map((f) => ({
  id: f.id,
  label: f.name,
  previewUrl: f.preview_url,
  traits: { style: f.style, theme: f.theme, category: f.category },
})));
```

### kulrs integration

```javascript
// Fetch kulrs-formatted catalog and populate the font picker
const resp = await fetch(`${BASE_URL}/api/integrations/kulrs`, { headers });
const fonts = await resp.json();

kulrs.loadFontLibrary(fonts.map((f) => ({
  uid: f.id,
  displayName: f.name,
  traits: f.traits,
  tags: f.tags,
  thumbnail: f.preview_url,
})));
```

---

## 11. Compatibility and deprecation policy

- **v1** is the current stable API surface.
- Breaking changes will be introduced under a new version prefix (e.g. `/api/v2/`).
- The unversioned routes (`/api/catalog/`, `/api/integrations/`) are considered
  legacy and may be deprecated in a future major version.
- Deprecated endpoints will be flagged with an `X-Deprecated` response header
  at least one release cycle before removal.
