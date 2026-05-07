/**
 * Base API client — thin fetch wrapper.
 *
 * Features:
 *  - Injects Authorization header from the auth store
 *  - On 401: attempts a single token refresh, retries, then clears auth on failure
 *  - Throws plain Error with the backend's `detail` message on non-2xx responses
 *
 * Usage:
 *   import { apiClient } from '@/lib/apiClient';
 *   const user = await apiClient.get<User>('/users/me');
 *   await apiClient.post('/auth/login', body);
 */

import { API_URL } from "@/lib/config";

// One-time visibility log so you can confirm in the browser console / Metro
// log which backend the app is actually pointing at.
// eslint-disable-next-line no-console
console.log("[API] API_BASE_URL =", API_URL);

/** Default request timeout in milliseconds. Prevents fetch from hanging
 *  indefinitely when the backend is unreachable, which would keep TanStack
 *  Query in isLoading state forever (infinite skeleton). */
const REQUEST_TIMEOUT_MS = 15_000;

// Lazy import to avoid circular dependency at module load time.
// The store is a singleton so accessing it via getState() is safe outside React.
function getAuthStore() {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  return require("@/store/authStore").useAuthStore;
}

class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly data?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Create an AbortSignal that fires after the given timeout. */
function timeoutSignal(ms: number): AbortSignal {
  const controller = new AbortController();
  setTimeout(() => controller.abort(), ms);
  return controller.signal;
}

async function refreshAccessToken(refreshToken: string): Promise<{
  access_token: string;
  refresh_token: string;
}> {
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
    signal: timeoutSignal(REQUEST_TIMEOUT_MS),
  });
  if (!res.ok) throw new ApiError(res.status, "Token refresh failed");
  return res.json();
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  isRetry = false,
): Promise<T> {
  const store = getAuthStore();
  const { accessToken, refreshToken, setTokens, clearAuth } = store.getState();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    signal: init.signal ?? timeoutSignal(REQUEST_TIMEOUT_MS),
  });

  if (res.status === 401 && !isRetry && refreshToken) {
    try {
      const fresh = await refreshAccessToken(refreshToken);
      await setTokens(fresh.access_token, fresh.refresh_token);
      return request<T>(path, init, true);
    } catch {
      await clearAuth();
      throw new ApiError(401, "Session expired. Please log in again.");
    }
  }

  if (!res.ok) {
    let detail = "Request failed";
    let bodyData: Record<string, unknown> | undefined;
    try {
      const body = await res.json();
      bodyData = body;
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, detail, bodyData);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, init?: RequestInit) =>
    request<T>(path, { ...init, method: "GET" }),

  post: <T>(path: string, body?: unknown, init?: RequestInit) =>
    request<T>(path, {
      ...init,
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(path: string, body?: unknown, init?: RequestInit) =>
    request<T>(path, {
      ...init,
      method: "PATCH",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body?: unknown, init?: RequestInit) =>
    request<T>(path, {
      ...init,
      method: "PUT",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  delete: <T = void>(path: string, init?: RequestInit) =>
    request<T>(path, { ...init, method: "DELETE" }),
};

export { ApiError };
