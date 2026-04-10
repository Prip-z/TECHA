import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { api } from "../lib/api";
import type { EventRecord } from "../types/models";

export function ArchivePage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!token) return;
    api.listAllEvents(token).then((response) => setEvents(response.items));
  }, [token]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return events;
    return events.filter((item) => {
      const readableDate = new Date(item.date).toLocaleDateString().toLowerCase();
      return item.name.toLowerCase().includes(normalized) || readableDate.includes(normalized);
    });
  }, [events, query]);

  return (
    <div className="page-stack">
      <section className="section-card">
        <div className="section-heading">
          <h2>Архив</h2>
          <button className="ghost-button" onClick={() => navigate("/")}>
            Назад
          </button>
        </div>
        <input
          className="search-input"
          placeholder="Поиск по дате или названию"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <div className="archive-list">
          {filtered.map((item) => (
            <button key={item.id} className="event-row" onClick={() => navigate(`/events/${item.id}`)}>
              <span>{item.name}</span>
              <small>{new Date(item.date).toLocaleString()}</small>
              <strong>{item.type === "tournament" ? "Турнир" : "Обычный"}</strong>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
