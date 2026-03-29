import { NavLink, Outlet } from "react-router-dom";
import styles from "./Layout.module.css";

export default function Layout() {
  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <NavLink to="/" className={styles.logo}>
          Font Lab
        </NavLink>
        <nav className={styles.nav}>
          <NavLink to="/" end className={navClass}>
            Catalog
          </NavLink>
          <NavLink to="/builds" className={navClass}>
            Builds
          </NavLink>
          <NavLink to="/admin" className={navClass}>
            Admin
          </NavLink>
        </nav>
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}

function navClass({ isActive }: { isActive: boolean }) {
  return isActive ? "nav-link active" : "nav-link";
}
