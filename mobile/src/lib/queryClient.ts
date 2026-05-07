/**
 * Singleton TanStack QueryClient.
 *
 * Exported as a module-level constant so it can be shared between:
 *  - The React tree (via QueryClientProvider in _layout.tsx)
 *  - The auth store (to call queryClient.clear() on logout / session expiry)
 *  - Auth screens (to call queryClient.clear() before a new login)
 *
 * Using a module singleton avoids passing queryClient as a prop and prevents
 * the accidental creation of multiple QueryClient instances.
 */

import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});
