import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { listGlyphs, updateGlyph, deleteGlyph, type Glyph } from "../api";
import styles from "./GlyphReviewPage.module.css";

export default function GlyphReviewPage() {
  const { id } = useParams<{ id: string }>();
  const [glyphs, setGlyphs] = useState<Glyph[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    listGlyphs(id)
      .then(setGlyphs)
      .finally(() => setLoading(false));
  }, [id]);

  const selectedGlyph = glyphs.find((g) => g.id === selected);

  async function handleLabel(glyphId: string, label: string) {
    if (!id) return;
    const updated = await updateGlyph(id, glyphId, { label });
    setGlyphs((prev) => prev.map((g) => (g.id === glyphId ? updated : g)));
  }

  async function handleApprove(glyphId: string) {
    if (!id) return;
    const updated = await updateGlyph(id, glyphId, { status: "approved" });
    setGlyphs((prev) => prev.map((g) => (g.id === glyphId ? updated : g)));
  }

  async function handleReject(glyphId: string) {
    if (!id) return;
    const updated = await updateGlyph(id, glyphId, { status: "rejected" });
    setGlyphs((prev) => prev.map((g) => (g.id === glyphId ? updated : g)));
  }

  async function handleDelete(glyphId: string) {
    if (!id) return;
    await deleteGlyph(id, glyphId);
    setGlyphs((prev) => prev.filter((g) => g.id !== glyphId));
    if (selected === glyphId) setSelected(null);
  }

  if (loading) return <p>Loading glyphs…</p>;

  return (
    <div>
      <Link to={`/samples/${id}`} className={styles.back}>
        ← Sample
      </Link>
      <h1 className={styles.title}>Glyph Review</h1>
      <p className={styles.summary}>
        {glyphs.length} glyphs ·{" "}
        {glyphs.filter((g) => g.status === "approved").length} approved ·{" "}
        {glyphs.filter((g) => g.status === "rejected").length} rejected
      </p>

      <div className={styles.layout}>
        <div className={styles.grid}>
          {glyphs.map((g) => (
            <button
              key={g.id}
              className={`${styles.cell} ${g.id === selected ? styles.cellSelected : ""} ${styles[`status_${g.status}`] ?? ""}`}
              onClick={() => setSelected(g.id)}
              title={g.label ?? g.unicode_char ?? "?"}
            >
              <span className={styles.char}>
                {g.unicode_char ?? g.label ?? "?"}
              </span>
              <span className={styles.dims}>
                {g.w}×{g.h}
              </span>
            </button>
          ))}
        </div>

        {selectedGlyph && (
          <div className={styles.detail}>
            <h2>
              {selectedGlyph.unicode_char ?? selectedGlyph.label ?? "Unknown"}
            </h2>
            <table className={styles.meta}>
              <tbody>
                <tr>
                  <th>Position</th>
                  <td>
                    ({selectedGlyph.x}, {selectedGlyph.y})
                  </td>
                </tr>
                <tr>
                  <th>Size</th>
                  <td>
                    {selectedGlyph.w} × {selectedGlyph.h}
                  </td>
                </tr>
                <tr>
                  <th>Confidence</th>
                  <td>
                    {selectedGlyph.confidence != null
                      ? `${(selectedGlyph.confidence * 100).toFixed(0)}%`
                      : "—"}
                  </td>
                </tr>
                <tr>
                  <th>Status</th>
                  <td>{selectedGlyph.status}</td>
                </tr>
              </tbody>
            </table>

            <div className={styles.labelRow}>
              <input
                placeholder="Label"
                defaultValue={selectedGlyph.label ?? ""}
                onBlur={(e) => handleLabel(selectedGlyph.id, e.target.value)}
                className={styles.labelInput}
              />
            </div>

            <div className={styles.btnRow}>
              <button
                onClick={() => handleApprove(selectedGlyph.id)}
                className={styles.approve}
              >
                Approve
              </button>
              <button
                onClick={() => handleReject(selectedGlyph.id)}
                className={styles.reject}
              >
                Reject
              </button>
              <button
                onClick={() => handleDelete(selectedGlyph.id)}
                className={styles.delete}
              >
                Delete
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
