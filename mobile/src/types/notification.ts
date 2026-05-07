export type NotificationType =
  | "friend_request_received"
  | "friend_request_accepted"
  | "game_invitation"
  | "game_started"
  | "game_closed"
  | "settlement_owed"
  | "game_resettled";

export interface AppNotification {
  id: string;
  user_id: string;
  type: NotificationType;
  read: boolean;
  data: Record<string, string> | null;
  created_at: string;
}

export interface UnreadCount {
  count: number;
}

export interface MarkAllReadResult {
  marked_read: number;
}
