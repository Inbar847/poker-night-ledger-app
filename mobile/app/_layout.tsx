/**
 * Root layout — wraps the entire app.
 *
 * Responsibilities:
 *  1. Provide a QueryClient to all screens via QueryClientProvider.
 *  2. Bootstrap auth once on mount (load tokens from SecureStore).
 *     The auth store sets isBootstrapped=true when done; the (app) layout
 *     shows a loading spinner until then.
 */

import { QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { StatusBar } from "react-native";
import { useEffect } from "react";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import { queryClient } from "@/lib/queryClient";
import { useAuthStore } from "@/store/authStore";
import { tokens } from "@/theme";

function AuthBootstrap() {
  const bootstrap = useAuthStore((s) => s.bootstrap);
  useEffect(() => {
    bootstrap();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return null;
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <StatusBar barStyle="light-content" />
        <AuthBootstrap />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: tokens.color.bg.primary },
            animation: "fade",
          }}
        />
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
