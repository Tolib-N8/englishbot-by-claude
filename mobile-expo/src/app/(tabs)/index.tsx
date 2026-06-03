import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Settings as SettingsIcon } from 'lucide-react-native';

import { api, makeClient } from '@/api/client';
import type { Conversation, FlashcardStats, LevelOut } from '@/api/types';
import { Body, Button, Card, Heading, Subtle, useTokens } from '@/components/ui';
import { useSettings } from '@/state/settings';

export default function HomeScreen() {
  const t = useTokens();
  const router = useRouter();
  const { baseUrl } = useSettings();
  const client = useMemo(() => makeClient(baseUrl), [baseUrl]);

  const levelQ = useQuery({ queryKey: ['level', baseUrl], queryFn: () => api.getLevel(client) });
  const statsQ = useQuery({ queryKey: ['stats', baseUrl], queryFn: () => api.flashcardStats(client) });
  const convsQ = useQuery({ queryKey: ['conversations', baseUrl], queryFn: () => api.conversations(client) });

  const lvl = levelQ.data;
  const stats = statsQ.data;
  const convs = (convsQ.data ?? []).slice(0, 5);

  const isError = levelQ.isError || statsQ.isError || convsQ.isError;
  const isLoading = levelQ.isLoading || statsQ.isLoading || convsQ.isLoading;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: t.bg }}>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 14 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Heading>English Tutor</Heading>
          <View style={{ flex: 1 }} />
          <Pressable
            onPress={() => router.push('/settings')}
            hitSlop={10}
            style={{ padding: 6 }}
          >
            <SettingsIcon color={t.muted} size={22} />
          </Pressable>
        </View>

        {isError && (
          <Card>
            <Body>Нет связи с backend. Открой Настройки и проверь URL.</Body>
            <View style={{ height: 8 }} />
            <Button title="Открыть настройки" onPress={() => router.push('/settings')} />
          </Card>
        )}

        {!isError && (
          <Pressable onPress={() => router.push('/level')}>
            <Card>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Body style={{ fontWeight: '600' }}>Уровень — IELTS / CEFR</Body>
                <View style={{ flex: 1 }} />
                <Subtle>Подробнее ›</Subtle>
              </View>
              <View style={{ height: 8 }} />
              {!lvl?.assessment ? (
                <Subtle>Уровень ещё не оценён — открой, чтобы оценить.</Subtle>
              ) : (
                <View style={{ flexDirection: 'row', gap: 22 }}>
                  <Stat label="CEFR" value={lvl.assessment.cefr_level} color={t.primary} />
                  <Stat label="IELTS" value={lvl.assessment.ielts_band ?? '—'} />
                  {lvl.target_band ? <Stat label="Цель" value={lvl.target_band} color={t.success} /> : null}
                </View>
              )}
            </Card>
          </Pressable>
        )}

        {!isError && (
          <View style={{ flexDirection: 'row', gap: 10 }}>
            <SmallStat label="К повтору" value={stats?.due_now ?? 0} />
            <SmallStat label="Сегодня" value={stats?.reviewed_today ?? 0} />
            <SmallStat label="Всего" value={stats?.total ?? 0} />
          </View>
        )}

        {!isError && (
          <View style={{ flexDirection: 'row', gap: 10 }}>
            <View style={{ flex: 1 }}>
              <Button title="Начать чат" onPress={() => router.push('/(tabs)/chat')} />
            </View>
            <View style={{ flex: 1 }}>
              <Button title={`Повторить ${stats?.due_now ?? 0}`} variant="outline" onPress={() => router.push('/(tabs)/cards')} />
            </View>
          </View>
        )}

        {!isError && convs.length > 0 && (
          <View style={{ gap: 6 }}>
            <Body style={{ fontWeight: '600' }}>Недавние беседы</Body>
            {convs.map((c: Conversation) => (
              <Pressable
                key={c.id}
                onPress={() => router.push({ pathname: '/chat-detail', params: { id: String(c.id), title: c.title ?? '' } })}
              >
                <Card>
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <Body style={{ flex: 1 }} numberOfLines={1}>{c.title ?? 'Без названия'}</Body>
                    <Subtle>›</Subtle>
                  </View>
                </Card>
              </Pressable>
            ))}
          </View>
        )}

        {isLoading && !isError && <Subtle>Loading…</Subtle>}
      </ScrollView>
    </SafeAreaView>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  const t = useTokens();
  return (
    <View>
      <Subtle>{label}</Subtle>
      <Body style={{ fontSize: 28, fontWeight: '700', color: color ?? t.text }}>{value}</Body>
    </View>
  );
}

function SmallStat({ label, value }: { label: string; value: number }) {
  return (
    <View style={{ flex: 1 }}>
      <Card>
        <Body style={{ fontSize: 22, fontWeight: '700', textAlign: 'center' }}>{value}</Body>
        <Subtle style={{ textAlign: 'center' }}>{label}</Subtle>
      </Card>
    </View>
  );
}
