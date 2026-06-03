import { ScrollView } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Body, Button, Heading, Subtle, useTokens } from '@/components/ui';

export default function ChatDetailScreen() {
  const t = useTokens();
  const router = useRouter();
  const { id, title } = useLocalSearchParams<{ id?: string; title?: string }>();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: t.bg }}>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 12 }}>
        <Heading>{title || 'Беседа'}</Heading>
        <Subtle>conversation #{id}</Subtle>
        <Body>В разработке.</Body>
        <Button title="← Назад" variant="ghost" onPress={() => router.back()} />
      </ScrollView>
    </SafeAreaView>
  );
}
