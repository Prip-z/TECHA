import type { ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

const roleLabel: Record<string, string> = {
  super_admin: "супер-админ",
  admin: "админ",
  host: "ведущий",
};

function topTitle(pathname: string) {
  if (pathname.startsWith("/archive")) return "Архив";
  if (pathname.startsWith("/admin")) return "Управление";
  if (pathname.startsWith("/events/")) return "Вечер";
  if (pathname.startsWith("/games/")) return "Бланк игры";
  return "Текущий вечер";
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="ghost-nav" onClick={() => navigate("/archive")}>
          Архив
        </button>
        <Link className="brand" to="/">
          <span className="brand-mark">M</span>
          <span className="brand-copy">
            <strong>Mafia</strong>
            <small>{topTitle(location.pathname)}</small>
          </span>
        </Link>
        <button
          className="ghost-nav"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          Выйти
        </button>
      </header>

      <main className="screen">{children}</main>

      <footer className="footer-bar">
        <button className="footer-chip" onClick={() => navigate("/")}>
          Вечера
        </button>
        <button className="footer-chip" onClick={() => navigate("/admin")}>
          {user?.role === "host" ? "Инструменты" : "Админка"}
        </button>
        <div className="footer-profile">
          <span>{user?.name ?? "Гость"}</span>
          <small>{user?.role ? roleLabel[user.role] ?? user.role : ""}</small>
        </div>
      </footer>
    </div>
  );
}
