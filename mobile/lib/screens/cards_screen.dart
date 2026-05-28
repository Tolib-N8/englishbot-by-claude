import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';

class CardsScreen extends StatefulWidget {
  const CardsScreen({super.key});
  @override
  State<CardsScreen> createState() => _CardsScreenState();
}

class _CardsScreenState extends State<CardsScreen> {
  List<Flashcard> _due = [];
  bool _loading = true;
  bool _revealed = false;
  bool _busy = false;
  String? _error;

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  static const _buttons = [
    (0, 'Again', Colors.red),
    (3, 'Hard', Colors.orange),
    (4, 'Good', Colors.green),
    (5, 'Easy', Colors.blue),
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final due = await _api.dueCards(limit: 50);
      if (mounted) setState(() { _due = due; _loading = false; _revealed = false; });
    } catch (_) {
      if (mounted) setState(() { _error = 'Нет связи с backend.'; _loading = false; });
    }
  }

  Future<void> _review(int quality) async {
    if (_due.isEmpty || _busy) return;
    setState(() => _busy = true);
    final card = _due.first;
    try {
      await _api.review(card.id, quality);
      if (mounted) {
        setState(() {
          _due = _due.sublist(1);
          _revealed = false;
          _busy = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text(_error!));
    if (_due.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.check_circle_outline, size: 48, color: Colors.green),
            const SizedBox(height: 12),
            const Text('Всё повторено! Карточек к повтору нет.'),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: _load, child: const Text('Обновить')),
          ],
        ),
      );
    }

    final card = _due.first;
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Text('${_due.length} к повтору', style: const TextStyle(color: Colors.grey)),
          const SizedBox(height: 12),
          Expanded(
            child: Card(
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(card.wordEn, style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
                      if (card.partOfSpeech != null)
                        Text(card.partOfSpeech!, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                      if (_revealed) ...[
                        const Divider(height: 32),
                        Text(card.translationRu, style: const TextStyle(fontSize: 22)),
                        if (card.exampleEn != null) ...[
                          const SizedBox(height: 12),
                          Text('“${card.exampleEn}”', style: const TextStyle(fontStyle: FontStyle.italic, color: Colors.grey)),
                          if (card.exampleRu != null)
                            Text(card.exampleRu!, style: const TextStyle(color: Colors.grey)),
                        ],
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (!_revealed)
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () => setState(() => _revealed = true),
                child: const Text('Показать ответ'),
              ),
            )
          else
            Row(
              children: _buttons.map((b) {
                final (q, label, color) = b;
                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 2),
                    child: FilledButton(
                      style: FilledButton.styleFrom(backgroundColor: color),
                      onPressed: _busy ? null : () => _review(q),
                      child: Text(label, style: const TextStyle(fontSize: 12)),
                    ),
                  ),
                );
              }).toList(),
            ),
        ],
      ),
    );
  }
}
