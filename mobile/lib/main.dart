import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'api/client.dart';
import 'state/settings.dart';
import 'screens/home_screen.dart';
import 'screens/chat_list_screen.dart';
import 'screens/exercises_screen.dart';
import 'screens/cards_screen.dart';
import 'screens/settings_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final settings = SettingsModel()..load();
  runApp(
    ChangeNotifierProvider.value(value: settings, child: const EnglishBotApp()),
  );
}

/// Convenience: build an ApiClient from the current settings.
ApiClient apiOf(BuildContext context) =>
    ApiClient(context.read<SettingsModel>().baseUrl);

class EnglishBotApp extends StatelessWidget {
  const EnglishBotApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'English Tutor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2563EB)),
        useMaterial3: true,
      ),
      home: const RootShell(),
    );
  }
}

class RootShell extends StatefulWidget {
  const RootShell({super.key});
  @override
  State<RootShell> createState() => _RootShellState();
}

class _RootShellState extends State<RootShell> {
  int _index = 0;

  static const _titles = ['Home', 'Chat', 'Grammar', 'Cards'];

  Widget _body() {
    switch (_index) {
      case 1:
        return const ChatListScreen();
      case 2:
        return const ExercisesScreen();
      case 3:
        return const CardsScreen();
      default:
        return const HomeScreen();
    }
  }

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsModel>();
    if (!settings.loaded) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_index]),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const SettingsScreen()),
            ),
          ),
        ],
      ),
      body: _body(),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.chat_outlined), selectedIcon: Icon(Icons.chat), label: 'Chat'),
          NavigationDestination(icon: Icon(Icons.school_outlined), selectedIcon: Icon(Icons.school), label: 'Grammar'),
          NavigationDestination(icon: Icon(Icons.style_outlined), selectedIcon: Icon(Icons.style), label: 'Cards'),
        ],
      ),
    );
  }
}
