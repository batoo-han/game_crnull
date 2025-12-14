export type BotDifficulty = "easy" | "medium" | "hard";
export type GameStatus = "IN_PROGRESS" | "WIN" | "LOSE" | "DRAW";

export type GameState = {
  session_id: string;
  board: string[];
  status: GameStatus;
  winner: string | null;
  last_player_move?: number | null;
  last_bot_move?: number | null;
  promo_code?: string | null;
  promo_expires_at?: string | null;
};

function normalizeBaseUrl(raw: string | undefined): string {
  // В продакшене лучше использовать same-origin и прокси Nginx (/api -> backend),
  // чтобы не упираться в CORS и не “шить” хост в сборку.
  const base = (raw ?? "").trim();
  if (!base) return "";
  return base.endsWith("/") ? base.slice(0, -1) : base;
}

const API_BASE = normalizeBaseUrl(import.meta.env.VITE_API_BASE);

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!res.ok) {
    // Важно: читаемый текст ошибки для UX.
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }

  return (await res.json()) as T;
}

export async function newGame(difficulty: BotDifficulty): Promise<GameState> {
  return api<GameState>("/api/game/new", {
    method: "POST",
    body: JSON.stringify({ difficulty })
  });
}

export async function makeMove(sessionId: string, cell: number): Promise<GameState> {
  return api<GameState>("/api/game/move", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, cell })
  });
}

export type PromoCodeResponse = {
  promo_code: string;
  promo_expires_at: string;
  message?: string;
};

export async function getGiftPromo(sessionId: string): Promise<PromoCodeResponse> {
  return api<PromoCodeResponse>("/api/game/gift-promo", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId })
  });
}


