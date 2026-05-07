export type GameInvitationStatus = "pending" | "accepted" | "declined";

export interface GameInvitation {
  id: string;
  game_id: string;
  invited_user_id: string;
  invited_user_display_name: string;
  invited_by_user_id: string;
  status: GameInvitationStatus;
  created_at: string;
}

export interface CreateGameInvitationRequest {
  invited_user_id: string;
}
