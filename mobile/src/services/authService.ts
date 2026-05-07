/**
 * Auth service — login, register, logout.
 *
 * Keeps raw API calls out of components and screens.
 * Does NOT manage token storage — that belongs to authStore.
 */

import { API_URL } from "@/lib/config";
import type { AuthTokens, LoginRequest, RegisterRequest } from "@/types/auth";
import type { User } from "@/types/user";

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const url = `${API_URL}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (err) {
    // Network-level failure (CORS block, DNS, server down, offline).
    // The original error message ("Failed to fetch", "Network request failed")
    // is the most useful clue we have — surface it instead of swallowing it.
    const reason = err instanceof Error ? err.message : String(err);
    // eslint-disable-next-line no-console
    console.error("[authService] network error", { url, reason });
    throw new Error(`Network error contacting ${url}: ${reason}`);
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const parsed = await res.json();
      if (typeof parsed?.detail === "string") {
        detail = parsed.detail;
      } else if (Array.isArray(parsed?.detail)) {
        // FastAPI validation: detail is an array of {loc, msg, type}.
        detail = parsed.detail
          .map((d: { msg?: string; loc?: unknown[] }) => {
            const field = Array.isArray(d.loc) ? d.loc.slice(1).join(".") : "";
            return field ? `${field}: ${d.msg ?? ""}` : d.msg ?? "";
          })
          .filter(Boolean)
          .join("; ");
      }
    } catch {
      // ignore parse errors
    }
    // eslint-disable-next-line no-console
    console.error("[authService] http error", { url, status: res.status, detail });
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

/** Authenticate with email + password. Returns access + refresh tokens. */
export async function login(data: LoginRequest): Promise<AuthTokens> {
  return postJson<AuthTokens>("/auth/login", data);
}

/**
 * Register a new account then immediately log in.
 * Returns the registered user — caller must still call login() for tokens.
 */
export async function register(data: RegisterRequest): Promise<User> {
  return postJson<User>("/auth/register", data);
}
