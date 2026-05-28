import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';

class ChatDetailScreen extends StatefulWidget {
  final int conversationId;
  final String? title;
  const ChatDetailScreen({super.key, required this.conversationId, this.title});
  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  List<Message> _messages = [];
  bool _loading = true;
  bool _busy = false;
  String _streaming = '';
  List<Correction> _streamCorr = [];

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final m = await _api.messages(widget.conversationId);
      if (mounted) setState(() { _messages = m; _loading = false; });
      _scrollDown();
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      }
    });
  }

  Future<void> _send() async {
    final text = _input.text.trim();
    if (text.isEmpty || _busy) return;
    _input.clear();
    setState(() {
      _busy = true;
      _streaming = '';
      _streamCorr = [];
      _messages = [..._messages, Message(id: -1, role: 'user', content: text)];
    });
    _scrollDown();
    try {
      await for (final ev in _api.chatStream(widget.conversationId, text)) {
        if (ev.type == 'token') {
          setState(() => _streaming += (ev.data['text'] ?? '').toString());
          _scrollDown();
        } else if (ev.type == 'corrections') {
          final items = (ev.data['items'] as List?) ?? [];
          setState(() => _streamCorr = items.map((e) => Correction.fromJson(e)).toList());
        } else if (ev.type == 'error') {
          setState(() => _streaming += '\n[ошибка: ${ev.data['detail']}]');
        }
      }
    } finally {
      await _load();
      if (mounted) setState(() { _busy = false; _streaming = ''; _streamCorr = []; });
    }
  }

  Future<void> _saveSession() async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Сохраняю сессию…')),
    );
    try {
      await _api.summarizeSession(widget.conversationId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Сессия сохранена в vault, слова → в колоду')),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Не удалось сохранить сессию')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title ?? 'Беседа', maxLines: 1, overflow: TextOverflow.ellipsis),
        actions: [
          IconButton(
            icon: const Icon(Icons.bookmark_add_outlined),
            tooltip: 'Сохранить сессию',
            onPressed: _messages.length >= 2 ? _saveSession : null,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : ListView(
                    controller: _scroll,
                    padding: const EdgeInsets.all(12),
                    children: [
                      ..._messages.map((m) => _Bubble(message: m)),
                      if (_streaming.isNotEmpty)
                        _Bubble(message: Message(id: -2, role: 'assistant', content: _streaming, corrections: _streamCorr)),
                    ],
                  ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(8, 4, 8, 8),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _input,
                      enabled: !_busy,
                      minLines: 1,
                      maxLines: 4,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _send(),
                      decoration: const InputDecoration(
                        hintText: 'Напиши на английском…',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _busy ? null : _send,
                    icon: _busy
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.send),
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

class _Bubble extends StatelessWidget {
  final Message message;
  const _Bubble({required this.message});
  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    final cs = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
      children: [
        Container(
          margin: const EdgeInsets.symmetric(vertical: 4),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
          decoration: BoxDecoration(
            color: isUser ? cs.primary : cs.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            message.content,
            style: TextStyle(color: isUser ? cs.onPrimary : cs.onSurface),
          ),
        ),
        if (!isUser && message.corrections.isNotEmpty)
          Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.all(10),
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.85),
            decoration: BoxDecoration(
              color: Colors.amber.withValues(alpha: 0.12),
              border: Border.all(color: Colors.amber.shade300),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Корректировки (${message.corrections.length})',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.amber.shade900)),
                const SizedBox(height: 4),
                ...message.corrections.map((c) => Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text.rich(TextSpan(children: [
                            TextSpan(
                              text: c.original,
                              style: const TextStyle(decoration: TextDecoration.lineThrough, color: Colors.red),
                            ),
                            const TextSpan(text: '  →  '),
                            TextSpan(
                              text: c.fixed,
                              style: const TextStyle(fontWeight: FontWeight.w600, color: Colors.green),
                            ),
                          ])),
                          Text(c.explanationRu, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                        ],
                      ),
                    )),
              ],
            ),
          ),
      ],
    );
  }
}
