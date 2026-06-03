import axios, { type AxiosInstance } from 'axios';

import type {
  Assessment,
  AttemptResult,
  ChatStreamEvent,
  Conversation,
  ConversationDetail,
  Exercise,
  Flashcard,
  FlashcardStats,
  LessonDetail,
  LessonSummary,
  LevelOut,
  PronunciationResult,
  TemplateDetail,
  TemplateSummary,
  TopicSuggestion,
  WritingPrompt,
  WritingResult,
  WritingTaskType,
} from './types';

export function makeClient(baseUrl: string): AxiosInstance {
  return axios.create({
    baseURL: baseUrl,
    headers: { 'Content-Type': 'application/json' },
    timeout: 200_000,
  });
}

// -------- API surface (one wrapper per route we use) --------------------

export const api = {
  health: (c: AxiosInstance) =>
    c.get<{ status: string }>('/healthz').then((r) => r.data),

  // Level + assessment
  getLevel: (c: AxiosInstance) =>
    c.get<LevelOut>('/api/v1/level').then((r) => r.data),
  assessLevel: (c: AxiosInstance) =>
    c.post<LevelOut>('/api/v1/level/assess').then((r) => r.data),
  setTarget: (c: AxiosInstance, target_band: string) =>
    c.patch<LevelOut>('/api/v1/level/target', { target_band }).then((r) => r.data),

  // Flashcards
  flashcardStats: (c: AxiosInstance) =>
    c.get<FlashcardStats>('/api/v1/flashcards/stats').then((r) => r.data),
  dueCards: (c: AxiosInstance, limit = 50) =>
    c.get<Flashcard[]>('/api/v1/flashcards/due', { params: { limit } }).then((r) => r.data),
  review: (c: AxiosInstance, id: number, quality: 0 | 3 | 4 | 5) =>
    c.post(`/api/v1/flashcards/${id}/review`, { quality }).then((r) => r.data),

  // Conversations
  conversations: (c: AxiosInstance) =>
    c.get<Conversation[]>('/api/v1/conversations').then((r) => r.data),
  createConversation: (c: AxiosInstance) =>
    c.post<Conversation>('/api/v1/conversations', {}).then((r) => r.data),
  conversation: (c: AxiosInstance, id: number) =>
    c.get<ConversationDetail>(`/api/v1/conversations/${id}`).then((r) => r.data),
  summarizeSession: (c: AxiosInstance, id: number) =>
    c.post(`/api/v1/notes/summarize/${id}`).then((r) => r.data),

  // Grammar
  exerciseTopics: (c: AxiosInstance) =>
    c.get<TopicSuggestion[]>('/api/v1/exercises/topics').then((r) => r.data),
  generateExercises: (c: AxiosInstance, topic: string, count: number) =>
    c.post<Exercise[]>('/api/v1/exercises/generate', { topic, count }).then((r) => r.data),
  attempt: (c: AxiosInstance, id: number, user_answer: string) =>
    c.post<AttemptResult>(`/api/v1/exercises/${id}/attempt`, { user_answer }).then((r) => r.data),

  // Writing
  writingPrompt: (c: AxiosInstance, task_type: WritingTaskType) =>
    c.post<WritingPrompt>('/api/v1/writing/prompt', { task_type }).then((r) => r.data),
  writingSubmit: (c: AxiosInstance, body: WritingPrompt & { user_text: string }) =>
    c.post<WritingResult>('/api/v1/writing/submit', body).then((r) => r.data),
  writingHistory: (c: AxiosInstance) =>
    c.get<WritingResult[]>('/api/v1/writing').then((r) => r.data),
  writingGet: (c: AxiosInstance, id: number) =>
    c.get<WritingResult>(`/api/v1/writing/${id}`).then((r) => r.data),

  // Lessons + Templates
  lessons: (c: AxiosInstance) =>
    c.get<LessonSummary[]>('/api/v1/writing/lessons').then((r) => r.data),
  lesson: (c: AxiosInstance, slug: string) =>
    c.get<LessonDetail>(`/api/v1/writing/lessons/${slug}`).then((r) => r.data),
  lessonMarkRead: (c: AxiosInstance, slug: string) =>
    c.post<LessonDetail>(`/api/v1/writing/lessons/${slug}/read`).then((r) => r.data),
  templates: (c: AxiosInstance) =>
    c.get<TemplateSummary[]>('/api/v1/writing/templates').then((r) => r.data),
  template: (c: AxiosInstance, slug: string) =>
    c.get<TemplateDetail>(`/api/v1/writing/templates/${slug}`).then((r) => r.data),

  // Pronunciation
  practicePhrase: (c: AxiosInstance) =>
    c.get<{ phrase: string }>('/api/v1/pronounce/practice').then((r) => r.data.phrase),
  uploadPronunciation: async (c: AxiosInstance, audioUri: string, targetText: string) => {
    const form = new FormData();
    form.append('target_text', targetText);
    // React Native FormData accepts the file object form { uri, name, type }.
    // Types are lax here on purpose.
    form.append('audio', {
      uri: audioUri,
      name: 'rec.m4a',
      type: 'audio/m4a',
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any);
    const res = await c.post<PronunciationResult>('/api/v1/pronounce/transcribe', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      transformRequest: (d) => d, // axios would otherwise JSON-serialise FormData
    });
    return res.data;
  },
};

// -------- SSE chat streaming via fetch ----------------------------------
// React Native's stock EventSource is missing — we use streamed fetch
// + line splitting. Works on both iOS and Android in modern Expo SDKs.

export async function streamChat(
  baseUrl: string,
  body: { conversation_id: number; content: string },
  onEvent: (e: ChatStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${baseUrl}/api/v1/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
    onEvent({ type: 'error', detail: `HTTP ${res.status}` });
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let idx: number;
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const parsed = parseFrame(frame);
      if (parsed) onEvent(parsed);
    }
  }
}

function parseFrame(frame: string): ChatStreamEvent | null {
  let event = 'message';
  const lines: string[] = [];
  for (const ln of frame.split('\n')) {
    if (ln.startsWith('event:')) event = ln.slice(6).trim();
    else if (ln.startsWith('data:')) lines.push(ln.slice(5).trim());
  }
  if (!lines.length) return null;
  try {
    const data = JSON.parse(lines.join('\n'));
    return { type: event as ChatStreamEvent['type'], ...data };
  } catch {
    return null;
  }
}

// Tiny re-export so screens don't need to import axios.
export { makeClient as _makeClient };

// Sub-typing helper for callers
export type Assessment_ = Assessment; // suppress unused import lint
