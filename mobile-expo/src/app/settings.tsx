import { useEffect, useMemo, useState } from 'react';
import { ScrollView, TextInput, View } from 'react-native';
import { Stack, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Body, Button, Card, Heading, Subtle, useTokens } from '@/components/ui';
import { useSettings } from '@/state/settings';
import { api, makeClient } from '@/api/client';

export default function SettingsScreen() {
  const t = useTokens();
  const router = useRouter();
  const { baseUrl, setBaseUrl } = useSettings();

  const [draft, setDraft] = useState(baseUrl);
  const [status, setStatus] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    setDraft(baseUrl);
  }, [baseUrl]);

  const dirty = useMemo(() => draft.trim() !== baseUrl, [draft, baseUrl]);

  async function save() {
    await setBaseUrl(draft);
    setStatus('Сохранено');
  }

  async function test() {
    setTesting(true);
    setStatus(null);
    try {
      const c = makeClient(draft.trim().replace(/\/+$/, ''));
      await api.health(c);
      setStatus('OK — backend доступен ✓');
    } catch {
      setStatus('Не удалось подключиться ✗');
    } finally {
      setTesting(false);
    }
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: t.bg }}>
      <Stack.Screen options={{ title: 'Настройки' }} />
      <ScrollView contentContainerStyle={{ padding: 16, gap: 12 }}>
        <Heading>Настройки</Heading>
        <Subtle>Адрес backend (Tailscale IP компьютера, где запущен сервер)</Subtle>

        <Card>
          <TextInput
            value={draft}
            onChangeText={setDraft}
            placeholder="http://100.64.0.1:8000"
            placeholderTextColor={t.muted}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            style={{
              color: t.text,
              backgroundColor: t.surfaceAlt,
              borderRadius: 8,
              padding: 10,
              fontSize: 14,
            }}
          />
          <View style={{ flexDirection: 'row', gap: 8, marginTop: 10 }}>
            <Button title={dirty ? 'Сохранить' : 'Сохранено'} onPress={save} disabled={!dirty} />
            <Button title={testing ? 'Проверяю…' : 'Проверить связь'} variant="outline" onPress={test} disabled={testing} />
          </View>
          {status && (
            <Body style={{ marginTop: 10 }}>{status}</Body>
          )}
        </Card>

        <Card>
          <Subtle>
            Backend должен работать на компьютере (englishbot start) там, где выполнен вход
            в Claude Code. Telephone достаёт его через Tailscale.
          </Subtle>
        </Card>

        <View style={{ height: 8 }} />
        <Button title="← Назад" variant="ghost" onPress={() => router.back()} />
      </ScrollView>
    </SafeAreaView>
  );
}
