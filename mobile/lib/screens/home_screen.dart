import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';
import 'level_screen.dart' show CefrScaleBar;
import 'chat_detail_screen.dart';

class HomeScreen extends StatefulWidget {
  /// Switch the root bottom-nav tab (0 Home, 1 Level, 2 Chat, 3 Grammar, 4 Cards).
  final void Function(int index)? onNavigate;
  const HomeScreen({super.key, this.onNavigate});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Level? _level;
  FlashcardStats? _stats;
  List<Conversation> _convos = [];
  bool _loading = true;
  String? _error;

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final level = await _api.getLevel();
      final stats = await _api.flashcardStats();
      final convos = await _api.conversations();
      if (mounted) {
        setState(() {
          _level = level;
          _stats = stats;
          _convos = convos;
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() { _error = 'Нет связи с backend. Проверь адрес в настройках (⚙️).'; _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
              const SizedBox(height: 12),
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              FilledButton(onPressed: _load, child: const Text('Повторить')),
            ],
          ),
        ),
      );
    }

    final due = _stats?.dueNow ?? 0;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _LevelSummary(level: _level!, onOpen: () => widget.onNavigate?.call(1)),
          const SizedBox(height: 16),

          // Stats
          Row(
            children: [
              _statCard('К повтору', '$due'),
              _statCard('Сегодня', '${_stats?.reviewedToday ?? 0}'),
              _statCard('Всего карт', '${_stats?.total ?? 0}'),
            ],
          ),
          const SizedBox(height: 16),

          // Quick actions
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: () => widget.onNavigate?.call(2),
                  icon: const Icon(Icons.chat_bubble_outline),
                  label: const Text('Начать чат'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton.tonalIcon(
                  onPressed: due > 0 ? () => widget.onNavigate?.call(4) : null,
                  icon: const Icon(Icons.style_outlined),
                  label: Text('Повторить $due'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Recent conversations
          const Text('Недавние беседы', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          if (_convos.isEmpty)
            const Text('Пока нет бесед.', style: TextStyle(color: Colors.grey))
          else
            ..._convos.take(5).map((c) => Card(
                  child: ListTile(
                    title: Text(c.title ?? 'Без названия', maxLines: 1, overflow: TextOverflow.ellipsis),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () async {
                      await Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => ChatDetailScreen(conversationId: c.id, title: c.title),
                        ),
                      );
                      _load();
                    },
                  ),
                )),
        ],
      ),
    );
  }

  Widget _statCard(String label, String value) => Expanded(
        child: Card(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
            child: Column(
              children: [
                Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
              ],
            ),
          ),
        ),
      );
}

class _LevelSummary extends StatelessWidget {
  final Level level;
  final VoidCallback onOpen;
  const _LevelSummary({required this.level, required this.onOpen});

  @override
  Widget build(BuildContext context) {
    final a = level.assessment;
    final cs = Theme.of(context).colorScheme;
    return Card(
      child: InkWell(
        onTap: onOpen,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Expanded(
                    child: Text('Уровень — IELTS / CEFR', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                  Text('Подробнее', style: TextStyle(color: cs.primary, fontSize: 13)),
                  Icon(Icons.chevron_right, size: 18, color: cs.primary),
                ],
              ),
              const SizedBox(height: 12),
              if (a == null)
                const Text('Уровень ещё не оценён — открой, чтобы оценить.')
              else ...[
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    _big('CEFR', a.cefrLevel, cs.primary),
                    const SizedBox(width: 24),
                    _big('IELTS', a.ieltsBand ?? '—', null),
                    const Spacer(),
                    if (level.targetBand != null) _big('Цель', level.targetBand!, Colors.green),
                  ],
                ),
                const SizedBox(height: 12),
                CefrScaleBar(currentLevel: a.cefrLevel),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _big(String label, String value, Color? color) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          Text(value, style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: color)),
        ],
      );
}
