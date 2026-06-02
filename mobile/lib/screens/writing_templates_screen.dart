import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';

class TemplatesListScreen extends StatefulWidget {
  const TemplatesListScreen({super.key});
  @override
  State<TemplatesListScreen> createState() => _TemplatesListScreenState();
}

class _TemplatesListScreenState extends State<TemplatesListScreen> {
  List<TemplateSummary> _items = [];
  bool _loading = true;

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final l = await _api.templates();
      if (mounted) setState(() { _items = l; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Шаблоны Task 2')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Padding(
                  padding: EdgeInsets.only(bottom: 12),
                  child: Text(
                    'Готовые скелеты с [PLACEHOLDERS] и объяснениями для каждого типа вопросов',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                ),
                ..._items.map((t) => Card(
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: t.generated ? Colors.blue.shade100 : Colors.grey.shade300,
                          child: Text(
                            '${t.order}',
                            style: TextStyle(
                              color: t.generated ? Colors.blue.shade800 : Colors.grey.shade700,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        title: Text(t.title, style: const TextStyle(fontWeight: FontWeight.w600)),
                        subtitle: Text(t.summary, maxLines: 2, overflow: TextOverflow.ellipsis),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () async {
                          await Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => TemplateDetailScreen(slug: t.slug)),
                          );
                          _load();
                        },
                      ),
                    )),
              ],
            ),
    );
  }
}

class TemplateDetailScreen extends StatefulWidget {
  final String slug;
  const TemplateDetailScreen({super.key, required this.slug});
  @override
  State<TemplateDetailScreen> createState() => _TemplateDetailScreenState();
}

class _TemplateDetailScreenState extends State<TemplateDetailScreen> {
  TemplateDetail? _t;
  bool _loading = true;
  String? _error;

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  @override
  void initState() {
    super.initState();
    _load(widget.slug);
  }

  Future<void> _load(String slug) async {
    setState(() { _loading = true; _error = null; _t = null; });
    try {
      final t = await _api.template(slug);
      if (mounted) setState(() { _t = t; _loading = false; });
    } catch (_) {
      if (mounted) setState(() { _error = 'Не удалось загрузить шаблон'; _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = _t;
    return Scaffold(
      appBar: AppBar(title: Text(t?.title ?? 'Загрузка…', maxLines: 1, overflow: TextOverflow.ellipsis)),
      body: _loading
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: const [
                    CircularProgressIndicator(),
                    SizedBox(height: 16),
                    Text('Claude собирает шаблон', style: TextStyle(fontWeight: FontWeight.w600)),
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
                        data: t!.bodyMd,
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
                            if (t.prevSlug != null)
                              OutlinedButton(
                                onPressed: () => _load(t.prevSlug!),
                                child: const Text('← Назад'),
                              ),
                            const Spacer(),
                            if (t.nextSlug != null)
                              FilledButton(
                                onPressed: () => _load(t.nextSlug!),
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
