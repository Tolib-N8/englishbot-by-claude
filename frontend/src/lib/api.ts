import axios from "axios";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

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
  role: "user" | "assistant" | "system";
  content: string;
  corrections_json: Correction[] | null;
  created_at: string;
};

export type ConversationDetail = Conversation & {
  messages: Message[];
};

export type Vocabulary = {
  id: number;
  word_en: string;
  lemma_en: string | null;
  translation_ru: string;
  example_en: string | null;
  example_ru: string | null;
  part_of_speech: string | null;
  cefr_level: string | null;
  source: string | null;
  notes: string | null;
  created_at: string;
  has_flashcard: boolean;
};

export type Flashcard = {
  id: number;
  vocabulary_id: number;
  ease: number;
  interval_days: number;
  repetitions: number;
  due_date: string;
  last_reviewed_at: string | null;
  lapses: number;
  suspended: boolean;
  word_en: string;
  translation_ru: string;
  example_en: string | null;
  example_ru: string | null;
  part_of_speech: string | null;
};

export type FlashcardStats = {
  total: number;
  due_now: number;
  reviewed_today: number;
  new_today: number;
};

export type AppSettings = {
  level: string;
  native_language: string;
  model: string;
};

export type Skill = {
  name: string;
  cefr: string | null;
  ielts: string | null;
  comment_ru: string | null;
};

export type Evidence = {
  quote: string;
  issue_ru: string | null;
};

export type RoadmapPhase = {
  title: string;
  skill: string | null;
  target_ru: string | null;
  actions_ru: string[];
  est_weeks: number | null;
};

export type Assessment = {
  cefr_level: string;
  ielts_band: string | null;
  confidence: "low" | "medium" | "high" | string;
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

export type Level = {
  assessment: Assessment | null;
  target_band: string | null;
  words_total: number;
  words_mastered: number;
  topics: number;
  sessions: number;
  conversations: number;
};

export type ExerciseType = "fill_blank" | "mcq" | "translate_ru_en" | "translate_en_ru";

export type Exercise = {
  id: number;
  topic: string;
  level: string;
  type: ExerciseType;
  prompt: string;
  prompt_ru: string | null;
  choices_json: string[] | null;
  created_at: string;
  attempted: boolean;
  last_correct: boolean | null;
};

export type AttemptResult = {
  is_correct: boolean;
  feedback_ru: string | null;
  answer: string;
  explanation_ru: string | null;
};

export type TopicSuggestion = {
  topic: string;
  source: "roadmap" | "common" | string;
};

export type ExerciseStats = {
  total: number;
  attempted: number;
  correct: number;
  accuracy: number;
};

export type NoteSummary = {
  path: string;
  folder: string;
  name: string;
  title: string;
  type: string | null;
  cefr: string | null;
  date: string | null;
};

export type NoteDetail = NoteSummary & {
  frontmatter: Record<string, unknown>;
  body: string;
  links: string[];
};

export type SummarizeResponse = {
  confirmation: string;
  new_note_paths: string[];
};
