import { Tabs } from 'expo-router';
import { useColorScheme } from 'react-native';
import {
  BookOpen,
  MessageSquare,
  PencilRuler,
  FileText,
  Mic,
  Layers,
} from 'lucide-react-native';

export default function TabsLayout() {
  const scheme = useColorScheme();
  const tint = scheme === 'dark' ? '#60A5FA' : '#2563EB';
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: tint,
        tabBarStyle: { borderTopWidth: 0.5, height: 60, paddingBottom: 6 },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size }) => <BookOpen color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: 'Chat',
          tabBarIcon: ({ color, size }) => <MessageSquare color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="grammar"
        options={{
          title: 'Grammar',
          tabBarIcon: ({ color, size }) => <PencilRuler color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="writing"
        options={{
          title: 'Writing',
          tabBarIcon: ({ color, size }) => <FileText color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="speak"
        options={{
          title: 'Speak',
          tabBarIcon: ({ color, size }) => <Mic color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="cards"
        options={{
          title: 'Cards',
          tabBarIcon: ({ color, size }) => <Layers color={color} size={size} />,
        }}
      />
    </Tabs>
  );
}
