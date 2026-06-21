import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { persistQueryClient } from "@tanstack/react-query-persist-client";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { StatusBar } from "expo-status-bar";
import { useState } from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { AuthProvider, useAuth } from "@/providers/AuthProvider";
import { RootNavigator } from "@/navigation/RootNavigator";
import { palette } from "@/theme";

function AppShell() {
  const { bootstrapping } = useAuth();
  return <RootNavigator bootstrapping={bootstrapping} />;
}

// Minimal AsyncStorage persister so cached queries (dashboard, learn, notes)
// survive cold starts and are readable offline.
const asyncStoragePersister = {
  persistClient: async (client: unknown) => {
    await AsyncStorage.setItem("rq-cache", JSON.stringify(client));
  },
  restoreClient: async () => {
    const raw = await AsyncStorage.getItem("rq-cache");
    return raw ? JSON.parse(raw) : undefined;
  },
  removeClient: async () => {
    await AsyncStorage.removeItem("rq-cache");
  },
};

export default function App() {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            gcTime: 1000 * 60 * 60 * 24, // keep in cache 24h for offline reads
            staleTime: 1000 * 30,
            retry: 2,
          },
        },
      })
  );

  useState(() => {
    persistQueryClient({
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      queryClient: queryClient as any,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      persister: asyncStoragePersister as any,
      maxAge: 1000 * 60 * 60 * 24,
    });
    return null;
  });

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider queryClient={queryClient}>
          <StatusBar style="dark" backgroundColor={palette.background} />
          <AppShell />
        </AuthProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
