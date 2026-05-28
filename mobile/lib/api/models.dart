class Skill {
  final String name;
  final String? cefr;
  final String? ielts;
  final String? commentRu;
  Skill({required this.name, this.cefr, this.ielts, this.commentRu});
  factory Skill.fromJson(Map<String, dynamic> j) => Skill(
        name: j['name'] ?? '',
        cefr: j['cefr'],
        ielts: j['ielts'],
        commentRu: j['comment_ru'],
      );
}

class RoadmapPhase {
  final String title;
  final String? skill;
  final String? targetRu;
  final List<String> actionsRu;
  final int? estWeeks;
  RoadmapPhase({
    required this.title,
    this.skill,
    this.targetRu,
    this.actionsRu = const [],
    this.estWeeks,
  });
  factory RoadmapPhase.fromJson(Map<String, dynamic> j) => RoadmapPhase(
        title: j['title'] ?? '',
        skill: j['skill'],
        targetRu: j['target_ru'],
        actionsRu: (j['actions_ru'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        estWeeks: j['est_weeks'],
      );
}

class Assessment {
  final String cefrLevel;
  final String? ieltsBand;
  final String confidence;
  final String summaryRu;
  final List<Skill> skills;
  final List<String> strengths;
  final List<String> weaknesses;
  final List<String> nextSteps;
  final List<RoadmapPhase> roadmap;
  final String? targetBand;
  final int basedOnMessages;
  final int basedOnWords;
  final String createdAt;

  Assessment({
    required this.cefrLevel,
    this.ieltsBand,
    required this.confidence,
    required this.summaryRu,
    required this.skills,
    required this.strengths,
    required this.weaknesses,
    required this.nextSteps,
    required this.roadmap,
    this.targetBand,
    required this.basedOnMessages,
    required this.basedOnWords,
    required this.createdAt,
  });

  factory Assessment.fromJson(Map<String, dynamic> j) => Assessment(
        cefrLevel: j['cefr_level'] ?? 'A1',
        ieltsBand: j['ielts_band'],
        confidence: j['confidence'] ?? 'low',
        summaryRu: j['summary_ru'] ?? '',
        skills: (j['skills'] as List?)?.map((e) => Skill.fromJson(e)).toList() ?? const [],
        strengths: (j['strengths'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        weaknesses: (j['weaknesses'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        nextSteps: (j['next_steps'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        roadmap: (j['roadmap'] as List?)?.map((e) => RoadmapPhase.fromJson(e)).toList() ?? const [],
        targetBand: j['target_band'],
        basedOnMessages: j['based_on_messages'] ?? 0,
        basedOnWords: j['based_on_words'] ?? 0,
        createdAt: j['created_at'] ?? '',
      );
}

class Level {
  final Assessment? assessment;
  final String? targetBand;
  final int wordsTotal;
  final int wordsMastered;
  final int topics;
  final int sessions;
  final int conversations;
  Level({
    this.assessment,
    this.targetBand,
    required this.wordsTotal,
    required this.wordsMastered,
    required this.topics,
    required this.sessions,
    required this.conversations,
  });
  factory Level.fromJson(Map<String, dynamic> j) => Level(
        assessment: j['assessment'] != null ? Assessment.fromJson(j['assessment']) : null,
        targetBand: j['target_band'],
        wordsTotal: j['words_total'] ?? 0,
        wordsMastered: j['words_mastered'] ?? 0,
        topics: j['topics'] ?? 0,
        sessions: j['sessions'] ?? 0,
        conversations: j['conversations'] ?? 0,
      );
}

class FlashcardStats {
  final int total;
  final int dueNow;
  final int reviewedToday;
  final int newToday;
  FlashcardStats({
    required this.total,
    required this.dueNow,
    required this.reviewedToday,
    required this.newToday,
  });
  factory FlashcardStats.fromJson(Map<String, dynamic> j) => FlashcardStats(
        total: j['total'] ?? 0,
        dueNow: j['due_now'] ?? 0,
        reviewedToday: j['reviewed_today'] ?? 0,
        newToday: j['new_today'] ?? 0,
      );
}

class Flashcard {
  final int id;
  final String wordEn;
  final String translationRu;
  final String? exampleEn;
  final String? exampleRu;
  final String? partOfSpeech;
  Flashcard({
    required this.id,
    required this.wordEn,
    required this.translationRu,
    this.exampleEn,
    this.exampleRu,
    this.partOfSpeech,
  });
  factory Flashcard.fromJson(Map<String, dynamic> j) => Flashcard(
        id: j['id'],
        wordEn: j['word_en'] ?? '',
        translationRu: j['translation_ru'] ?? '',
        exampleEn: j['example_en'],
        exampleRu: j['example_ru'],
        partOfSpeech: j['part_of_speech'],
      );
}

class Conversation {
  final int id;
  final String? title;
  final String updatedAt;
  Conversation({required this.id, this.title, required this.updatedAt});
  factory Conversation.fromJson(Map<String, dynamic> j) => Conversation(
        id: j['id'],
        title: j['title'],
        updatedAt: j['updated_at'] ?? '',
      );
}

class Correction {
  final String original;
  final String fixed;
  final String explanationRu;
  Correction({required this.original, required this.fixed, required this.explanationRu});
  factory Correction.fromJson(Map<String, dynamic> j) => Correction(
        original: j['original'] ?? '',
        fixed: j['fixed'] ?? '',
        explanationRu: j['explanation_ru'] ?? '',
      );
}

class Message {
  final int id;
  final String role;
  final String content;
  final List<Correction> corrections;
  Message({required this.id, required this.role, required this.content, this.corrections = const []});
  factory Message.fromJson(Map<String, dynamic> j) => Message(
        id: j['id'],
        role: j['role'] ?? '',
        content: j['content'] ?? '',
        corrections: (j['corrections_json'] as List?)?.map((e) => Correction.fromJson(e)).toList() ?? const [],
      );
}

class TopicSuggestion {
  final String topic;
  final String source;
  TopicSuggestion({required this.topic, required this.source});
  factory TopicSuggestion.fromJson(Map<String, dynamic> j) =>
      TopicSuggestion(topic: j['topic'] ?? '', source: j['source'] ?? 'common');
}

class Exercise {
  final int id;
  final String topic;
  final String type;
  final String prompt;
  final String? promptRu;
  final List<String>? choices;
  Exercise({
    required this.id,
    required this.topic,
    required this.type,
    required this.prompt,
    this.promptRu,
    this.choices,
  });
  factory Exercise.fromJson(Map<String, dynamic> j) => Exercise(
        id: j['id'],
        topic: j['topic'] ?? '',
        type: j['type'] ?? '',
        prompt: j['prompt'] ?? '',
        promptRu: j['prompt_ru'],
        choices: (j['choices_json'] as List?)?.map((e) => e.toString()).toList(),
      );
}

class AttemptResult {
  final bool isCorrect;
  final String? feedbackRu;
  final String answer;
  final String? explanationRu;
  AttemptResult({required this.isCorrect, this.feedbackRu, required this.answer, this.explanationRu});
  factory AttemptResult.fromJson(Map<String, dynamic> j) => AttemptResult(
        isCorrect: j['is_correct'] ?? false,
        feedbackRu: j['feedback_ru'],
        answer: j['answer'] ?? '',
        explanationRu: j['explanation_ru'],
      );
}

/// One server-sent event from the chat stream.
class ChatEvent {
  final String type; // token | corrections | done | error | user_message_saved
  final Map<String, dynamic> data;
  ChatEvent(this.type, this.data);
}
