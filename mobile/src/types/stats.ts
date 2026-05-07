/**
 * Types for personal history and statistics (Stage 8).
 * Mirror the backend Pydantic schemas in app/schemas/stats.py.
 * Decimal fields come as strings from the FastAPI JSON encoder.
 */

export interface GameHistoryItem {
  game_id: string;
  title: string;
  currency: string;
  chip_cash_rate: string;
  closed_at: string;
  role_in_game: "dealer" | "player";
  /** null when the user has no final stack (incomplete settlement) */
  net_balance: string | null;
  total_buy_ins: string;
}

export interface RecentGameSummary {
  game_id: string;
  title: string;
  closed_at: string;
  net_balance: string | null;
  currency: string;
}

export interface UserStats {
  total_games_played: number;
  total_games_hosted: number;
  /** Games where net_balance is known (user had a final stack) */
  games_with_result: number;
  cumulative_net: string;
  /** null when games_with_result === 0 */
  average_net: string | null;
  profitable_games: number;
  /** null when games_with_result === 0 */
  win_rate: number | null;
  recent_games: RecentGameSummary[];
}
