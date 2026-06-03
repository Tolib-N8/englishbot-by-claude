import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useState } from 'react';

const KEY = 'backend_base_url';
const COMPILE_DEFAULT =
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ((process.env as any).EXPO_PUBLIC_BACKEND_URL as string | undefined) ??
  'http://localhost:8000';

type Ctx = {
  loaded: boolean;
  baseUrl: string;
  setBaseUrl: (url: string) => Promise<void>;
};

const SettingsContext = createContext<Ctx>({
  loaded: false,
  baseUrl: COMPILE_DEFAULT,
  setBaseUrl: async () => {},
});

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [baseUrl, setBaseUrlState] = useState(COMPILE_DEFAULT);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const stored = await AsyncStorage.getItem(KEY);
        if (stored) setBaseUrlState(stored);
      } finally {
        setLoaded(true);
      }
    })();
  }, []);

  async function setBaseUrl(url: string) {
    const clean = url.trim().replace(/\/+$/, '');
    setBaseUrlState(clean);
    await AsyncStorage.setItem(KEY, clean);
  }

  return (
    <SettingsContext.Provider value={{ loaded, baseUrl, setBaseUrl }}>
      {children}
    </SettingsContext.Provider>
  );
}

export const useSettings = () => useContext(SettingsContext);
