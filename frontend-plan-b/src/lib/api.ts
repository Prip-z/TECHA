import type {
  AppSettings,
  AuthTokenResponse,
  EventGameItem,
  EventListResponse,
  EventRecord,
  EventRosterItem,
  GameParticipant,
  GameRecord,
  PlayerListResponse,
  PlayerRecord,
  StaffRole,
  StaffUser,
  TableRecord,
} from "../types/models";

function resolveApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (configuredUrl) {
    return configuredUrl;
  }

  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }

  return "http://localhost:8000";
}

const API_BASE_URL = resolveApiBaseUrl();

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(response.status, message || `Request failed: ${response.status}`);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  get baseUrl() {
    return API_BASE_URL;
  },

  login(login: string, password: string) {
    return request<AuthTokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ login, password }),
    });
  },

  getMe(token: string) {
    return request<StaffUser>("/auth/me", {}, token);
  },

  getSettings(token: string) {
    return request<AppSettings>("/settings", {}, token);
  },

  updateSettings(token: string, payload: AppSettings) {
    return request<AppSettings>(
      "/settings",
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
      token,
    );
  },

  listStaff(token: string) {
    return request<StaffUser[]>("/auth/staff", {}, token);
  },

  createStaff(token: string, payload: { login: string; password: string; name: string; role: StaffRole }) {
    return request<{ id: number; login: string; name: string; role: StaffRole }>("/auth/staff", {
      method: "POST",
      body: JSON.stringify(payload),
    }, token);
  },

  updateStaff(token: string, staffId: number, payload: Partial<{ name: string; password: string; role: StaffRole; is_active: boolean }>) {
    return request<StaffUser>(`/auth/staff/${staffId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, token);
  },

  deleteStaff(token: string, staffId: number) {
    return request<void>(`/auth/staff/${staffId}`, { method: "DELETE" }, token);
  },

  listDashboardEvents(token: string) {
    return request<EventListResponse>("/events?mode=dashboard", {}, token);
  },

  listAllEvents(token: string) {
    return request<EventListResponse>("/events?mode=all&limit=100", {}, token);
  },

  createEvent(token: string, payload: { name: string; date: string; type: "default" | "tournament"; price_per_game: number }) {
    return request<EventRecord>("/events", {
      method: "POST",
      body: JSON.stringify(payload),
    }, token);
  },

  updateEvent(token: string, eventId: number, payload: { name: string; date: string; type: "default" | "tournament"; price_per_game: number }) {
    return request<EventRecord>(`/events/${eventId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }, token);
  },

  listEventPlayers(token: string, eventId: number) {
    return request<EventRosterItem[]>(`/events/${eventId}/players`, {}, token);
  },

  addEventPlayer(token: string, eventId: number, playerId: number) {
    return request(`/events/${eventId}/players`, {
      method: "POST",
      body: JSON.stringify({ player_id: playerId }),
    }, token);
  },

  removeEventPlayer(token: string, eventId: number, playerId: number) {
    return request<void>(`/events/${eventId}/players/${playerId}`, { method: "DELETE" }, token);
  },

  listEventGames(token: string, eventId: number) {
    return request<EventGameItem[]>(`/events/${eventId}/games`, {}, token);
  },

  listPlayers(token: string, search?: string) {
    const query = search ? `?search=${encodeURIComponent(search)}` : "";
    return request<PlayerListResponse>(`/players${query}`, {}, token);
  },

  createPlayer(token: string, payload: { name: string; nick: string; phone?: string | null; social_link?: string | null }) {
    return request<PlayerRecord>("/players", {
      method: "POST",
      body: JSON.stringify(payload),
    }, token);
  },

  updatePlayer(token: string, playerId: number, payload: { name: string; nick: string; phone?: string | null; social_link?: string | null }) {
    return request<PlayerRecord>(`/players/${playerId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }, token);
  },

  listTables(token: string) {
    return request<TableRecord[]>("/tables", {}, token);
  },

  createTable(token: string, name: string) {
    return request<TableRecord>("/tables", {
      method: "POST",
      body: JSON.stringify({ name }),
    }, token);
  },

  updateTable(token: string, tableId: number, name: string) {
    return request<TableRecord>(`/tables/${tableId}`, {
      method: "PUT",
      body: JSON.stringify({ name }),
    }, token);
  },

  deleteTable(token: string, tableId: number) {
    return request<void>(`/tables/${tableId}`, { method: "DELETE" }, token);
  },

  createGame(token: string, payload: { event_id: number; table_id: number }) {
    return request<GameRecord>("/games", {
      method: "POST",
      body: JSON.stringify(payload),
    }, token);
  },

  getGame(token: string, gameId: number) {
    return request<GameRecord>(`/games/${gameId}`, {}, token);
  },

  listGameParticipants(token: string, gameId: number) {
    return request<GameParticipant[]>(`/games/${gameId}/participants`, {}, token);
  },

  addGameParticipant(token: string, gameId: number, payload: { player_id: number; seat_number: number }) {
    return request(`/games/${gameId}/participants`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, token);
  },

  updateGameParticipant(
    token: string,
    gameId: number,
    participantId: number,
    payload: Partial<{ seat_number: number; fouls: number; score: number; extra_score: number; role: string; is_alive: boolean }>,
  ) {
    return request<GameParticipant>(`/games/${gameId}/participants/${participantId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }, token);
  },

  removeGameParticipant(token: string, gameId: number, participantId: number) {
    return request<void>(`/games/${gameId}/participants/${participantId}`, { method: "DELETE" }, token);
  },

  startGame(token: string, gameId: number) {
    return request<GameRecord>(`/games/${gameId}/start`, { method: "POST" }, token);
  },

  finishGame(token: string, gameId: number, payload: { confirm_word: string; result: string; protests: string }) {
    return request<GameRecord>(`/games/${gameId}/finish`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, token);
  },

  async downloadFile(path: string, token: string, suggestedName: string) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) {
      const message = await response.text();
      throw new ApiError(response.status, message || "Download failed");
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = suggestedName;
    anchor.click();
    URL.revokeObjectURL(objectUrl);
  },
};
