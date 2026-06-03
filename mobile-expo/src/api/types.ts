// Mirrors the backend Pydantic schemas (the bits we actually consume).
// Add fields here as we wire more screens.

export type Conversation = {
  id: number;
  title: string | null;
  mode: string;
  created_at: string;
  updated_at: string;
};

export type Correction = {
  original: string;
  fixed: string;
  explanation_ru: string;
};

export type Message = {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | string;
  content: string;
  corrections_json: Correction[] | null;
  created_at: string;
};

export type ConversationDetail = Conversation & { messages: Message[] };

export type FlashcardStats = {
  total: number;
  due_now: number;
  reviewed_today: number;
  new_today: number;
};

export type Flashcard = {
  id: number;
  word_en: string;
  translation_ru: string;
  example_en: string | null;
  example_ru: string | null;
  part_of_speech: string | null;
};

export type RoadmapPhase = {
  title: string;
  skill: string | null;
  target_ru: string | null;
  actions_ru: string[];
  est_weeks: number | null;
};

export type Skill = {
  name: string;
  cefr: string | null;
  ielts: string | null;
  comment_ru: string | null;
};

export type Evidence = { quote: string; issue_ru: string | null };

export type Assessment = {
  cefr_level: string;
  ielts_band: string | null;
  confidence: string;
  summary_ru: string;
  skills: Skill[];
  strengths: string[];
  weaknesses: string[];
  next_steps: string[];
  evidence: Evidence[];
  roadmap: RoadmapPhase[];
  target_band: string | null;
  based_on_messages: number;
  based_on_words: number;
  created_at: string;
};

export type LevelOut = {
  assessment: Assessment | null;
  target_band: string | null;
  words_total: number;
  words_mastered: number;
  topics: number;
  sessions: number;
  conversations: number;
};

// --- exercises -----------------------------------------------------------

export type ExerciseType =
  | 'fill_blank'
  | 'mcq'
  | 'translate_ru_en'
  | 'translate_en_ru';

export type Exercise = {
  id: number;
  topic: string;
  type: ExerciseType;
  prompt: string;
  prompt_ru: string | null;
  choices_json: string[] | null;
};

export type TopicSuggestion = { topic: string; source: string };

export type AttemptResult = {
  is_correct: boolean;
  feedback_ru: string | null;
  answer: string;
  explanation_ru: string | null;
};

// --- writing -------------------------------------------------------------

export type WritingTaskType = 'task2' | 'task1_academic';

export type WritingPrompt = {
  task_type: WritingTaskType;
  prompt_en: string;
  prompt_ru: string | null;
  min_words: number;
};

export type WritingCriterion = {
  name: string;
  band: string | null;
  comment_ru: string | null;
};

export type WritingCorrection = {
  original: string;
  fixed: string;
  explanation_ru: string | null;
};

export type WritingResult = {
  id: number;
  task_type: string;
  prompt_en: string;
  prompt_ru: string | null;
  min_words: number;
  user_text: string;
  word_count: number;
  overall_band: string | null;
  criteria: WritingCriterion[];
  corrections: WritingCorrection[];
  tip_ru: string | null;
  created_at: string;
};

export type LessonSummary = {
  slug: string;
  title: string;
  summary: string;
  order: number;
  read: boolean;
  generated: boolean;
};

export type LessonDetail = LessonSummary & {
  body_md: string;
  prev_slug: string | null;
  next_slug: string | null;
};

export type TemplateSummary = Omit<LessonSummary, 'read'>;
export type TemplateDetail = TemplateSummary & {
  body_md: string;
  prev_slug: string | null;
  next_slug: string | null;
};

// --- pronunciation -------------------------------------------------------

export type PronunciationWord = {
  word: string;
  status: 'matched' | 'missed' | 'substituted' | string;
  heard?: string | null;
};

export type PronunciationResult = {
  id: number;
  target_text: string;
  transcript: string;
  overall_score: number;
  per_word: PronunciationWord[];
  tip_ru: string | null;
};

// --- SSE chat ------------------------------------------------------------

export type ChatStreamEvent =
  | { type: 'user_message_saved'; id: number }
  | { type: 'token'; text: string }
  | { type: 'corrections'; items: Correction[] }
  | { type: 'done'; message_id: number }
  | { type: 'error'; detail: string };
