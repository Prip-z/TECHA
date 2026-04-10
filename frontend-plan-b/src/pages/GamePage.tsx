import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Modal } from "../components/Modal";
import { QuickActionRail } from "../components/QuickActionRail";
import { TimerPanel } from "../components/TimerPanel";
import { useAuth } from "../contexts/AuthContext";
import { useRealtimeRoom } from "../hooks/useRealtimeRoom";
import { api } from "../lib/api";
import { loadGameDraft, saveGameDraft } from "../lib/storage";
import type { ChatMessage, EventRosterItem, GameDraftState, GameParticipant, GameRecord, GameResult, NightDraft, SyncEnvelope, VoteDraft } from "../types/models";

const emptyNight = (round: number): NightDraft => ({
  round,
  killedSeat: null,
  notes: "",
});

const emptyVote = (round: number): VoteDraft => ({
  round,
  nominations: [],
  votes: {},
  isTie: false,
  isRevote: false,
  liftApplied: false,
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
  votes: [emptyVote(1)],
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
    votes: base.votes?.length ? base.votes : [emptyVote(base.roundNumber ?? 1)],
    nights: base.nights?.length ? base.nights : [emptyNight(base.roundNumber ?? 1)],
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
  const aliveParticipants = useMemo(
    () => participants.filter((item) => item.is_alive).sort((left, right) => left.seat_number - right.seat_number),
    [participants],
  );
  const currentNight = useMemo(() => draft.nights.find((item) => item.round === draft.roundNumber) ?? emptyNight(draft.roundNumber), [draft.nights, draft.roundNumber]);
  const currentVote = useMemo(() => draft.votes.find((item) => item.round === draft.roundNumber) ?? emptyVote(draft.roundNumber), [draft.roundNumber, draft.votes]);
  const voteCounts = useMemo(
    () =>
      currentVote.nominations.reduce<Record<number, number>>((accumulator, seat) => {
        accumulator[seat] = Object.values(currentVote.votes).filter((value) => value === seat).length;
        return accumulator;
      }, {}),
    [currentVote.nominations, currentVote.votes],
  );
  const votersEntered = useMemo(() => Object.keys(currentVote.votes).length, [currentVote.votes]);

  function syncDraft(nextDraft: GameDraftState) {
    const normalized = normalizeDraft(nextDraft);
    setDraft(normalized);
    send("draft_sync", normalized);
  }

  function updateDraftLocally(updater: (current: GameDraftState) => GameDraftState) {
    syncDraft(updater(draft));
  }

  function ensureVoteRound(current: GameDraftState) {
    return current.votes.some((item) => item.round === current.roundNumber) ? current.votes : [...current.votes, emptyVote(current.roundNumber)];
  }

  function ensureNightRound(current: GameDraftState) {
    return current.nights.some((item) => item.round === current.roundNumber) ? current.nights : [...current.nights, emptyNight(current.roundNumber)];
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

  function toggleNomination(seatNumber: number) {
    updateDraftLocally((current) => {
      const votes = ensureVoteRound(current);
      return {
        ...current,
        votes: votes.map((item) =>
          item.round === current.roundNumber
            ? {
                ...item,
                nominations: item.nominations.includes(seatNumber)
                  ? item.nominations.filter((seat) => seat !== seatNumber)
                  : [...item.nominations, seatNumber].sort((left, right) => left - right),
                votes: Object.fromEntries(Object.entries(item.votes).filter(([, value]) => value !== seatNumber)),
              }
            : item,
        ),
      };
    });
  }

  function addVoteToSeat(seatNumber: number) {
    const nextVoter = aliveParticipants.find((participant) => !(participant.seat_number in currentVote.votes));
    if (!nextVoter) return;
    updateDraftLocally((current) => ({
      ...current,
      votes: ensureVoteRound(current).map((item) =>
        item.round === current.roundNumber ? { ...item, votes: { ...item.votes, [String(nextVoter.seat_number)]: seatNumber } } : item,
      ),
    }));
  }

  function removeVoteFromSeat(seatNumber: number) {
    const latestVoter = [...aliveParticipants]
      .reverse()
      .find((participant) => currentVote.votes[String(participant.seat_number)] === seatNumber);
    if (!latestVoter) return;
    updateDraftLocally((current) => {
      const currentRound = current.votes.find((item) => item.round === current.roundNumber) ?? emptyVote(current.roundNumber);
      const nextVotes = { ...currentRound.votes };
      delete nextVotes[String(latestVoter.seat_number)];
      return {
        ...current,
        votes: ensureVoteRound(current).map((item) => (item.round === current.roundNumber ? { ...item, votes: nextVotes } : item)),
      };
    });
  }

  function updateManualVote(voterSeat: number, value: string) {
    updateDraftLocally((current) => {
      const currentRound = current.votes.find((item) => item.round === current.roundNumber) ?? emptyVote(current.roundNumber);
      const nextVotes = { ...currentRound.votes };
      if (!value) {
        delete nextVotes[String(voterSeat)];
      } else {
        nextVotes[String(voterSeat)] = Number(value);
      }
      return {
        ...current,
        votes: ensureVoteRound(current).map((item) => (item.round === current.roundNumber ? { ...item, votes: nextVotes } : item)),
      };
    });
  }

  function updateCurrentNight(field: keyof NightDraft, value: string | number | null) {
    updateDraftLocally((current) => ({
      ...current,
      nights: ensureNightRound(current).map((item) => (item.round === current.roundNumber ? { ...item, [field]: value } : item)),
    }));
  }

  function startNight() {
    if (draft.phase !== "day") return;
    syncDraft({
      ...draft,
      phase: "night",
      stage: "shooting",
      nights: ensureNightRound(draft),
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
      votes: draft.votes.some((item) => item.round === nextRound) ? draft.votes : [...draft.votes, emptyVote(nextRound)],
      nights: draft.nights,
    });
  }

  function applyNightResult() {
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
                <small>Сначала выставь кандидатов, потом добей голоса быстрыми кнопками или руками по местам.</small>

                <div className="vote-seat-grid">
                  {aliveParticipants.map((participant) => (
                    <button
                      key={participant.id}
                      className={`vote-seat-chip ${currentVote.nominations.includes(participant.seat_number) ? "active" : ""}`}
                      onClick={() => toggleNomination(participant.seat_number)}
                    >
                      {participant.seat_number}
                    </button>
                  ))}
                </div>

                <div className="mini-stats">
                  <span>Кандидатов: {currentVote.nominations.length}</span>
                  <span>Голосов внесено: {votersEntered} / {aliveParticipants.length}</span>
                </div>

                <div className="vote-board">
                  {currentVote.nominations.length === 0 ? <small>Никто не выставлен на голосование.</small> : null}
                  {currentVote.nominations.map((seat) => (
                    <div key={seat} className="vote-row">
                      <strong>Место {seat}</strong>
                      <div className="vote-counter">
                        <button className="ghost-button small" onClick={() => removeVoteFromSeat(seat)}>
                          -1
                        </button>
                        <span>{voteCounts[seat] ?? 0}</span>
                        <button className="ghost-button small" onClick={() => addVoteToSeat(seat)}>
                          +1
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="vote-voter-grid">
                  {aliveParticipants.map((participant) => (
                    <label key={participant.id}>
                      <span>Голос места {participant.seat_number}</span>
                      <select value={String(currentVote.votes[String(participant.seat_number)] ?? "")} onChange={(event) => updateManualVote(participant.seat_number, event.target.value)}>
                        <option value="">Не указан</option>
                        {currentVote.nominations.map((seat) => (
                          <option key={seat} value={seat}>
                            За {seat}
                          </option>
                        ))}
                      </select>
                    </label>
                  ))}
                </div>

                <div className="switch-row">
                  <label>
                    <input type="checkbox" checked={currentVote.isTie} onChange={(event) => updateDraftLocally((current) => ({
                      ...current,
                      votes: ensureVoteRound(current).map((item) => (item.round === current.roundNumber ? { ...item, isTie: event.target.checked } : item)),
                    }))} />
                    ничья
                  </label>
                  <label>
                    <input type="checkbox" checked={currentVote.isRevote} onChange={(event) => updateDraftLocally((current) => ({
                      ...current,
                      votes: ensureVoteRound(current).map((item) => (item.round === current.roundNumber ? { ...item, isRevote: event.target.checked } : item)),
                    }))} />
                    переголосование
                  </label>
                </div>

                <button className="primary-button" onClick={startNight}>
                  Закрыть голосование и перейти к ночи
                </button>
              </article>
            </div>
          ) : (
            <div className="game-panels">
              <article className="sheet-panel">
                <h3>Ночь</h3>
                <label>
                  <span>Результат</span>
                  <select value={String(currentNight.killedSeat ?? "")} onChange={(event) => updateCurrentNight("killedSeat", event.target.value ? Number(event.target.value) : null)}>
                    <option value="">Никто не убит</option>
                    {aliveParticipants.map((participant) => (
                      <option key={participant.id} value={participant.seat_number}>
                        Убит игрок {participant.seat_number}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Заметки ночи</span>
                  <textarea value={currentNight.notes} onChange={(event) => updateCurrentNight("notes", event.target.value)} />
                </label>
                <div className="switch-row">
                  <button className="ghost-button" onClick={applyNightResult}>
                    Применить результат ночи
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
