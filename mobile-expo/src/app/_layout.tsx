import { Stack, ThemeProvider, DarkTheme, DefaultTheme } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useColorScheme } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { SettingsProvider, useSettings } from '@/state/settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 },
  },
});

function RootStack() {
  const { loaded } = useSettings();
  if (!loaded) return null;
  return (
    <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }} />
  );
}

export default function RootLayout() {
  const scheme = useColorScheme();
  return (
    <SettingsProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider value={scheme === 'dark' ? DarkTheme : DefaultTheme}>
          <StatusBar style={scheme === 'dark' ? 'light' : 'dark'} />
          <RootStack />
        </ThemeProvider>
      </QueryClientProvider>
    </SettingsProvider>
  );
}
