/**
 * App entry point — redirects based on auth state.
 *
 *  - Not bootstrapped yet  → wait (LoadingScreen shown by (app) layout)
 *  - Has access token      → go to profile (the (app) auth guard handles invalid tokens)
 *  - No access token       → go to login
 */

import { Redirect } from "expo-router";
import LoadingScreen from "@/components/LoadingScreen";
import { useAuthStore } from "@/store/authStore";

export default function Index() {
  const { isBootstrapped, accessToken } = useAuthStore();

  if (!isBootstrapped) {
    return <LoadingScreen />;
  }

  if (accessToken) {
    return <Redirect href="/games" />;
  }

  return <Redirect href="/auth/login" />;
}
