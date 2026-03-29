const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ---- Types ----

export interface Sample {
  id: string;
  name: string;
  slug: string;
  original_filename: string | null;
  content_type: string | null;
  status: string;
  style: string | null;
  category: string | null;
  created_at: string;
  updated_at: string;
}

export interface Glyph {
  id: string;
  sample_id: string;
  unicode_char: string | null;
  label: string | null;
  x: number;
  y: number;
  w: number;
  h: number;
  confidence: number | null;
  status: string;
}

export interface CatalogEntry {
  id: string;
  name: string;
  slug: string;
  style: string | null;
  category: string | null;
  glyph_count: number;
  created_at: string;
}

export interface ApiKey {
  id: string;
  label: string;
  key_prefix: string;
  role: string;
  created_at: string;
  revoked_at: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

// ---- Samples ----

export async function listSamples(
  page = 1,
  perPage = 20,
): Promise<PaginatedResponse<Sample>> {
  return request(`/samples?page=${page}&per_page=${perPage}`);
}

export async function getSample(id: string): Promise<Sample> {
  return request(`/samples/${encodeURIComponent(id)}`);
}

export async function uploadSample(file: File, name: string): Promise<Sample> {
  const form = new FormData();
  form.append("file", file);
  form.append("name", name);
  return request("/samples", { method: "POST", body: form });
}

export async function updateSample(
  id: string,
  data: Partial<Pick<Sample, "name" | "style" | "category" | "status">>,
): Promise<Sample> {
  return request(`/samples/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteSample(id: string): Promise<void> {
  await fetch(`${BASE}/samples/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

// ---- Glyphs ----

export async function segmentSample(sampleId: string): Promise<void> {
  await request(`/samples/${encodeURIComponent(sampleId)}/segment`, {
    method: "POST",
  });
}

export async function listGlyphs(sampleId: string): Promise<Glyph[]> {
  return request(`/samples/${encodeURIComponent(sampleId)}/glyphs`);
}

export async function getGlyph(
  sampleId: string,
  glyphId: string,
): Promise<Glyph> {
  return request(
    `/samples/${encodeURIComponent(sampleId)}/glyphs/${encodeURIComponent(glyphId)}`,
  );
}

export async function updateGlyph(
  sampleId: string,
  glyphId: string,
  data: Partial<Pick<Glyph, "label" | "unicode_char" | "status">>,
): Promise<Glyph> {
  return request(
    `/samples/${encodeURIComponent(sampleId)}/glyphs/${encodeURIComponent(glyphId)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export async function deleteGlyph(
  sampleId: string,
  glyphId: string,
): Promise<void> {
  await fetch(
    `${BASE}/samples/${encodeURIComponent(sampleId)}/glyphs/${encodeURIComponent(glyphId)}`,
    { method: "DELETE" },
  );
}

export async function getGlyphOutline(
  sampleId: string,
  glyphId: string,
): Promise<string> {
  const res = await fetch(
    `${BASE}/samples/${encodeURIComponent(sampleId)}/glyphs/${encodeURIComponent(glyphId)}/outline`,
  );
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.text();
}

// ---- Catalog ----

export async function listCatalog(
  page = 1,
  perPage = 20,
): Promise<PaginatedResponse<CatalogEntry>> {
  return request(`/catalog?page=${page}&per_page=${perPage}`);
}

export async function searchCatalog(
  q: string,
): Promise<PaginatedResponse<CatalogEntry>> {
  return request(`/catalog/search?q=${encodeURIComponent(q)}`);
}

export async function findSimilar(
  id: string,
  limit = 10,
): Promise<{ id: string; name: string; score: number }[]> {
  return request(
    `/catalog/${encodeURIComponent(id)}/similar?limit=${limit}`,
  );
}

// ---- Keys ----

export async function listKeys(): Promise<ApiKey[]> {
  return request("/keys");
}

export async function createKey(
  label: string,
  role: string,
): Promise<ApiKey & { key: string }> {
  return request("/keys", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label, role }),
  });
}

export async function revokeKey(id: string): Promise<void> {
  await request(`/keys/${encodeURIComponent(id)}/revoke`, { method: "POST" });
}

// ---- Taxonomy ----

export interface TaxonomyDimension {
  name: string;
  label: string;
  terms: { slug: string; label: string }[];
}

export async function listTaxonomy(): Promise<TaxonomyDimension[]> {
  return request("/taxonomy");
}
