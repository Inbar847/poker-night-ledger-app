/**
 * Authenticated app shell.
 *
 * Guards all routes in this group:
 *  - While bootstrapping (SecureStore read in progress) → show loading spinner.
 *  - After bootstrap, no access token → redirect to login.
 *  - Authenticated → render children with themed Stack navigator.
 *
 * The bottom tab bar is rendered by individual "main" screens (dashboard,
 * profile, notifications) so it naturally disappears when detail screens
 * are pushed onto the Stack.
 */

import { Redirect, Stack } from "expo-router";

import LoadingScreen from "@/components/LoadingScreen";
import InvitationPopup from "@/features/invitations/InvitationPopup";
import { usePersonalSocket } from "@/hooks/usePersonalSocket";
import { useAuthStore } from "@/store/authStore";
import { tokens } from "@/theme";

export default function AppLayout() {
  const { isBootstrapped, accessToken } = useAuthStore();

  // Personal WebSocket for user-level events (Stage 26).
  // Must be called unconditionally (React hook rules); the hook handles
  // the no-token case internally by skipping the connection.
  usePersonalSocket();

  if (!isBootstrapped) {
    return <LoadingScreen />;
  }

  if (!accessToken) {
    return <Redirect href="/auth/login" />;
  }

  return (
    <>
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: tokens.color.bg.primary },
          headerTintColor: tokens.color.text.primary,
          headerTitleStyle: { fontWeight: "600" },
          headerShadowVisible: false,
          contentStyle: { backgroundColor: tokens.color.bg.primary },
        }}
      />
      <InvitationPopup />
    </>
  );
}
