import { ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Body, Button, Heading, useTokens } from '@/components/ui';
import { useRouter } from 'expo-router';

export default function LevelScreen() {
  const t = useTokens();
  const router = useRouter();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: t.bg }}>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 12 }}>
        <Heading>Уровень</Heading>
        <Body>Будет полная оценка и роудмеп.</Body>
        <Button title="← Назад" variant="ghost" onPress={() => router.back()} />
      </ScrollView>
    </SafeAreaView>
  );
}
