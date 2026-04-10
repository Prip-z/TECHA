import type { JSX } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { LoadingScreen } from "../components/LoadingScreen";
import { useAuth } from "../contexts/AuthContext";
import { AdminPage } from "../pages/AdminPage";
import { ArchivePage } from "../pages/ArchivePage";
import { DashboardPage } from "../pages/DashboardPage";
import { EventPage } from "../pages/EventPage";
import { GamePage } from "../pages/GamePage";
import { LoginPage } from "../pages/LoginPage";

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { token, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingScreen label="Восстанавливаем сессию" />;
  }

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}

export function App() {
  const location = useLocation();
  const isLoginPage = location.pathname === "/login";

  if (isLoginPage) {
    return <LoginPage />;
  }

  return (
    <ProtectedRoute>
      <AppShell>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/archive" element={<ArchivePage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/events/:eventId" element={<EventPage />} />
          <Route path="/games/:gameId" element={<GamePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </ProtectedRoute>
  );
}
