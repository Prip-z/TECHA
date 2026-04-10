export type StaffRole = "super_admin" | "admin" | "host";
export type EventType = "default" | "tournament";
export type GameStatus = "preparation" | "voting" | "revote" | "shooting" | "testament" | "finished";
export type ParticipantRole = "civilian" | "mafia" | "don" | "sheriff";
export type GameResult =
  | "civilian_win"
  | "mafia_win"
  | "ppk_civilian_win"
  | "ppk_mafia_win"
  | "draw";
export type RoundPhase = "day" | "night";

export interface AuthTokenResponse {
  access_token: string;
  token_type: "bearer";
  role: StaffRole;
}

export interface StaffUser {
  id: number;
  login: string;
  name: string;
  role: StaffRole;
  is_active: boolean;
}

export interface EventRecord {
  id: number;
  name: string;
  date: string;
  type: EventType;
  price_per_game: number;
}

export interface EventListResponse {
  items: EventRecord[];
  total: number;
}

export interface PlayerRecord {
  id: number;
  name: string;
  nick: string;
  phone: string | null;
  social_link: string | null;
}

export interface PlayerListResponse {
  items: PlayerRecord[];
  total: number;
}

export interface EventRosterItem {
  id: number;
  player_id: number;
  name: string;
  nick: string;
  phone: string | null;
  social_link: string | null;
  games_played: number;
  paid_amount: number;
}

export interface TableRecord {
  id: number;
  name: string;
}

export interface AppSettings {
  default_price_per_game: number;
}

export interface EventGameItem {
  game_id: number;
  game_number: number;
  table_id: number;
  table_name: string;
  host_staff_id: number;
  host_name: string;
  status: GameStatus | string;
  result: GameResult | null;
}

export interface GameRecord {
  game_id: number;
  event_id: number;
  table_id: number;
  host_staff_id: number;
  game_number: number;
  status: GameStatus;
  result: GameResult | null;
  protests: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface GameParticipant {
  id: number;
  game_id: number;
  player_id: number;
  name: string;
  nick: string;
  seat_number: number;
  fouls: number;
  score: number;
  extra_score: number;
  role: ParticipantRole;
  is_alive: boolean;
}

export interface SyncEnvelope<T = unknown> {
  type: string;
  roomId?: string;
  action?: string;
  userId?: string;
  role?: StaffRole;
  payload?: T;
}

export interface ChatMessage {
  id: string;
  author: string;
  text: string;
  createdAt: string;
}

export interface VoteDraft {
  round: number;
  nominations: number[];
  votes: Record<string, number | "X">;
  isTie: boolean;
  isRevote: boolean;
  liftApplied: boolean;
}

export interface ShotDraft {
  round: number;
  shooterSeat: number | null;
  targetSeat: number | "X" | null;
}

export interface TestamentDraft {
  sourceSeat: number | null;
  targetSeats: number[];
}

export interface NightDraft {
  round: number;
  killedSeat: number | null;
  notes: string;
}

export interface GameDraftState {
  stage: GameStatus;
  roundNumber: number;
  phase: RoundPhase;
  timerPreset: 30 | 60 | 90;
  timerEndsAt: number | null;
  timerRemainingMs: number | null;
  winner: GameResult | null;
  protests: string;
  votes: VoteDraft[];
  shots: ShotDraft[];
  testament: TestamentDraft;
  nights: NightDraft[];
  notes: string;
  chat: ChatMessage[];
}
