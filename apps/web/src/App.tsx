import { Navigate, Route, Routes } from "react-router-dom";
import { GamePage } from "./pages/GamePage";
import { AdminPage } from "./pages/AdminPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<GamePage />} />
      <Route path="/admin" element={<AdminPage />} />
      <Route path="/admin/:secret" element={<AdminPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}


