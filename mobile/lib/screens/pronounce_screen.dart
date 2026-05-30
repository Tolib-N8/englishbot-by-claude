import 'dart:io';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';
import 'package:record/record.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';

class PronounceScreen extends StatefulWidget {
  const PronounceScreen({super.key});
  @override
  State<PronounceScreen> createState() => _PronounceScreenState();
}

class _PronounceScreenState extends State<PronounceScreen> {
  final _recorder = AudioRecorder();
  String? _phrase;
  bool _loadingPhrase = false;
  bool _recording = false;
  bool _processing = false;
  PronunciationResult? _result;
  String? _error;

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  @override
  void initState() {
    super.initState();
    _newPhrase();
  }

  @override
  void dispose() {
    _recorder.dispose();
    super.dispose();
  }

  Future<void> _newPhrase() async {
    setState(() {
      _loadingPhrase = true;
      _result = null;
      _error = null;
    });
    try {
      final p = await _api.practicePhrase();
      if (mounted) setState(() => _phrase = p);
    } catch (_) {
      if (mounted) setState(() => _error = 'Не удалось получить фразу');
    } finally {
      if (mounted) setState(() => _loadingPhrase = false);
    }
  }

  Future<void> _startRecording() async {
    if (!await _recorder.hasPermission()) {
      setState(() => _error = 'Нет доступа к микрофону');
      return;
    }
    final dir = await getTemporaryDirectory();
    final path = '${dir.path}/pronounce_${DateTime.now().millisecondsSinceEpoch}.m4a';
    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.aacLc, sampleRate: 16000, numChannels: 1),
      path: path,
    );
    setState(() {
      _recording = true;
      _error = null;
      _result = null;
    });
  }

  Future<void> _stopRecording() async {
    final path = await _recorder.stop();
    setState(() => _recording = false);
    if (path == null) return;
    await _upload(path);
  }

  Future<void> _upload(String path) async {
    setState(() => _processing = true);
    try {
      final r = await _api.uploadPronunciation(path, _phrase ?? '');
      if (mounted) setState(() => _result = r);
    } catch (_) {
      if (mounted) setState(() => _error = 'Не удалось отправить запись');
    } finally {
      // Best-effort cleanup of temp file.
      try { await File(path).delete(); } catch (_) {}
      if (mounted) setState(() => _processing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scorePct = _result != null ? (_result!.overallScore * 100).round() : 0;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            const Expanded(child: Text('Произношение', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold))),
            OutlinedButton(
              onPressed: _loadingPhrase || _recording || _processing ? null : _newPhrase,
              child: Text(_loadingPhrase ? '...' : 'Новая фраза'),
            ),
          ],
        ),
        const SizedBox(height: 16),

        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Прочитай вслух', style: TextStyle(fontSize: 12, color: Colors.grey)),
                const SizedBox(height: 8),
                Text(_phrase ?? '...', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w500, height: 1.4)),
                const SizedBox(height: 16),
                Row(
                  children: [
                    if (!_recording)
                      FilledButton.icon(
                        onPressed: (_processing || _phrase == null) ? null : _startRecording,
                        icon: const Icon(Icons.mic),
                        label: const Text('Запись'),
                      )
                    else
                      FilledButton.icon(
                        onPressed: _stopRecording,
                        style: FilledButton.styleFrom(backgroundColor: Colors.red),
                        icon: const Icon(Icons.stop),
                        label: const Text('Стоп'),
                      ),
                    const SizedBox(width: 12),
                    if (_processing)
                      const Row(
                        children: [
                          SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                          SizedBox(width: 8),
                          Text('Анализирую...', style: TextStyle(fontSize: 12, color: Colors.grey)),
                        ],
                      ),
                  ],
                ),
                if (_error != null) Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(_error!, style: const TextStyle(color: Colors.red, fontSize: 13)),
                ),
              ],
            ),
          ),
        ),

        if (_result != null) ...[
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Text('Результат', style: TextStyle(fontWeight: FontWeight.bold)),
                      const Spacer(),
                      Text(
                        '$scorePct%',
                        style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: scorePct >= 80 ? Colors.green : scorePct >= 50 ? Colors.amber : Colors.red,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text('Whisper расслышал:', style: TextStyle(fontSize: 12, color: Colors.grey)),
                  Container(
                    margin: const EdgeInsets.only(top: 4, bottom: 12),
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.grey.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      _result!.transcript.isEmpty ? '(тишина)' : _result!.transcript,
                      style: const TextStyle(fontFamily: 'monospace'),
                    ),
                  ),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: _result!.perWord.map((w) {
                      final color = switch (w.status) {
                        'matched' => Colors.green,
                        'substituted' => Colors.amber,
                        _ => Colors.red,
                      };
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: color.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          w.heard != null ? '${w.word} → ${w.heard}' : w.word,
                          style: TextStyle(color: color.shade900, fontSize: 13),
                        ),
                      );
                    }).toList(),
                  ),
                  if (_result!.tipRu != null) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.blue.withValues(alpha: 0.10),
                        border: Border.all(color: Colors.blue.withValues(alpha: 0.4)),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text('💡 ${_result!.tipRu}', style: const TextStyle(fontSize: 13)),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}
