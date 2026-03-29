import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  getSample,
  updateSample,
  deleteSample,
  segmentSample,
  type Sample,
} from "../api";
import styles from "./SampleDetailPage.module.css";

export default function SampleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [sample, setSample] = useState<Sample | null>(null);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!id) return;
    getSample(id).then((s) => {
      setSample(s);
      setName(s.name);
    });
  }, [id]);

  if (!sample) return <p>Loading…</p>;

  async function handleSave() {
    if (!id) return;
    setBusy(true);
    const updated = await updateSample(id, { name });
    setSample(updated);
    setEditing(false);
    setBusy(false);
  }

  async function handleSegment() {
    if (!id) return;
    setBusy(true);
    await segmentSample(id);
    setBusy(false);
    navigate(`/samples/${id}/glyphs`);
  }

  async function handleDelete() {
    if (!id || !confirm("Delete this sample?")) return;
    await deleteSample(id);
    navigate("/");
  }

  return (
    <div>
      <Link to="/" className={styles.back}>
        ← Catalog
      </Link>

      <div className={styles.header}>
        {editing ? (
          <div className={styles.editRow}>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={styles.nameInput}
            />
            <button onClick={handleSave} disabled={busy}>
              Save
            </button>
            <button onClick={() => setEditing(false)}>Cancel</button>
          </div>
        ) : (
          <h1 onClick={() => setEditing(true)} className={styles.name}>
            {sample.name}
          </h1>
        )}
      </div>

      <table className={styles.meta}>
        <tbody>
          <tr>
            <th>ID</th>
            <td>{sample.id}</td>
          </tr>
          <tr>
            <th>Slug</th>
            <td>{sample.slug}</td>
          </tr>
          <tr>
            <th>Status</th>
            <td>{sample.status}</td>
          </tr>
          <tr>
            <th>Style</th>
            <td>{sample.style ?? "—"}</td>
          </tr>
          <tr>
            <th>Category</th>
            <td>{sample.category ?? "—"}</td>
          </tr>
          <tr>
            <th>Original file</th>
            <td>{sample.original_filename ?? "—"}</td>
          </tr>
          <tr>
            <th>Created</th>
            <td>{new Date(sample.created_at).toLocaleString()}</td>
          </tr>
        </tbody>
      </table>

      <div className={styles.actions}>
        <button onClick={handleSegment} disabled={busy}>
          Segment Glyphs
        </button>
        <Link to={`/samples/${sample.id}/glyphs`}>
          <button>View Glyphs</button>
        </Link>
        <button
          onClick={handleDelete}
          className={styles.danger}
          disabled={busy}
        >
          Delete
        </button>
      </div>
    </div>
  );
}
