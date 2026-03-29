import { useEffect, useState } from "react";
import { listKeys, createKey, revokeKey, type ApiKey } from "../api";
import styles from "./AdminPage.module.css";

export default function AdminPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [label, setLabel] = useState("");
  const [role, setRole] = useState("read");
  const [newKeySecret, setNewKeySecret] = useState<string | null>(null);

  useEffect(() => {
    listKeys().then(setKeys).catch(console.error);
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const result = await createKey(label, role);
    setNewKeySecret(result.key);
    setLabel("");
    const updated = await listKeys();
    setKeys(updated);
  }

  async function handleRevoke(id: string) {
    if (!confirm("Revoke this key?")) return;
    await revokeKey(id);
    const updated = await listKeys();
    setKeys(updated);
  }

  return (
    <div>
      <h1 className={styles.title}>Admin — API Keys</h1>

      <form onSubmit={handleCreate} className={styles.form}>
        <input
          placeholder="Key label"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          required
          className={styles.input}
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className={styles.select}
        >
          <option value="read">Read</option>
          <option value="write">Write</option>
          <option value="admin">Admin</option>
        </select>
        <button type="submit" className={styles.createBtn}>
          Create Key
        </button>
      </form>

      {newKeySecret && (
        <div className={styles.secret}>
          <strong>New key created — copy it now:</strong>
          <code>{newKeySecret}</code>
          <button onClick={() => setNewKeySecret(null)}>Dismiss</button>
        </div>
      )}

      <table className={styles.table}>
        <thead>
          <tr>
            <th>Label</th>
            <th>Prefix</th>
            <th>Role</th>
            <th>Created</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {keys.map((k) => (
            <tr key={k.id}>
              <td>{k.label}</td>
              <td>
                <code>{k.key_prefix}…</code>
              </td>
              <td>{k.role}</td>
              <td>{new Date(k.created_at).toLocaleDateString()}</td>
              <td>{k.revoked_at ? "Revoked" : "Active"}</td>
              <td>
                {!k.revoked_at && (
                  <button
                    onClick={() => handleRevoke(k.id)}
                    className={styles.revokeBtn}
                  >
                    Revoke
                  </button>
                )}
              </td>
            </tr>
          ))}
          {keys.length === 0 && (
            <tr>
              <td colSpan={6} className={styles.muted}>
                No API keys yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
