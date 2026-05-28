import 'package:flutter_test/flutter_test.dart';

import 'package:englishbot/api/models.dart';

void main() {
  test('Level.fromJson parses with no assessment', () {
    final level = Level.fromJson({
      'assessment': null,
      'target_band': '6.5',
      'words_total': 12,
      'words_mastered': 0,
      'topics': 5,
      'sessions': 1,
      'conversations': 1,
    });
    expect(level.assessment, isNull);
    expect(level.targetBand, '6.5');
    expect(level.wordsTotal, 12);
  });

  test('Assessment.fromJson parses roadmap phases', () {
    final a = Assessment.fromJson({
      'cefr_level': 'B1',
      'ielts_band': '5.0',
      'confidence': 'low',
      'summary_ru': 'тест',
      'skills': [],
      'strengths': [],
      'weaknesses': [],
      'next_steps': [],
      'roadmap': [
        {
          'title': 'Этап 1',
          'skill': 'Grammar',
          'target_ru': 'цель',
          'actions_ru': ['a', 'b'],
          'est_weeks': 2,
        }
      ],
      'target_band': '6.5',
      'based_on_messages': 6,
      'based_on_words': 95,
      'created_at': '2026-05-29',
    });
    expect(a.cefrLevel, 'B1');
    expect(a.roadmap.length, 1);
    expect(a.roadmap.first.actionsRu.length, 2);
  });
}
