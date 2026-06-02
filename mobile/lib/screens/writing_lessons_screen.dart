import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';

class LessonsListScreen extends StatefulWidget {
  const LessonsListScreen({super.key});
  @override
  State<LessonsListScreen> createState() => _LessonsListScreenState();
}

class _LessonsListScreenState extends State<LessonsListScreen> {
  List<LessonSummary> _lessons = [];
  bool _loading = true;

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final l = await _api.lessons();
      if (mounted) setState(() { _lessons = l; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final readCount = _lessons.where((l) => l.read).length;
    return Scaffold(
      appBar: AppBar(title: const Text('Гайды IELTS Writing')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Text(
                      'Курс из ${_lessons.length} уроков · прочитано $readCount / ${_lessons.length}',
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ),
                  ..._lessons.map((l) => Card(
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: l.read
                                ? Colors.green.shade100
                                : l.generated
                                    ? Colors.blue.shade100
                                    : Colors.grey.shade300,
                            child: Text(
                              l.read ? '✓' : '${l.order}',
                              style: TextStyle(
                                color: l.read
                                    ? Colors.green.shade800
                                    : l.generated
                                        ? Colors.blue.shade800
                                        : Colors.grey.shade700,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          title: Text(l.title, style: const TextStyle(fontWeight: FontWeight.w600)),
                          subtitle: Text(l.summary, maxLines: 2, overflow: TextOverflow.ellipsis),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () async {
                            await Navigator.of(context).push(
                              MaterialPageRoute(builder: (_) => LessonDetailScreen(slug: l.slug)),
                            );
                            _load();
                          },
                        ),
                      )),
                ],
              ),
            ),
    );
  }
}

class LessonDetailScreen extends StatefulWidget {
  final String slug;
  const LessonDetailScreen({super.key, required this.slug});
  @override
  State<LessonDetailScreen> createState() => _LessonDetailScreenState();
}

class _LessonDetailScreenState extends State<LessonDetailScreen> {
  LessonDetail? _lesson;
  bool _loading = true;
  bool _markingRead = false;
  String? _error;

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  @override
  void initState() {
    super.initState();
    _load(widget.slug);
  }

  Future<void> _load(String slug) async {
    setState(() { _loading = true; _error = null; _lesson = null; });
    try {
      final l = await _api.lesson(slug);
      if (mounted) setState(() { _lesson = l; _loading = false; });
    } catch (_) {
      if (mounted) setState(() { _error = 'Не удалось загрузить урок'; _loading = false; });
    }
  }

  Future<void> _markRead() async {
    if (_lesson == null) return;
    setState(() => _markingRead = true);
    try {
      final l = await _api.lessonMarkRead(_lesson!.slug);
      if (mounted) setState(() => _lesson = l);
    } catch (_) {} finally {
      if (mounted) setState(() => _markingRead = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = _lesson;
    return Scaffold(
      appBar: AppBar(title: Text(l?.title ?? 'Загрузка…', maxLines: 1, overflow: TextOverflow.ellipsis)),
      body: _loading
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: const [
                    CircularProgressIndicator(),
                    SizedBox(height: 16),
                    Text('Claude готовит урок', style: TextStyle(fontWeight: FontWeight.w600)),
                    SizedBox(height: 4),
                    Text('Первый раз — 30-60 секунд', style: TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ),
              ),
            )
          : _error != null
              ? Center(child: Text(_error!))
              : Column(
                  children: [
                    Expanded(
                      child: Markdown(
                        data: l!.bodyMd,
                        padding: const EdgeInsets.all(16),
                        selectable: true,
                      ),
                    ),
                    SafeArea(
                      top: false,
                      child: Padding(
                        padding: const EdgeInsets.all(8),
                        child: Row(
                          children: [
                            if (l.prevSlug != null)
                              OutlinedButton(
                                onPressed: () => _load(l.prevSlug!),
                                child: const Text('← Назад'),
                              ),
                            const SizedBox(width: 8),
                            if (!l.read)
                              OutlinedButton(
                                onPressed: _markingRead ? null : _markRead,
                                child: Text(_markingRead ? '…' : '✓ Прочитано'),
                              ),
                            const Spacer(),
                            if (l.nextSlug != null)
                              FilledButton(
                                onPressed: () async {
                                  if (!l.read) await _markRead();
                                  if (mounted) _load(l.nextSlug!);
                                },
                                child: const Text('Дальше →'),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }
}
