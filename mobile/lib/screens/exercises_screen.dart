import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';

class ExercisesScreen extends StatefulWidget {
  const ExercisesScreen({super.key});
  @override
  State<ExercisesScreen> createState() => _ExercisesScreenState();
}

class _ExercisesScreenState extends State<ExercisesScreen> {
  List<TopicSuggestion> _topics = [];
  String? _selectedTopic;
  List<Exercise> _batch = [];
  bool _loadingTopics = true;
  bool _generating = false;

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  @override
  void initState() {
    super.initState();
    _loadTopics();
  }

  Future<void> _loadTopics() async {
    try {
      final t = await _api.exerciseTopics();
      if (mounted) setState(() { _topics = t; _loadingTopics = false; });
    } catch (_) {
      if (mounted) setState(() => _loadingTopics = false);
    }
  }

  Future<void> _generate() async {
    if (_selectedTopic == null) return;
    setState(() { _generating = true; _batch = []; });
    try {
      final ex = await _api.generateExercises(_selectedTopic!, 6);
      if (mounted) setState(() => _batch = ex);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Не удалось сгенерировать. Попробуй ещё раз.')),
        );
      }
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loadingTopics) return const Center(child: CircularProgressIndicator());
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Тема (★ — из твоего плана)', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _topics.map((t) {
            final sel = _selectedTopic == t.topic;
            return ChoiceChip(
              label: Text(
                '${t.source == 'roadmap' ? '★ ' : ''}${t.topic}',
                style: const TextStyle(fontSize: 12),
              ),
              selected: sel,
              onSelected: (_) => setState(() => _selectedTopic = t.topic),
            );
          }).toList(),
        ),
        const SizedBox(height: 12),
        FilledButton(
          onPressed: (_selectedTopic == null || _generating) ? null : _generate,
          child: Text(_generating ? 'Генерирую…' : 'Создать 6 заданий'),
        ),
        const SizedBox(height: 16),
        ..._batch.map((e) => _ExerciseTile(api: _api, exercise: e)),
        if (_batch.isEmpty && !_generating)
          const Padding(
            padding: EdgeInsets.only(top: 24),
            child: Text('Выбери тему и нажми «Создать».', style: TextStyle(color: Colors.grey)),
          ),
      ],
    );
  }
}

class _ExerciseTile extends StatefulWidget {
  final ApiClient api;
  final Exercise exercise;
  const _ExerciseTile({required this.api, required this.exercise});
  @override
  State<_ExerciseTile> createState() => _ExerciseTileState();
}

class _ExerciseTileState extends State<_ExerciseTile> {
  final _ctrl = TextEditingController();
  AttemptResult? _result;
  bool _busy = false;

  static const _labels = {
    'fill_blank': 'Заполни пропуск',
    'mcq': 'Выбери вариант',
    'translate_ru_en': 'Перевод RU → EN',
    'translate_en_ru': 'Перевод EN → RU',
  };

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Future<void> _submit(String value) async {
    if (value.trim().isEmpty || _busy || _result != null) return;
    setState(() => _busy = true);
    try {
      final r = await widget.api.attempt(widget.exercise.id, value);
      if (mounted) setState(() => _result = r);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final e = widget.exercise;
    final prompt = e.type == 'translate_ru_en' ? (e.promptRu ?? e.prompt) : e.prompt;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_labels[e.type] ?? e.type,
                style: const TextStyle(fontSize: 11, color: Colors.grey, letterSpacing: 0.5)),
            const SizedBox(height: 6),
            Text(prompt, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
            const SizedBox(height: 10),
            if (_result == null && e.type == 'mcq' && e.choices != null)
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: e.choices!
                    .map((c) => OutlinedButton(
                          onPressed: _busy ? null : () => _submit(c),
                          child: Text(c),
                        ))
                    .toList(),
              )
            else if (_result == null)
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _ctrl,
                      enabled: !_busy,
                      onSubmitted: _submit,
                      decoration: const InputDecoration(
                        hintText: 'Твой ответ…',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    onPressed: _busy ? null : () => _submit(_ctrl.text),
                    child: Text(_busy ? '…' : 'OK'),
                  ),
                ],
              ),
            if (_result != null) _Feedback(result: _result!),
          ],
        ),
      ),
    );
  }
}

class _Feedback extends StatelessWidget {
  final AttemptResult result;
  const _Feedback({required this.result});
  @override
  Widget build(BuildContext context) {
    final ok = result.isCorrect;
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: (ok ? Colors.green : Colors.red).withValues(alpha: 0.1),
        border: Border.all(color: (ok ? Colors.green : Colors.red).withValues(alpha: 0.4)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(ok ? '✓ Верно!' : '✗ Неверно', style: const TextStyle(fontWeight: FontWeight.bold)),
          if (!ok) Text('Правильный ответ: ${result.answer}'),
          if (result.feedbackRu != null)
            Padding(padding: const EdgeInsets.only(top: 2), child: Text(result.feedbackRu!, style: const TextStyle(fontSize: 13, color: Colors.grey))),
          if (result.explanationRu != null)
            Padding(padding: const EdgeInsets.only(top: 2), child: Text('💡 ${result.explanationRu!}', style: const TextStyle(fontSize: 13, color: Colors.grey))),
        ],
      ),
    );
  }
}
