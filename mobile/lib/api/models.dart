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

class PronunciationWord {
  final String word;
  final String status; // matched | missed | substituted
  final String? heard;
  PronunciationWord({required this.word, required this.status, this.heard});
  factory PronunciationWord.fromJson(Map<String, dynamic> j) => PronunciationWord(
        word: j['word'] ?? '',
        status: j['status'] ?? 'missed',
        heard: j['heard'],
      );
}

class PronunciationResult {
  final int id;
  final String targetText;
  final String transcript;
  final double overallScore;
  final List<PronunciationWord> perWord;
  final String? tipRu;
  PronunciationResult({
    required this.id,
    required this.targetText,
    required this.transcript,
    required this.overallScore,
    required this.perWord,
    this.tipRu,
  });
  factory PronunciationResult.fromJson(Map<String, dynamic> j) => PronunciationResult(
        id: j['id'],
        targetText: j['target_text'] ?? '',
        transcript: j['transcript'] ?? '',
        overallScore: (j['overall_score'] as num?)?.toDouble() ?? 0.0,
        perWord: (j['per_word'] as List?)?.map((e) => PronunciationWord.fromJson(e)).toList() ?? const [],
        tipRu: j['tip_ru'],
      );
}

// ---------- IELTS Writing ----------

class WritingPromptModel {
  final String taskType;
  final String promptEn;
  final String? promptRu;
  final int minWords;
  WritingPromptModel({
    required this.taskType,
    required this.promptEn,
    this.promptRu,
    required this.minWords,
  });
  factory WritingPromptModel.fromJson(Map<String, dynamic> j) => WritingPromptModel(
        taskType: j['task_type'] ?? 'task2',
        promptEn: j['prompt_en'] ?? '',
        promptRu: j['prompt_ru'],
        minWords: j['min_words'] ?? 250,
      );
}

class WritingCriterion {
  final String name;
  final String? band;
  final String? commentRu;
  WritingCriterion({required this.name, this.band, this.commentRu});
  factory WritingCriterion.fromJson(Map<String, dynamic> j) => WritingCriterion(
        name: j['name'] ?? '',
        band: j['band'],
        commentRu: j['comment_ru'],
      );
}

class WritingCorrection {
  final String original;
  final String fixed;
  final String? explanationRu;
  WritingCorrection({required this.original, required this.fixed, this.explanationRu});
  factory WritingCorrection.fromJson(Map<String, dynamic> j) => WritingCorrection(
        original: j['original'] ?? '',
        fixed: j['fixed'] ?? '',
        explanationRu: j['explanation_ru'],
      );
}

class WritingResult {
  final int id;
  final String taskType;
  final String promptEn;
  final String? promptRu;
  final int minWords;
  final String userText;
  final int wordCount;
  final String? overallBand;
  final List<WritingCriterion> criteria;
  final List<WritingCorrection> corrections;
  final String? tipRu;
  final String createdAt;
  WritingResult({
    required this.id,
    required this.taskType,
    required this.promptEn,
    this.promptRu,
    required this.minWords,
    required this.userText,
    required this.wordCount,
    this.overallBand,
    required this.criteria,
    required this.corrections,
    this.tipRu,
    required this.createdAt,
  });
  factory WritingResult.fromJson(Map<String, dynamic> j) => WritingResult(
        id: j['id'],
        taskType: j['task_type'] ?? '',
        promptEn: j['prompt_en'] ?? '',
        promptRu: j['prompt_ru'],
        minWords: j['min_words'] ?? 0,
        userText: j['user_text'] ?? '',
        wordCount: j['word_count'] ?? 0,
        overallBand: j['overall_band'],
        criteria: (j['criteria'] as List?)?.map((e) => WritingCriterion.fromJson(e)).toList() ?? const [],
        corrections: (j['corrections'] as List?)?.map((e) => WritingCorrection.fromJson(e)).toList() ?? const [],
        tipRu: j['tip_ru'],
        createdAt: j['created_at'] ?? '',
      );
}

class WritingHistoryItem {
  final int id;
  final String taskType;
  final int wordCount;
  final String? overallBand;
  final String createdAt;
  WritingHistoryItem({
    required this.id,
    required this.taskType,
    required this.wordCount,
    this.overallBand,
    required this.createdAt,
  });
  factory WritingHistoryItem.fromJson(Map<String, dynamic> j) => WritingHistoryItem(
        id: j['id'],
        taskType: j['task_type'] ?? '',
        wordCount: j['word_count'] ?? 0,
        overallBand: j['overall_band'],
        createdAt: j['created_at'] ?? '',
      );
}

// ---------- Lessons & Templates ----------

class LessonSummary {
  final String slug;
  final String title;
  final String summary;
  final int order;
  final bool read;
  final bool generated;
  LessonSummary({
    required this.slug,
    required this.title,
    required this.summary,
    required this.order,
    required this.read,
    required this.generated,
  });
  factory LessonSummary.fromJson(Map<String, dynamic> j) => LessonSummary(
        slug: j['slug'] ?? '',
        title: j['title'] ?? '',
        summary: j['summary'] ?? '',
        order: j['order'] ?? 0,
        read: j['read'] ?? false,
        generated: j['generated'] ?? false,
      );
}

class LessonDetail {
  final String slug;
  final String title;
  final String summary;
  final int order;
  final String bodyMd;
  final bool read;
  final String? prevSlug;
  final String? nextSlug;
  LessonDetail({
    required this.slug,
    required this.title,
    required this.summary,
    required this.order,
    required this.bodyMd,
    required this.read,
    this.prevSlug,
    this.nextSlug,
  });
  factory LessonDetail.fromJson(Map<String, dynamic> j) => LessonDetail(
        slug: j['slug'] ?? '',
        title: j['title'] ?? '',
        summary: j['summary'] ?? '',
        order: j['order'] ?? 0,
        bodyMd: j['body_md'] ?? '',
        read: j['read'] ?? false,
        prevSlug: j['prev_slug'],
        nextSlug: j['next_slug'],
      );
}

class TemplateSummary {
  final String slug;
  final String title;
  final String summary;
  final int order;
  final bool generated;
  TemplateSummary({
    required this.slug,
    required this.title,
    required this.summary,
    required this.order,
    required this.generated,
  });
  factory TemplateSummary.fromJson(Map<String, dynamic> j) => TemplateSummary(
        slug: j['slug'] ?? '',
        title: j['title'] ?? '',
        summary: j['summary'] ?? '',
        order: j['order'] ?? 0,
        generated: j['generated'] ?? false,
      );
}

class TemplateDetail {
  final String slug;
  final String title;
  final String summary;
  final int order;
  final String bodyMd;
  final String? prevSlug;
  final String? nextSlug;
  TemplateDetail({
    required this.slug,
    required this.title,
    required this.summary,
    required this.order,
    required this.bodyMd,
    this.prevSlug,
    this.nextSlug,
  });
  factory TemplateDetail.fromJson(Map<String, dynamic> j) => TemplateDetail(
        slug: j['slug'] ?? '',
        title: j['title'] ?? '',
        summary: j['summary'] ?? '',
        order: j['order'] ?? 0,
        bodyMd: j['body_md'] ?? '',
        prevSlug: j['prev_slug'],
        nextSlug: j['next_slug'],
      );
}
