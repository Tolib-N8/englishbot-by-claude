import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';

const _cefrScale = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
const _ieltsBands = ['4.0', '4.5', '5.0', '5.5', '6.0', '6.5', '7.0', '7.5', '8.0', '8.5', '9.0'];

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Level? _level;
  FlashcardStats? _stats;
  bool _loading = true;
  bool _assessing = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  ApiClient get _api => ApiClient(context.read<SettingsModel>().baseUrl);

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final level = await _api.getLevel();
      final stats = await _api.flashcardStats();
      if (mounted) setState(() { _level = level; _stats = stats; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = 'Нет связи с backend. Проверь адрес в настройках.'; _loading = false; });
    }
  }

  Future<void> _assess() async {
    setState(() => _assessing = true);
    try {
      final level = await _api.assessLevel();
      if (mounted) setState(() => _level = level);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _assessing = false);
    }
  }

  Future<void> _setTarget(String band) async {
    try {
      final level = await _api.setTarget(band);
      if (mounted) setState(() => _level = level);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return _ErrorBox(message: _error!, onRetry: _load);
    }
    final a = _level?.assessment;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _LevelCard(
            level: _level!,
            assessing: _assessing,
            onAssess: _assess,
            onSetTarget: _setTarget,
          ),
          const SizedBox(height: 16),
          _StatsRow(stats: _stats),
          if (a != null && a.roadmap.isNotEmpty) ...[
            const SizedBox(height: 16),
            _RoadmapCard(roadmap: a.roadmap, target: a.targetBand),
          ],
        ],
      ),
    );
  }
}

class _LevelCard extends StatelessWidget {
  final Level level;
  final bool assessing;
  final VoidCallback onAssess;
  final void Function(String) onSetTarget;
  const _LevelCard({
    required this.level,
    required this.assessing,
    required this.onAssess,
    required this.onSetTarget,
  });

  @override
  Widget build(BuildContext context) {
    final a = level.assessment;
    final idx = a != null ? _cefrScale.indexOf(a.cefrLevel) : -1;
    final cs = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Уровень — IELTS / CEFR', style: TextStyle(fontWeight: FontWeight.bold)),
                FilledButton.tonal(
                  onPressed: assessing ? null : onAssess,
                  child: Text(assessing ? 'Оцениваю…' : (a != null ? 'Переоценить' : 'Оценить')),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (a == null)
              const Text('Уровень ещё не оценён. Нажми «Оценить».')
            else ...[
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  _bigStat('CEFR', a.cefrLevel, cs.primary),
                  const SizedBox(width: 24),
                  _bigStat('IELTS', a.ieltsBand ?? '—', null),
                  const Spacer(),
                  _ConfidenceChip(confidence: a.confidence),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: List.generate(_cefrScale.length, (i) {
                  final on = i == idx;
                  final passed = i < idx;
                  return Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 2),
                      child: Column(
                        children: [
                          Container(
                            height: 6,
                            decoration: BoxDecoration(
                              color: on ? cs.primary : passed ? cs.primary.withValues(alpha: 0.4) : cs.surfaceContainerHighest,
                              borderRadius: BorderRadius.circular(3),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(_cefrScale[i],
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: on ? FontWeight.bold : FontWeight.normal,
                                color: on ? cs.primary : Colors.grey,
                              )),
                        ],
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 12),
              Text(a.summaryRu, style: const TextStyle(fontSize: 13)),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                const Text('Цель IELTS: '),
                DropdownButton<String>(
                  value: _ieltsBands.contains(level.targetBand) ? level.targetBand : null,
                  hint: const Text('—'),
                  items: _ieltsBands
                      .map((b) => DropdownMenuItem(value: b, child: Text(b)))
                      .toList(),
                  onChanged: (v) {
                    if (v != null) onSetTarget(v);
                  },
                ),
              ],
            ),
            if (a != null)
              const Text(
                '⚠️ Оценка только по письменной речи в чате — это не полный IELTS.',
                style: TextStyle(fontSize: 11, color: Colors.grey),
              ),
          ],
        ),
      ),
    );
  }

  Widget _bigStat(String label, String value, Color? color) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          Text(value, style: TextStyle(fontSize: 34, fontWeight: FontWeight.bold, color: color)),
        ],
      );
}

class _ConfidenceChip extends StatelessWidget {
  final String confidence;
  const _ConfidenceChip({required this.confidence});
  @override
  Widget build(BuildContext context) {
    final map = {
      'low': ('низкая надёжность', Colors.amber),
      'medium': ('средняя надёжность', Colors.blue),
      'high': ('высокая надёжность', Colors.green),
    };
    final (label, color) = map[confidence] ?? ('—', Colors.grey);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(label, style: TextStyle(fontSize: 11, color: color.shade900)),
    );
  }
}

class _StatsRow extends StatelessWidget {
  final FlashcardStats? stats;
  const _StatsRow({required this.stats});
  @override
  Widget build(BuildContext context) {
    final s = stats;
    return Row(
      children: [
        _stat('К повтору', '${s?.dueNow ?? 0}'),
        _stat('Сегодня', '${s?.reviewedToday ?? 0}'),
        _stat('Всего карт', '${s?.total ?? 0}'),
      ],
    );
  }

  Widget _stat(String label, String value) => Expanded(
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
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

class _RoadmapCard extends StatelessWidget {
  final List<RoadmapPhase> roadmap;
  final String? target;
  const _RoadmapCard({required this.roadmap, this.target});
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Роудмеп до IELTS ${target ?? ''}',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 12),
            ...roadmap.asMap().entries.map((e) {
              final p = e.value;
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(child: Text(p.title, style: const TextStyle(fontWeight: FontWeight.w600))),
                        if (p.estWeeks != null)
                          Text('~${p.estWeeks} нед', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                      ],
                    ),
                    if (p.targetRu != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text('🎯 ${p.targetRu}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                      ),
                    ...p.actionsRu.map((act) => Padding(
                          padding: const EdgeInsets.only(top: 2, left: 8),
                          child: Text('› $act', style: const TextStyle(fontSize: 12)),
                        )),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class _ErrorBox extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorBox({required this.message, required this.onRetry});
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            FilledButton(onPressed: onRetry, child: const Text('Повторить')),
          ],
        ),
      ),
    );
  }
}
