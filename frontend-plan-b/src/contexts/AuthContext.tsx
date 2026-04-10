import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useState } from "react";

import { api } from "../lib/api";
import { clearSession, loadSession, saveSession } from "../lib/storage";
import type { StaffUser } from "../types/models";

interface AuthContextValue {
  token: string | null;
  user: StaffUser | null;
  loading: boolean;
  login: (login: string, password: string) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<StaffUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const session = loadSession();
    if (!session) {
      setLoading(false);
      return;
    }

    setToken(session.token);
    setUser(session.user);
    api
      .getMe(session.token)
      .then((nextUser) => {
        setUser(nextUser);
        saveSession(session.token, nextUser);
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(loginValue: string, password: string) {
    const result = await api.login(loginValue, password);
    const nextUser = await api.getMe(result.access_token);
    setToken(result.access_token);
    setUser(nextUser);
    saveSession(result.access_token, nextUser);
  }

  function logout() {
    setToken(null);
    setUser(null);
    clearSession();
  }

  async function refreshMe() {
    if (!token) {
      return;
    }
    const nextUser = await api.getMe(token);
    setUser(nextUser);
    saveSession(token, nextUser);
  }

  return (
    <AuthContext.Provider value={{ token, user, loading, login, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
