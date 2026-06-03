import { ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Body, Heading, useTokens } from '@/components/ui';

export default function ChatTab() {
  const t = useTokens();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: t.bg }}>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 12 }}>
        <Heading>Chat</Heading>
        <Body>В разработке.</Body>
      </ScrollView>
    </SafeAreaView>
  );
}
