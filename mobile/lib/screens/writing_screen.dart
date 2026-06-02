import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';
import 'writing_lessons_screen.dart';
import 'writing_templates_screen.dart';

class WritingScreen extends StatefulWidget {
  const WritingScreen({super.key});
  @override
  State<WritingScreen> createState() => _WritingScreenState();
}

class _WritingScreenState extends State<WritingScreen> {
  String _task = 'task2';
  WritingPromptModel? _prompt;
  WritingResult? _result;
  bool _loadingPrompt = false;
  bool _submitting = false;
  String? _error;
  final TextEditingController _ctrl = TextEditingController();
  List<WritingHistoryItem> _history = [];

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  static final RegExp _wordRe = RegExp(r"\b[\w'-]+\b");
  int _countWords(String s) => _wordRe.allMatches(s).length;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    try {
      final h = await _api.writingHistory();
      if (mounted) setState(() => _history = h);
    } catch (_) {}
  }

  Future<void> _newPrompt() async {
    setState(() {
      _loadingPrompt = true;
      _prompt = null;
      _result = null;
      _error = null;
      _ctrl.clear();
    });
    try {
      final p = await _api.writingPrompt(_task);
      if (mounted) setState(() => _prompt = p);
    } catch (_) {
      if (mounted) setState(() => _error = 'Не удалось получить задание');
    } finally {
      if (mounted) setState(() => _loadingPrompt = false);
    }
  }

  Future<void> _submit() async {
    final p = _prompt;
    if (p == null) return;
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final r = await _api.writingSubmit(
        taskType: _task,
        promptEn: p.promptEn,
        promptRu: p.promptRu,
        minWords: p.minWords,
        userText: _ctrl.text,
      );
      if (mounted) {
        setState(() => _result = r);
        _loadHistory();
      }
    } catch (_) {
      if (mounted) setState(() => _error = 'Не удалось получить оценку');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Color _bandColor(String? band) {
    final n = double.tryParse(band ?? '') ?? 0;
    if (n >= 7) return Colors.green.shade700;
    if (n >= 6) return Colors.blue.shade700;
    if (n >= 5) return Colors.amber.shade700;
    return Colors.red.shade700;
  }

  @override
  Widget build(BuildContext context) {
    final p = _prompt;
    final r = _result;
    final wc = _countWords(_ctrl.text);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Top: guides + templates
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const LessonsListScreen()),
                ),
                icon: const Icon(Icons.menu_book_outlined),
                label: const Text('Гайды'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const TemplatesListScreen()),
                ),
                icon: const Icon(Icons.dashboard_outlined),
                label: const Text('Шаблоны'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Task picker
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: SegmentedButton<String>(
                        segments: const [
                          ButtonSegment(value: 'task2', label: Text('Task 2 (эссе)')),
                          ButtonSegment(value: 'task1_academic', label: Text('Task 1')),
                        ],
                        selected: {_task},
                        onSelectionChanged: (s) => setState(() => _task = s.first),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    FilledButton(
                      onPressed: _loadingPrompt ? null : _newPrompt,
                      child: Text(_loadingPrompt
                          ? 'Генерирую…'
                          : _prompt == null
                              ? 'Получить задание'
                              : 'Новое задание'),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _task == 'task2' ? '~40 мин · мин. 250 слов' : '~20 мин · мин. 150 слов',
                      style: const TextStyle(fontSize: 11, color: Colors.grey),
                    ),
                  ],
                ),
                if (_loadingPrompt)
                  const Padding(
                    padding: EdgeInsets.only(top: 8),
                    child: Row(
                      children: [
                        SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
                        SizedBox(width: 8),
                        Text('Claude составляет задание (5–15 сек)…',
                            style: TextStyle(fontSize: 12, color: Colors.grey)),
                      ],
                    ),
                  ),
                if (p != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 10),
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.grey.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(p.promptEn, style: const TextStyle(fontSize: 15)),
                          if (p.promptRu != null) ...[
                            const SizedBox(height: 6),
                            Text(p.promptRu!, style: const TextStyle(fontSize: 12, color: Colors.grey, fontStyle: FontStyle.italic)),
                          ],
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),

        // Editor
        if (p != null && r == null) ...[
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: _ctrl,
                    onChanged: (_) => setState(() {}),
                    minLines: 10,
                    maxLines: 30,
                    decoration: const InputDecoration(
                      hintText: 'Write your answer here…',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Слов: $wc / ${p.minWords}',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: wc >= p.minWords ? Colors.green.shade700 : null,
                              ),
                            ),
                            const SizedBox(height: 4),
                            LinearProgressIndicator(
                              value: (wc / p.minWords).clamp(0.0, 1.0),
                              minHeight: 4,
                              color: wc >= p.minWords ? Colors.green : null,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 10),
                      FilledButton(
                        onPressed: (_submitting || wc < 20) ? null : _submit,
                        child: Text(_submitting ? 'Оцениваю…' : 'Отправить'),
                      ),
                    ],
                  ),
                  if (_submitting)
                    Container(
                      margin: const EdgeInsets.only(top: 10),
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.blue.withValues(alpha: 0.10),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: const [
                          SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                          SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Экзаменатор-Claude проверяет работу…',
                                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                                SizedBox(height: 2),
                                Text('30–90 секунд', style: TextStyle(fontSize: 11, color: Colors.grey)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(_error!, style: const TextStyle(color: Colors.red, fontSize: 13)),
                    ),
                ],
              ),
            ),
          ),
        ],

        // Result
        if (r != null) ...[
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: const [
                          Text('Overall band', style: TextStyle(fontSize: 11, color: Colors.grey)),
                        ],
                      ),
                      const SizedBox(width: 6),
                      Text(
                        r.overallBand ?? '—',
                        style: TextStyle(fontSize: 36, fontWeight: FontWeight.bold, color: _bandColor(r.overallBand)),
                      ),
                      const Spacer(),
                      OutlinedButton(
                        onPressed: () => setState(() => _result = null),
                        child: const Text('Новая'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text('${r.wordCount} слов · мин. ${r.minWords}',
                      style: const TextStyle(fontSize: 11, color: Colors.grey)),
                  const SizedBox(height: 12),
                  ...r.criteria.map((c) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            border: Border.all(color: Colors.grey.shade300),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(child: Text(c.name, style: const TextStyle(fontWeight: FontWeight.w600))),
                                  Text(
                                    c.band ?? '—',
                                    style: TextStyle(fontWeight: FontWeight.bold, color: _bandColor(c.band)),
                                  ),
                                ],
                              ),
                              if (c.commentRu != null)
                                Padding(
                                  padding: const EdgeInsets.only(top: 4),
                                  child: Text(c.commentRu!, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                                ),
                            ],
                          ),
                        ),
                      )),
                  if (r.tipRu != null)
                    Container(
                      margin: const EdgeInsets.only(top: 4),
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.blue.withValues(alpha: 0.10),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text('💡 ${r.tipRu}', style: const TextStyle(fontSize: 13)),
                    ),
                ],
              ),
            ),
          ),
          if (r.corrections.isNotEmpty) ...[
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Исправления (${r.corrections.length})',
                        style: const TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    ...r.corrections.map((c) => Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text.rich(TextSpan(children: [
                                TextSpan(
                                  text: c.original,
                                  style: const TextStyle(
                                    decoration: TextDecoration.lineThrough,
                                    color: Colors.red,
                                  ),
                                ),
                                const TextSpan(text: '  →  '),
                                TextSpan(
                                  text: c.fixed,
                                  style: TextStyle(
                                    fontWeight: FontWeight.w600,
                                    color: Colors.green.shade700,
                                  ),
                                ),
                              ])),
                              if (c.explanationRu != null)
                                Padding(
                                  padding: const EdgeInsets.only(top: 2),
                                  child: Text(
                                    c.explanationRu!,
                                    style: const TextStyle(fontSize: 12, color: Colors.grey),
                                  ),
                                ),
                            ],
                          ),
                        )),
                  ],
                ),
              ),
            ),
          ],
        ],

        // History
        if (_history.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text('Прошлые работы', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
          const SizedBox(height: 6),
          ..._history.take(10).map((h) => Card(
                child: ListTile(
                  dense: true,
                  leading: Text(
                    h.overallBand ?? '—',
                    style: TextStyle(fontWeight: FontWeight.bold, color: _bandColor(h.overallBand)),
                  ),
                  title: Text(
                    h.taskType == 'task2' ? 'Task 2' : 'Task 1',
                    style: const TextStyle(fontSize: 14),
                  ),
                  subtitle: Text('${h.wordCount} слов'),
                  trailing: Text(
                    h.createdAt.split('T').first,
                    style: const TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                  onTap: () async {
                    final r = await _api.writingGet(h.id);
                    if (!mounted) return;
                    setState(() {
                      _prompt = WritingPromptModel(
                        taskType: r.taskType,
                        promptEn: r.promptEn,
                        promptRu: r.promptRu,
                        minWords: r.minWords,
                      );
                      _ctrl.text = r.userText;
                      _task = r.taskType;
                      _result = r;
                    });
                  },
                ),
              )),
        ],
      ],
    );
  }
}
