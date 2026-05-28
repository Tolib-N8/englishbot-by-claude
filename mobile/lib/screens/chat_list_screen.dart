import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';
import 'chat_detail_screen.dart';

class ChatListScreen extends StatefulWidget {
  const ChatListScreen({super.key});
  @override
  State<ChatListScreen> createState() => _ChatListScreenState();
}

class _ChatListScreenState extends State<ChatListScreen> {
  List<Conversation>? _convos;
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
      final c = await _api.conversations();
      if (mounted) setState(() { _convos = c; _loading = false; });
    } catch (_) {
      if (mounted) setState(() { _error = 'Нет связи с backend.'; _loading = false; });
    }
  }

  Future<void> _newChat() async {
    try {
      final c = await _api.createConversation();
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => ChatDetailScreen(conversationId: c.id, title: c.title)),
      );
      _load();
    } catch (_) {}
  }

  Future<void> _open(Conversation c) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ChatDetailScreen(conversationId: c.id, title: c.title)),
    );
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: (_convos ?? []).isEmpty
                      ? ListView(children: const [
                          Padding(
                            padding: EdgeInsets.all(32),
                            child: Center(child: Text('Пока нет бесед. Нажми + чтобы начать.')),
                          )
                        ])
                      : ListView.separated(
                          itemCount: _convos!.length,
                          separatorBuilder: (_, __) => const Divider(height: 1),
                          itemBuilder: (_, i) {
                            final c = _convos![i];
                            return ListTile(
                              title: Text(c.title ?? 'Без названия', maxLines: 1, overflow: TextOverflow.ellipsis),
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () => _open(c),
                            );
                          },
                        ),
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: _newChat,
        child: const Icon(Icons.add),
      ),
    );
  }
}
