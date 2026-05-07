/**
 * API base URL.
 *
 * Set EXPO_PUBLIC_API_URL in your .env.local file:
 *   - iOS Simulator / local dev:     http://localhost:8000
 *   - Android Emulator:              http://10.0.2.2:8000
 *   - Physical device on LAN:        http://<your-machine-ip>:8000
 */
export const API_URL =
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

/** WebSocket base URL — derived from API_URL by replacing http(s) with ws(s). */
export const WS_URL = API_URL.replace(/^http/, "ws");
