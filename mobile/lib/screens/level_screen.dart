import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../state/settings.dart';

const cefrScale = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
const ieltsBands = ['4.0', '4.5', '5.0', '5.5', '6.0', '6.5', '7.0', '7.5', '8.0', '8.5', '9.0'];

class LevelScreen extends StatefulWidget {
  const LevelScreen({super.key});
  @override
  State<LevelScreen> createState() => _LevelScreenState();
}

class _LevelScreenState extends State<LevelScreen> {
  Level? _level;
  bool _loading = true;
  bool _assessing = false;
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
      final l = await _api.getLevel();
      if (mounted) setState(() { _level = l; _loading = false; });
    } catch (_) {
      if (mounted) setState(() { _error = 'Нет связи с backend.'; _loading = false; });
    }
  }

  Future<void> _assess() async {
    setState(() => _assessing = true);
    try {
      final l = await _api.assessLevel();
      if (mounted) setState(() => _level = l);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _assessing = false);
    }
  }

  Future<void> _setTarget(String band) async {
    try {
      final l = await _api.setTarget(band);
      if (mounted) setState(() => _level = l);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text(_error!));
    final lvl = _level!;
    final a = lvl.assessment;
    final cs = Theme.of(context).colorScheme;
    final roadmapStale = a != null && lvl.targetBand != null && a.targetBand != lvl.targetBand;

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Target selector
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  const Text('Цель IELTS: '),
                  DropdownButton<String>(
                    value: ieltsBands.contains(lvl.targetBand) ? lvl.targetBand : null,
                    hint: const Text('—'),
                    items: ieltsBands.map((b) => DropdownMenuItem(value: b, child: Text(b))).toList(),
                    onChanged: (v) { if (v != null) _setTarget(v); },
                  ),
                  const Spacer(),
                  FilledButton.tonal(
                    onPressed: _assessing ? null : _assess,
                    child: Text(_assessing ? 'Оцениваю…' : (a != null ? 'Переоценить' : 'Оценить')),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          if (_assessing) ...[
            Card(
              color: Colors.blue.withValues(alpha: 0.08),
              child: const Padding(
                padding: EdgeInsets.all(12),
                child: Row(
                  children: [
                    SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Claude анализирует твою речь…',
                              style: TextStyle(fontWeight: FontWeight.w600)),
                          SizedBox(height: 2),
                          Text('Это занимает 60–120 секунд. Не закрывай экран.',
                              style: TextStyle(fontSize: 12, color: Colors.grey)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],

          if (a == null)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(20),
                child: Text('Уровень ещё не оценён. Нажми «Оценить» — Claude проанализирует '
                    'твою письменную речь по критериям IELTS и составит план.'),
              ),
            )
          else ...[
            if (roadmapStale)
              Card(
                color: Colors.blue.withValues(alpha: 0.08),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      Expanded(child: Text('Цель изменилась (план для ${a.targetBand}). '
                          'Переоцени, чтобы обновить роудмеп до ${lvl.targetBand}.', style: const TextStyle(fontSize: 13))),
                      const SizedBox(width: 8),
                      FilledButton(onPressed: _assessing ? null : _assess, child: const Text('Обновить')),
                    ],
                  ),
                ),
              ),

            // Headline + scale
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        _bigStat('CEFR', a.cefrLevel, cs.primary),
                        const SizedBox(width: 20),
                        _bigStat('IELTS', a.ieltsBand ?? '—', null),
                        const SizedBox(width: 20),
                        if (a.targetBand != null) _bigStat('Цель', a.targetBand!, Colors.green),
                        const Spacer(),
                        _ConfidenceChip(confidence: a.confidence),
                      ],
                    ),
                    const SizedBox(height: 12),
                    CefrScaleBar(currentLevel: a.cefrLevel),
                    const SizedBox(height: 12),
                    Text(a.summaryRu, style: const TextStyle(fontSize: 13)),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.amber.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        '⚠️ Оценка только по письменной речи в чате — не полный IELTS '
                        '(Listening/Reading не проверяются). Основано на ${a.basedOnMessages} сообщениях.',
                        style: const TextStyle(fontSize: 11),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            if (a.roadmap.isNotEmpty) ...[
              const SizedBox(height: 12),
              _RoadmapCard(roadmap: a.roadmap, target: a.targetBand),
            ],

            if (a.skills.isNotEmpty) ...[
              const SizedBox(height: 12),
              _SkillsCard(skills: a.skills),
            ],

            if (a.strengths.isNotEmpty) ...[
              const SizedBox(height: 12),
              _ListCard(title: 'Сильные стороны', items: a.strengths, bullet: '•', color: Colors.green),
            ],
            if (a.weaknesses.isNotEmpty) ...[
              const SizedBox(height: 12),
              _ListCard(title: 'Слабые места', items: a.weaknesses, bullet: '•', color: Colors.red),
            ],
            if (a.nextSteps.isNotEmpty) ...[
              const SizedBox(height: 12),
              _ListCard(title: 'Рекомендации', items: a.nextSteps, bullet: '→', color: cs.primary),
            ],
          ],
        ],
      ),
    );
  }

  Widget _bigStat(String label, String value, Color? color) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          Text(value, style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold, color: color)),
        ],
      );
}

class CefrScaleBar extends StatelessWidget {
  final String currentLevel;
  const CefrScaleBar({super.key, required this.currentLevel});
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final idx = cefrScale.indexOf(currentLevel);
    return Row(
      children: List.generate(cefrScale.length, (i) {
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
                    color: on
                        ? cs.primary
                        : passed
                            ? cs.primary.withValues(alpha: 0.4)
                            : cs.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
                const SizedBox(height: 4),
                Text(cefrScale[i],
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
    );
  }
}

class _ConfidenceChip extends StatelessWidget {
  final String confidence;
  const _ConfidenceChip({required this.confidence});
  @override
  Widget build(BuildContext context) {
    final map = {
      'low': ('низкая', Colors.amber),
      'medium': ('средняя', Colors.blue),
      'high': ('высокая', Colors.green),
    };
    final (label, color) = map[confidence] ?? ('—', Colors.grey);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text('надёжность: $label', style: TextStyle(fontSize: 11, color: color.shade900)),
    );
  }
}

class _RoadmapCard extends StatelessWidget {
  final List<RoadmapPhase> roadmap;
  final String? target;
  const _RoadmapCard({required this.roadmap, this.target});
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
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
              final i = e.key;
              final p = e.value;
              return Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Column(
                      children: [
                        CircleAvatar(radius: 13, backgroundColor: cs.primary, child: Text('${i + 1}', style: TextStyle(fontSize: 12, color: cs.onPrimary))),
                      ],
                    ),
                    const SizedBox(width: 10),
                    Expanded(
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
                                padding: const EdgeInsets.only(top: 2),
                                child: Text('› $act', style: const TextStyle(fontSize: 12)),
                              )),
                        ],
                      ),
                    ),
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

class _SkillsCard extends StatelessWidget {
  final List<Skill> skills;
  const _SkillsCard({required this.skills});
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Разбор по критериям', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 10),
            ...skills.map((s) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(child: Text(s.name, style: const TextStyle(fontWeight: FontWeight.w600))),
                          Text('${s.cefr ?? '—'}${s.ielts != null ? ' · IELTS ${s.ielts}' : ''}',
                              style: const TextStyle(fontSize: 12, color: Colors.grey)),
                        ],
                      ),
                      if (s.commentRu != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 2),
                          child: Text(s.commentRu!, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                        ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }
}

class _ListCard extends StatelessWidget {
  final String title;
  final List<String> items;
  final String bullet;
  final Color color;
  const _ListCard({required this.title, required this.items, required this.bullet, required this.color});
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            ...items.map((it) => Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(bullet, style: TextStyle(color: color, fontWeight: FontWeight.bold)),
                      const SizedBox(width: 8),
                      Expanded(child: Text(it, style: const TextStyle(fontSize: 13))),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }
}
