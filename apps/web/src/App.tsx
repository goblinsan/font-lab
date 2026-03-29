import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import CatalogPage from "./pages/CatalogPage";
import SampleDetailPage from "./pages/SampleDetailPage";
import GlyphReviewPage from "./pages/GlyphReviewPage";
import BuildsPage from "./pages/BuildsPage";
import AdminPage from "./pages/AdminPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<CatalogPage />} />
        <Route path="samples/:id" element={<SampleDetailPage />} />
        <Route path="samples/:id/glyphs" element={<GlyphReviewPage />} />
        <Route path="builds" element={<BuildsPage />} />
        <Route path="admin" element={<AdminPage />} />
      </Route>
    </Routes>
  );
}
