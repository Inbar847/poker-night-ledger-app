/**
 * Notifications service — API calls for in-app notifications.
 * All calls go through apiClient so Authorization + token refresh are handled automatically.
 */

import { apiClient } from "@/lib/apiClient";
import type {
  AppNotification,
  MarkAllReadResult,
  UnreadCount,
} from "@/types/notification";

/** Fetch notifications for the current user, newest-first. */
export async function listNotifications(): Promise<AppNotification[]> {
  return apiClient.get<AppNotification[]>("/notifications");
}

/** Fetch unread notification count for the current user. */
export async function getUnreadCount(): Promise<UnreadCount> {
  return apiClient.get<UnreadCount>("/notifications/unread-count");
}

/** Mark a single notification as read. */
export async function markNotificationRead(id: string): Promise<AppNotification> {
  return apiClient.post<AppNotification>(`/notifications/${id}/read`);
}

/** Mark all notifications as read. */
export async function markAllNotificationsRead(): Promise<MarkAllReadResult> {
  return apiClient.post<MarkAllReadResult>("/notifications/read-all");
}

/** Permanently delete all notifications for the current user. */
export async function deleteAllNotifications(): Promise<void> {
  return apiClient.delete<void>("/notifications");
}
