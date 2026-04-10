import type { FormEvent } from "react";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loginValue, setLoginValue] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(loginValue, password);
      navigate((location.state as { from?: string } | null)?.from ?? "/");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Ошибка входа");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="brand brand-login">
          <span className="brand-mark">M</span>
          <span className="brand-copy">
            <strong>Mafia</strong>
            <small>организатор</small>
          </span>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>Логин</span>
            <input value={loginValue} onChange={(event) => setLoginValue(event.target.value)} placeholder="superadmin" />
          </label>
          <label>
            <span>Пароль</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Введите пароль"
            />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button className="primary-button" disabled={submitting} type="submit">
            {submitting ? "Входим..." : "Войти"}
          </button>
        </form>
      </div>
    </div>
  );
}
