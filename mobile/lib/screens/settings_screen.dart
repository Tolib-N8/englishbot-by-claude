import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../state/settings.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController _ctrl;
  String? _status;
  bool _testing = false;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: context.read<SettingsModel>().baseUrl);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    await context.read<SettingsModel>().setBaseUrl(_ctrl.text);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Сохранено')),
      );
    }
  }

  Future<void> _test() async {
    setState(() {
      _testing = true;
      _status = null;
    });
    final ok = await ApiClient(_ctrl.text.trim().replaceAll(RegExp(r'/+$'), '')).health();
    if (mounted) {
      setState(() {
        _testing = false;
        _status = ok ? 'OK — backend доступен ✓' : 'Не удалось подключиться ✗';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Настройки')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Адрес backend', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text(
              'Например, Tailscale-адрес твоего компьютера: http://100.x.y.z:8000',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _ctrl,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'http://100.64.0.1:8000',
              ),
              keyboardType: TextInputType.url,
              autocorrect: false,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                FilledButton(onPressed: _save, child: const Text('Сохранить')),
                const SizedBox(width: 12),
                OutlinedButton(
                  onPressed: _testing ? null : _test,
                  child: Text(_testing ? 'Проверяю…' : 'Проверить связь'),
                ),
              ],
            ),
            if (_status != null) ...[
              const SizedBox(height: 12),
              Text(_status!),
            ],
            const SizedBox(height: 24),
            const Text(
              'Backend должен быть запущен на компьютере (englishbot start) там, '
              'где выполнен вход в Claude Code.',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
