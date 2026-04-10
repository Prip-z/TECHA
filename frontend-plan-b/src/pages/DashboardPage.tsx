import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Modal } from "../components/Modal";
import { QuickActionRail } from "../components/QuickActionRail";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../lib/api";
import type { AppSettings, EventRecord, EventType } from "../types/models";

function splitEvents(events: EventRecord[]) {
  const now = Date.now();
  const past = events.filter((item) => new Date(item.date).getTime() < now);
  const future = events.filter((item) => new Date(item.date).getTime() >= now);
  return { past, future };
}

export function DashboardPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<AppSettings>({ default_price_per_game: 2500 });
  const [form, setForm] = useState({
    name: "",
    date: new Date().toISOString().slice(0, 16),
    type: "default" as EventType,
    price_per_game: 2500,
  });

  async function load() {
    if (!token) return;
    try {
      const eventsResponse = await api.listDashboardEvents(token);
      setEvents(eventsResponse.items);
      try {
        const settingsResponse = await api.getSettings(token);
        setSettings(settingsResponse);
        setForm((current) => ({
          ...current,
          price_per_game: current.type === "tournament" ? 0 : settingsResponse.default_price_per_game,
        }));
      } catch {
        setSettings({ default_price_per_game: 2500 });
        setForm((current) => ({
          ...current,
          price_per_game: current.type === "tournament" ? 0 : 2500,
        }));
      }
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Не удалось загрузить вечера");
    }
  }

  useEffect(() => {
    void load();
  }, [token]);

  const { past, future } = useMemo(() => splitEvents(events), [events]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    await api.createEvent(token, {
      ...form,
      date: new Date(form.date).toISOString(),
      price_per_game: form.type === "tournament" ? 0 : Number(form.price_per_game),
    });
    setShowCreate(false);
    await load();
  }

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <h1>Вечера</h1>
        <p>Управление вечерами, столами, игроками и ходом игры.</p>
      </section>

      <section className="section-card">
        <div className="section-heading">
          <h2>Прошедшие вечера</h2>
          <button className="ghost-button" onClick={() => navigate("/archive")}>
            Архив
          </button>
        </div>
        <div className="event-grid">
          {past.length === 0 ? <p className="muted-copy">Прошедших вечеров пока нет.</p> : null}
          {past.map((item) => (
            <button key={item.id} className="event-row" onClick={() => navigate(`/events/${item.id}`)}>
              <span>{item.name || "Вечер"}</span>
              <small>{new Date(item.date).toLocaleDateString()}</small>
              <strong>Открыть</strong>
            </button>
          ))}
        </div>
      </section>

      <section className="section-card">
        <div className="section-heading">
          <h2>Ближайшие вечера</h2>
          <button className="ghost-button" onClick={() => setShowCreate(true)}>
            Создать
          </button>
        </div>
        <div className="event-grid">
          {future.length === 0 ? <p className="muted-copy">Запланированных вечеров пока нет.</p> : null}
          {future.map((item) => (
            <button key={item.id} className="event-row" onClick={() => navigate(`/events/${item.id}`)}>
              <span>{item.name || "Вечер"}</span>
              <small>{new Date(item.date).toLocaleDateString()}</small>
              <strong>План</strong>
            </button>
          ))}
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <QuickActionRail onExport={() => navigate("/archive")} />

      {showCreate ? (
        <Modal title="Создать вечер" onClose={() => setShowCreate(false)}>
          <form className="form-grid" onSubmit={handleCreate}>
            <label>
              <span>Тип</span>
              <select
                value={form.type}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    type: event.target.value as "default" | "tournament",
                    price_per_game: event.target.value === "tournament" ? 0 : settings.default_price_per_game,
                  }))
                }
              >
                <option value="default">Обычный</option>
                <option value="tournament">Турнир</option>
              </select>
            </label>
            <label>
              <span>Название</span>
              <input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
            </label>
            <label>
              <span>Цена</span>
              <input
                type="number"
                value={form.price_per_game}
                disabled={form.type === "tournament"}
                onChange={(event) => setForm((current) => ({ ...current, price_per_game: Number(event.target.value) }))}
              />
              <small>Цена по умолчанию: {settings.default_price_per_game} ₽</small>
            </label>
            <label>
              <span>Дата</span>
              <input type="datetime-local" value={form.date} onChange={(event) => setForm((current) => ({ ...current, date: event.target.value }))} />
            </label>
            <button className="primary-button" type="submit">
              Сохранить
            </button>
          </form>
        </Modal>
      ) : null}
    </div>
  );
}
