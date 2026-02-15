import { Routes, Route, Navigate } from "react-router-dom";
import HomePage from "./pages/HomePage";
import SearchPage from "./pages/SearchPage";
import TaggingPage from "./pages/TaggingPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/search" element={<SearchPage />} />
      <Route path="/tag" element={<TaggingPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
