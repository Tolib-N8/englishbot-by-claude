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
