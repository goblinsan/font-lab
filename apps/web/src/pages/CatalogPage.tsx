import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import {
  listCatalog,
  searchCatalog,
  uploadSample,
  type CatalogEntry,
} from "../api";
import styles from "./CatalogPage.module.css";

export default function CatalogPage() {
  const [entries, setEntries] = useState<CatalogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setLoading(true);
    const promise = query
      ? searchCatalog(query)
      : listCatalog(page, 24);
    promise
      .then((res) => {
        setEntries(res.items);
        setTotal(res.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [page, query]);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    const name = file.name.replace(/\.[^.]+$/, "");
    await uploadSample(file, name);
    fileRef.current!.value = "";
    setPage(1);
    setQuery("");
  }

  return (
    <div>
      <div className={styles.toolbar}>
        <h1>Catalog</h1>
        <input
          type="search"
          placeholder="Search fonts…"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setPage(1);
          }}
          className={styles.search}
        />
        <form onSubmit={handleUpload} className={styles.upload}>
          <input type="file" ref={fileRef} accept="image/*" required />
          <button type="submit">Upload</button>
        </form>
      </div>

      {loading ? (
        <p className={styles.muted}>Loading…</p>
      ) : entries.length === 0 ? (
        <p className={styles.muted}>No fonts found.</p>
      ) : (
        <>
          <div className={styles.grid}>
            {entries.map((e) => (
              <Link
                key={e.id}
                to={`/samples/${e.id}`}
                className={styles.card}
              >
                <div className={styles.cardName}>{e.name}</div>
                <div className={styles.cardMeta}>
                  {e.style ?? "—"} · {e.glyph_count} glyphs
                </div>
              </Link>
            ))}
          </div>
          <div className={styles.pagination}>
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Prev
            </button>
            <span>
              Page {page} of {Math.max(1, Math.ceil(total / 24))}
            </span>
            <button
              disabled={page * 24 >= total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
