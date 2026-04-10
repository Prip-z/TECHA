import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Modal } from "../components/Modal";
import { QuickActionRail } from "../components/QuickActionRail";
import { TimerPanel } from "../components/TimerPanel";
import { useAuth } from "../contexts/AuthContext";
import { useRealtimeRoom } from "../hooks/useRealtimeRoom";
import { api } from "../lib/api";
import { loadGameDraft, saveGameDraft } from "../lib/storage";
import type { ChatMessage, EventRosterItem, GameDraftState, GameParticipant, GameRecord, GameResult, NightDraft, SyncEnvelope } from "../types/models";

const emptyNight = (round: number): NightDraft => ({
  round,
  mafiaTargetSeat: null,
  sheriffCheckSeat: null,
  donCheckSeat: null,
  killedSeat: null,
  notes: "",
});

const emptyDraft: GameDraftState = {
  stage: "preparation",
  roundNumber: 1,
  phase: "day",
  timerPreset: 60,
  timerEndsAt: null,
  timerRemainingMs: null,
  winner: null,
  protests: "",
  votes: [{ round: 1, nominations: [], votes: {}, isTie: false, isRevote: false, liftApplied: false }],
  shots: [{ round: 1, shooterSeat: null, targetSeat: null }],
  testament: { sourceSeat: null, targetSeats: [] },
  nights: [emptyNight(1)],
  notes: "",
  chat: [],
};

const resultOptions: Array<{ value: GameResult; label: string }> = [
  { value: "civilian_win", label: "Победа мирных" },
  { value: "mafia_win", label: "Победа мафии" },
  { value: "ppk_mafia_win", label: "ППК победа мафии" },
  { value: "ppk_civilian_win", label: "ППК победа мирных" },
  { value: "draw", label: "Ничья" },
];

const statusLabels: Record<string, string> = {
  preparation: "подготовка",
  voting: "день",
  revote: "переголосование",
  shooting: "ночь",
  testament: "завещание",
  finished: "завершено",
};

function createMessage(author: string, text: string): ChatMessage {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    author,
    text,
    createdAt: new Date().toISOString(),
  };
}

function normalizeDraft(input: GameDraftState | null | undefined): GameDraftState {
  const base = input ?? emptyDraft;
  return {
    ...emptyDraft,
    ...base,
    timerRemainingMs: base.timerRemainingMs ?? null,
    votes: base.votes?.length ? base.votes : emptyDraft.votes,
    shots: base.shots?.length ? base.shots : emptyDraft.shots,
    nights: base.nights?.length ? base.nights : emptyDraft.nights,
    chat: base.chat ?? [],
  };
}

function appendUniqueChatMessage(chat: ChatMessage[], nextMessage: ChatMessage) {
  if (chat.some((item) => item.id === nextMessage.id)) {
    return chat;
  }
  return [...chat, nextMessage].sort((left, right) => left.createdAt.localeCompare(right.createdAt));
}

export function GamePage() {
  const { token, user } = useAuth();
  const { gameId } = useParams();
  const navigate = useNavigate();
  const numericGameId = Number(gameId);
  const [game, setGame] = useState<GameRecord | null>(null);
  const [participants, setParticipants] = useState<GameParticipant[]>([]);
  const [eventPlayers, setEventPlayers] = useState<EventRosterItem[]>([]);
  const [draft, setDraft] = useState<GameDraftState>(() => normalizeDraft(loadGameDraft(Number(gameId))));
  const [chatInput, setChatInput] = useState("");
  const [finishWord, setFinishWord] = useState("");
  const [realtimeLog, setRealtimeLog] = useState<string[]>([]);
  const [showPlayerModal, setShowPlayerModal] = useState(false);

  async function load() {
    if (!token || !numericGameId) return;
    const [gameResponse, participantsResponse] = await Promise.all([api.getGame(token, numericGameId), api.listGameParticipants(token, numericGameId)]);
    const eventPlayersResponse = await api.listEventPlayers(token, gameResponse.event_id);
    setGame(gameResponse);
    setParticipants(participantsResponse);
    setEventPlayers(eventPlayersResponse);
    setDraft((current) =>
      normalizeDraft({
        ...current,
        stage: gameResponse.status,
        winner: gameResponse.result ?? current.winner,
        protests: gameResponse.protests ?? current.protests,
      }),
    );
  }

  useEffect(() => {
    void load();
  }, [numericGameId, token]);

  useEffect(() => {
    saveGameDraft(numericGameId, draft);
  }, [draft, numericGameId]);

  function handleRealtimeMessage(message: SyncEnvelope) {
    if (message.type === "game_updated") {
      void load();
    }
    if (message.type === "draft_sync" && message.payload) {
      setDraft(normalizeDraft(message.payload as GameDraftState));
    }
    if (message.type === "chat_message" && message.payload) {
      const chatMessage = message.payload as ChatMessage;
      setDraft((current) => ({ ...current, chat: appendUniqueChatMessage(current.chat, chatMessage) }));
    }
    if (message.type === "presence") {
      setRealtimeLog((current) => [...current.slice(-4), `${message.role ?? "user"} ${message.action ?? "sync"}`]);
    }
  }

  const { connected, send } = useRealtimeRoom(gameId ? `game-${gameId}` : null, token, handleRealtimeMessage);

  const takenSeats = useMemo(() => new Set(participants.map((item) => item.seat_number)), [participants]);
  const availableEventPlayers = useMemo(
    () => eventPlayers.filter((player) => !participants.some((participant) => participant.player_id === player.player_id)),
    [eventPlayers, participants],
  );
  const currentNight = useMemo(() => draft.nights.find((item) => item.round === draft.roundNumber) ?? emptyNight(draft.roundNumber), [draft.nights, draft.roundNumber]);
  const currentVote = useMemo(
    () => draft.votes.find((item) => item.round === draft.roundNumber) ?? { round: draft.roundNumber, nominations: [], votes: {}, isTie: false, isRevote: false, liftApplied: false },
    [draft.roundNumber, draft.votes],
  );

  function syncDraft(nextDraft: GameDraftState) {
    const normalized = normalizeDraft(nextDraft);
    setDraft(normalized);
    send("draft_sync", normalized);
  }

  function updateDraftLocally(updater: (current: GameDraftState) => GameDraftState) {
    syncDraft(updater(draft));
  }

  function getNextSeatNumber() {
    for (let seat = 1; seat <= 10; seat += 1) {
      if (!takenSeats.has(seat)) return seat;
    }
    return null;
  }

  async function addParticipant(playerId: number) {
    if (!token || !game) return;
    const seatNumber = getNextSeatNumber();
    if (!seatNumber) return;
    await api.addGameParticipant(token, game.game_id, { player_id: playerId, seat_number: seatNumber });
    setShowPlayerModal(false);
    await load();
  }

  async function removeParticipant(participantId: number) {
    if (!token || !game) return;
    await api.removeGameParticipant(token, game.game_id, participantId);
    await load();
  }

  async function updateParticipant(participantId: number, payload: Partial<GameParticipant>) {
    if (!token || !game) return;
    await api.updateGameParticipant(token, game.game_id, participantId, payload);
    await load();
  }

  async function handleStartGame() {
    if (!token || !game) return;
    const response = await api.startGame(token, game.game_id);
    setGame(response);
    syncDraft({ ...draft, stage: response.status, phase: "day" });
  }

  async function handleFinishGame() {
    if (!token || !game || !draft.winner) return;
    const response = await api.finishGame(token, game.game_id, {
      confirm_word: finishWord,
      result: draft.winner,
      protests: draft.protests,
    });
    setGame(response);
    syncDraft({ ...draft, stage: response.status });
  }

  function toggleTimer(preset: 30 | 60 | 90) {
    syncDraft({
      ...draft,
      timerPreset: preset,
      timerRemainingMs: null,
      timerEndsAt: Date.now() + preset * 1000,
    });
  }

  function togglePauseTimer() {
    if (draft.timerRemainingMs !== null) {
      syncDraft({
        ...draft,
        timerRemainingMs: null,
        timerEndsAt: Date.now() + draft.timerRemainingMs,
      });
      return;
    }
    if (!draft.timerEndsAt) {
      syncDraft({ ...draft, timerRemainingMs: draft.timerPreset * 1000, timerEndsAt: null });
      return;
    }
    syncDraft({
      ...draft,
      timerRemainingMs: Math.max(0, draft.timerEndsAt - Date.now()),
      timerEndsAt: null,
    });
  }

  function updateCurrentNight(field: keyof NightDraft, value: string | number | null) {
    updateDraftLocally((current) => ({
      ...current,
      nights: current.nights.some((item) => item.round === current.roundNumber)
        ? current.nights.map((item) => (item.round === current.roundNumber ? { ...item, [field]: value } : item))
        : [...current.nights, { ...emptyNight(current.roundNumber), [field]: value }],
    }));
  }

  function updateCurrentVote(field: "nominations" | "votes" | "isTie" | "isRevote" | "liftApplied", value: unknown) {
    updateDraftLocally((current) => ({
      ...current,
      votes: current.votes.some((item) => item.round === current.roundNumber)
        ? current.votes.map((item) => (item.round === current.roundNumber ? { ...item, [field]: value } : item))
        : [...current.votes, { round: current.roundNumber, nominations: [], votes: {}, isTie: false, isRevote: false, liftApplied: false, [field]: value }],
    }));
  }

  function startNight() {
    if (draft.phase !== "day") return;
    syncDraft({
      ...draft,
      phase: "night",
      stage: "shooting",
      nights: draft.nights.some((item) => item.round === draft.roundNumber) ? draft.nights : [...draft.nights, emptyNight(draft.roundNumber)],
    });
  }

  function startNextDay() {
    if (draft.phase !== "night") return;
    const nextRound = draft.roundNumber + 1;
    syncDraft({
      ...draft,
      roundNumber: nextRound,
      phase: "day",
      stage: "voting",
      nights: draft.nights,
      votes: [...draft.votes, { round: nextRound, nominations: [], votes: {}, isTie: false, isRevote: false, liftApplied: false }],
      shots: draft.shots,
    });
  }

  function applyNightKill() {
    if (currentNight.killedSeat == null) return;
    const killedParticipant = participants.find((item) => item.seat_number === currentNight.killedSeat);
    if (!killedParticipant) return;
    void updateParticipant(killedParticipant.id, { is_alive: false });
  }

  function sendChat() {
    if (!chatInput.trim() || !user) return;
    const message = createMessage(user.name, chatInput.trim());
    setChatInput("");
    setDraft((current) => ({ ...current, chat: appendUniqueChatMessage(current.chat, message) }));
    send("chat_message", message);
  }

  function exportGame() {
    if (!token) return;
    void api.downloadFile(`/games/${numericGameId}/export`, token, `game-${numericGameId}.xlsx`);
  }

  if (!game) {
    return <div className="section-card">Загрузка игры...</div>;
  }

  return (
    <div className="page-stack game-screen">
      <section className="hero-panel compact">
        <button className="ghost-button" onClick={() => navigate(`/events/${game.event_id}`)}>
          {"<"} Назад
        </button>
        <div>
          <h1>Стол #{game.table_id}</h1>
          <p>
            Игра {game.game_number} | {statusLabels[game.status] ?? game.status} | WS {connected ? "онлайн" : "офлайн"}
          </p>
        </div>
        <div className="presence-log">
          {realtimeLog.map((item, index) => (
            <small key={`${item}-${index}`}>{item}</small>
          ))}
        </div>
      </section>

      <TimerPanel
        preset={draft.timerPreset}
        endsAt={draft.timerEndsAt}
        pausedRemainingMs={draft.timerRemainingMs}
        onToggle={toggleTimer}
        onPauseToggle={togglePauseTimer}
      />

      <section className="section-card">
        <div className="section-heading">
          <h2>Игроки</h2>
          {game.status === "preparation" ? (
            <div className="switch-row">
              <button className="ghost-button small" disabled={availableEventPlayers.length === 0 || getNextSeatNumber() === null} onClick={() => setShowPlayerModal(true)}>
                + Игрок
              </button>
              <button className="primary-button small" onClick={() => void handleStartGame()}>
                Начать игру
              </button>
            </div>
          ) : null}
        </div>
        <div className="participant-table">
          <div className="participant-header">
            <span>Место</span>
            <span>Ник</span>
            <span>Фолы</span>
            <span>Баллы</span>
            <span>Доп.</span>
            <span>Статус</span>
          </div>
          {participants.map((participant) => (
            <div key={participant.id} className={`participant-row ${participant.is_alive ? "" : "dead"}`}>
              <span>{participant.seat_number}</span>
              <span>{participant.nick}</span>
              <button onClick={() => void updateParticipant(participant.id, { fouls: Math.min(4, participant.fouls + 1) })}>{participant.fouls}</button>
              <input type="number" value={participant.score} onChange={(event) => void updateParticipant(participant.id, { score: Number(event.target.value) })} />
              <input
                type="number"
                step="0.1"
                value={participant.extra_score}
                onChange={(event) => void updateParticipant(participant.id, { extra_score: Number(event.target.value) })}
              />
              {game.status === "preparation" ? (
                <button className="ghost-button small" onClick={() => void removeParticipant(participant.id)}>
                  Удалить
                </button>
              ) : (
                <button className="ghost-button small" onClick={() => void updateParticipant(participant.id, { is_alive: !participant.is_alive })}>
                  {participant.is_alive ? "Жив" : "Мертв"}
                </button>
              )}
            </div>
          ))}
        </div>
      </section>

      {game.status !== "preparation" ? (
        <section className="section-card">
          <div className="section-heading">
            <h2>Ход игры</h2>
            <small>
              Раунд {draft.roundNumber} | {draft.phase === "day" ? "День" : "Ночь"}
            </small>
          </div>

          {draft.phase === "day" ? (
            <div className="game-panels">
              <article className="sheet-panel">
                <h3>Голосование</h3>
                <label>
                  <span>Выставленные места</span>
                  <input
                    value={currentVote.nominations.join(",")}
                    onChange={(event) =>
                      updateCurrentVote(
                        "nominations",
                        event.target.value
                          .split(",")
                          .map((item) => Number(item.trim()))
                          .filter((item) => !Number.isNaN(item)),
                      )
                    }
                  />
                </label>
                <label>
                  <span>Голоса место-цель</span>
                  <textarea
                    value={Object.entries(currentVote.votes)
                      .map(([seat, value]) => `${seat}:${value}`)
                      .join(", ")}
                    onChange={(event) => {
                      const parsed = event.target.value.split(",").reduce<Record<string, number | "X">>((accumulator, pair) => {
                        const [seat, value] = pair.split(":").map((item) => item.trim());
                        if (!seat || !value) return accumulator;
                        accumulator[seat] = value.toUpperCase() === "X" ? "X" : Number(value);
                        return accumulator;
                      }, {});
                      updateCurrentVote("votes", parsed);
                    }}
                  />
                </label>
                <div className="switch-row">
                  <label>
                    <input type="checkbox" checked={currentVote.isTie} onChange={(event) => updateCurrentVote("isTie", event.target.checked)} />
                    ничья
                  </label>
                  <label>
                    <input type="checkbox" checked={currentVote.isRevote} onChange={(event) => updateCurrentVote("isRevote", event.target.checked)} />
                    переголосование
                  </label>
                </div>
                <button className="primary-button" onClick={startNight}>
                  Завершить день и перейти к ночи
                </button>
              </article>
            </div>
          ) : (
            <div className="game-panels">
              <article className="sheet-panel">
                <h3>Ночь</h3>
                <label>
                  <span>Выстрел мафии</span>
                  <input type="number" value={currentNight.mafiaTargetSeat ?? ""} onChange={(event) => updateCurrentNight("mafiaTargetSeat", Number(event.target.value) || null)} />
                </label>
                <label>
                  <span>Проверка шерифа</span>
                  <input type="number" value={currentNight.sheriffCheckSeat ?? ""} onChange={(event) => updateCurrentNight("sheriffCheckSeat", Number(event.target.value) || null)} />
                </label>
                <label>
                  <span>Проверка дона</span>
                  <input type="number" value={currentNight.donCheckSeat ?? ""} onChange={(event) => updateCurrentNight("donCheckSeat", Number(event.target.value) || null)} />
                </label>
                <label>
                  <span>Кто убит</span>
                  <input type="number" value={currentNight.killedSeat ?? ""} onChange={(event) => updateCurrentNight("killedSeat", Number(event.target.value) || null)} />
                </label>
                <label>
                  <span>Заметки ночи</span>
                  <textarea value={currentNight.notes} onChange={(event) => updateCurrentNight("notes", event.target.value)} />
                </label>
                <div className="switch-row">
                  <button className="ghost-button" onClick={applyNightKill}>
                    Применить убийство
                  </button>
                  <button className="primary-button" onClick={startNextDay}>
                    Начать следующий день
                  </button>
                </div>
              </article>
            </div>
          )}
        </section>
      ) : null}

      <section className="section-card">
        <div className="section-heading">
          <h2>Завершение игры</h2>
          <small>Для закрытия игры выбери победителя и введи слово подтверждения.</small>
        </div>
        <div className="result-grid">
          <select value={draft.winner ?? ""} onChange={(event) => syncDraft({ ...draft, winner: event.target.value as GameResult })}>
            <option value="">Выбери победителя</option>
            {resultOptions.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <input value={finishWord} onChange={(event) => setFinishWord(event.target.value)} placeholder="Слово: завершить" />
          <textarea value={draft.protests} onChange={(event) => syncDraft({ ...draft, protests: event.target.value })} placeholder="Протесты и заметки" />
          <button className="primary-button" onClick={() => void handleFinishGame()}>
            Завершить игру
          </button>
        </div>
      </section>

      <section className="section-card">
        <div className="section-heading">
          <h2>Чат судей</h2>
          <small>Без дублей сообщений.</small>
        </div>
        <div className="chat-list">
          {draft.chat.map((item) => (
            <div key={item.id} className="chat-bubble">
              <strong>{item.author}</strong>
              <span>{item.text}</span>
            </div>
          ))}
        </div>
        <div className="chat-compose">
          <input value={chatInput} onChange={(event) => setChatInput(event.target.value)} placeholder="Сообщение второму судье" />
          <button onClick={sendChat}>Отправить</button>
        </div>
      </section>

      <QuickActionRail onExport={exportGame} />

      {showPlayerModal ? (
        <Modal title="Добавить игрока в игру" onClose={() => setShowPlayerModal(false)}>
          <div className="modal-stack">
            <div className="search-results">
              {availableEventPlayers.map((player) => (
                <button key={player.id} className="search-result-row" onClick={() => void addParticipant(player.player_id)}>
                  <div>
                    <strong>{player.nick}</strong>
                    <small>
                      {player.name} | игр на вечере: {player.games_played}
                    </small>
                  </div>
                  <span>Место {getNextSeatNumber()}</span>
                </button>
              ))}
            </div>
          </div>
        </Modal>
      ) : null}
    </div>
  );
}
