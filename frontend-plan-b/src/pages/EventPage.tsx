import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Modal } from "../components/Modal";
import { QuickActionRail } from "../components/QuickActionRail";
import { useAuth } from "../contexts/AuthContext";
import { useRealtimeRoom } from "../hooks/useRealtimeRoom";
import { api } from "../lib/api";
import type { EventGameItem, EventRecord, EventRosterItem, PlayerRecord, SyncEnvelope, TableRecord } from "../types/models";

const statusLabels: Record<string, string> = {
  preparation: "подготовка",
  voting: "голосование",
  revote: "переголосование",
  shooting: "стрельба",
  testament: "завещание",
  finished: "завершено",
};

export function EventPage() {
  const { token } = useAuth();
  const { eventId } = useParams();
  const navigate = useNavigate();
  const numericEventId = Number(eventId);
  const [eventRecord, setEventRecord] = useState<EventRecord | null>(null);
  const [roster, setRoster] = useState<EventRosterItem[]>([]);
  const [games, setGames] = useState<EventGameItem[]>([]);
  const [tables, setTables] = useState<TableRecord[]>([]);
  const [players, setPlayers] = useState<PlayerRecord[]>([]);
  const [showPlayerModal, setShowPlayerModal] = useState(false);
  const [showGameModal, setShowGameModal] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [search, setSearch] = useState("");
  const [playerForm, setPlayerForm] = useState({ name: "", nick: "", phone: "", social_link: "" });
  const [gameTableId, setGameTableId] = useState<number | null>(null);

  async function load() {
    if (!token || !numericEventId) return;
    const [eventsResponse, playersResponse, gamesResponse, tablesResponse] = await Promise.all([
      api.listAllEvents(token),
      api.listEventPlayers(token, numericEventId),
      api.listEventGames(token, numericEventId),
      api.listTables(token),
    ]);
    setEventRecord(eventsResponse.items.find((item) => item.id === numericEventId) ?? null);
    setRoster(playersResponse);
    setGames(gamesResponse);
    setTables(tablesResponse);
    setGameTableId(tablesResponse[0]?.id ?? null);
  }

  useEffect(() => {
    void load();
  }, [token, numericEventId]);

  useEffect(() => {
    if (!token || !showPlayerModal) return;
    if (!search.trim()) {
      setPlayers([]);
      return;
    }
    api.listPlayers(token, search).then((response) => setPlayers(response.items));
  }, [search, showPlayerModal, token]);

  function handleRealtimeMessage(message: SyncEnvelope) {
    if (message.type === "event_updated") {
      void load();
    }
  }

  useRealtimeRoom(eventId ? `event-${eventId}` : null, token, handleRealtimeMessage);

  const totals = useMemo(() => {
    const totalGames = roster.reduce((sum, item) => sum + item.games_played, 0);
    const totalPaid = roster.reduce((sum, item) => sum + item.paid_amount, 0);
    return { totalGames, totalPaid };
  }, [roster]);

  async function addPlayer(playerId: number) {
    if (!token) return;
    await api.addEventPlayer(token, numericEventId, playerId);
    setShowPlayerModal(false);
    setSearch("");
    setPlayers([]);
    await load();
  }

  async function handleCreatePlayer(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    const created = await api.createPlayer(token, playerForm);
    await addPlayer(created.id);
    setPlayerForm({ name: "", nick: "", phone: "", social_link: "" });
  }

  async function handleCreateGame(event: FormEvent) {
    event.preventDefault();
    if (!token || !gameTableId) return;
    const game = await api.createGame(token, { event_id: numericEventId, table_id: gameTableId });
    setShowGameModal(false);
    await load();
    navigate(`/games/${game.game_id}`);
  }

  async function handleRemovePlayer(playerId: number) {
    if (!token) return;
    await api.removeEventPlayer(token, numericEventId, playerId);
    await load();
  }

  function exportEvent() {
    if (!token) return;
    void api.downloadFile(`/events/${numericEventId}/export`, token, `event-${numericEventId}.xlsx`);
  }

  if (!eventRecord) {
    return <div className="section-card">Загрузка вечера...</div>;
  }

  return (
    <div className="page-stack">
      <section className="hero-panel compact">
        <div>
          <h1>{eventRecord.name || "Вечер"}</h1>
          <p>
            {new Date(eventRecord.date).toLocaleString()} | {eventRecord.type === "tournament" ? "Турнир" : "Обычный"} |{" "}
            {eventRecord.type === "tournament" ? "0 ₽" : `${eventRecord.price_per_game} ₽ / игра`}
          </p>
        </div>
        <button className="ghost-button" onClick={() => navigate("/")}>
          Назад
        </button>
      </section>

      <section className="section-card">
        <div className="section-heading">
          <h2>Игроки</h2>
          <button className="ghost-button" onClick={() => setShowPlayerModal(true)}>
            + Игрок
          </button>
        </div>
        <div className="roster-list">
          {roster.map((item) => (
            <div key={item.id} className="roster-row">
              <div>
                <strong>{item.nick}</strong>
                <small>
                  {item.games_played} игр | {item.paid_amount} ₽
                </small>
              </div>
              <button className="ghost-button small" disabled={item.games_played > 0} onClick={() => void handleRemovePlayer(item.player_id)}>
                Удалить
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="section-card">
        <div className="section-heading">
          <h2>Столы и игры</h2>
          <button className="ghost-button" onClick={() => setShowGameModal(true)}>
            Создать игру
          </button>
        </div>
        <div className="game-list">
          {games.map((game) => (
            <button key={game.game_id} className="game-list-row" onClick={() => navigate(`/games/${game.game_id}`)}>
              <span>{game.table_name}</span>
              <small>
                Ведущий {game.host_name} | Игра {game.game_number}
              </small>
              <strong>{statusLabels[game.status] ?? game.status}</strong>
            </button>
          ))}
        </div>
      </section>

      <section className="section-card">
        <button className="accordion-toggle" onClick={() => setShowStats((current) => !current)}>
          Статистика вечера
        </button>
        {showStats ? (
          <div className="stats-grid">
            <div className="stat-box">
              <span>Игроки</span>
              <strong>{roster.length}</strong>
            </div>
            <div className="stat-box">
              <span>Сыграно</span>
              <strong>{totals.totalGames}</strong>
            </div>
            <div className="stat-box">
              <span>Оплачено</span>
              <strong>{totals.totalPaid.toFixed(2)} ₽</strong>
            </div>
          </div>
        ) : null}
      </section>

      <QuickActionRail onExport={exportEvent} />

      {showPlayerModal ? (
        <Modal title="Добавить игрока" onClose={() => setShowPlayerModal(false)}>
          <div className="modal-stack">
            <input className="search-input" placeholder="Поиск имя-ник" value={search} onChange={(event) => setSearch(event.target.value)} />
            <div className="search-results">
              {players.map((player) => (
                <button key={player.id} className="search-result-row" onClick={() => void addPlayer(player.id)}>
                  <div>
                    <strong>{player.nick}</strong>
                    <small>
                      {player.name} - {player.nick}
                    </small>
                  </div>
                  <span>Добавить</span>
                </button>
              ))}
              {!search.trim() ? <small>Начни вводить ник или имя, тогда покажем результаты.</small> : null}
            </div>

            <form className="form-grid" onSubmit={handleCreatePlayer}>
              <label>
                <span>Имя</span>
                <input value={playerForm.name} onChange={(event) => setPlayerForm((current) => ({ ...current, name: event.target.value }))} />
              </label>
              <label>
                <span>Ник</span>
                <input value={playerForm.nick} onChange={(event) => setPlayerForm((current) => ({ ...current, nick: event.target.value }))} />
              </label>
              <label>
                <span>Телефон</span>
                <input value={playerForm.phone} onChange={(event) => setPlayerForm((current) => ({ ...current, phone: event.target.value }))} />
              </label>
              <label>
                <span>Соцсеть</span>
                <input value={playerForm.social_link} onChange={(event) => setPlayerForm((current) => ({ ...current, social_link: event.target.value }))} />
              </label>
              <button className="primary-button" type="submit">
                Сохранить профиль
              </button>
            </form>
          </div>
        </Modal>
      ) : null}

      {showGameModal ? (
        <Modal title="Создать игру" onClose={() => setShowGameModal(false)}>
          <form className="form-grid" onSubmit={handleCreateGame}>
            <label>
              <span>Стол</span>
              <select value={gameTableId ?? ""} onChange={(event) => setGameTableId(Number(event.target.value))}>
                {tables.map((table) => (
                  <option key={table.id} value={table.id}>
                    {table.name}
                  </option>
                ))}
              </select>
            </label>
            <button className="primary-button" type="submit">
              Создать игру
            </button>
          </form>
        </Modal>
      ) : null}
    </div>
  );
}
