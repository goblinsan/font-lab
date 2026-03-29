import styles from "./BuildsPage.module.css";

export default function BuildsPage() {
  return (
    <div>
      <h1 className={styles.title}>Builds</h1>
      <p className={styles.muted}>
        Build history will appear here once font exports are run.
      </p>
    </div>
  );
}
