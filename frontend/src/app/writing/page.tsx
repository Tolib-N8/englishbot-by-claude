"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type WritingListItem, type WritingPrompt, type WritingResult, type WritingTaskType } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const TASKS: { value: WritingTaskType; label: string; minutes: number }[] = [
  { value: "task2", label: "Task 2 (эссе)", minutes: 40 },
  { value: "task1_academic", label: "Task 1 Academic", minutes: 20 },
];

function countWords(s: string): number {
  return (s.match(/\b[\w'-]+\b/g) ?? []).length;
}

function bandColor(b: string | null | undefined): string {
  const n = parseFloat(b || "0");
  if (n >= 7) return "text-emerald-600";
  if (n >= 6) return "text-blue-600";
  if (n >= 5) return "text-amber-600";
  return "text-destructive";
}

// Render the user's text with corrections highlighted in red (strike) +
// suggested fix shown in tooltip.
function HighlightedText({ text, corrections }: { text: string; corrections: { original: string; fixed: string; explanation_ru: string | null }[] }) {
  // Greedy left-to-right replacement: find each correction's first remaining
  // occurrence and slice. Order matters; ignore corrections that don't match.
  const segments: Array<{ kind: "plain" | "fix"; text: string; fix?: string; note?: string | null }> = [];
  let cursor = 0;
  const remaining = [...corrections];
  while (cursor < text.length) {
    let nextIdx = -1;
    let chosen: typeof remaining[number] | null = null;
    let chosenIdx = -1;
    for (let i = 0; i < remaining.length; i++) {
      const c = remaining[i];
      if (!c.original) continue;
      const at = text.indexOf(c.original, cursor);
      if (at !== -1 && (nextIdx === -1 || at < nextIdx)) {
        nextIdx = at;
        chosen = c;
        chosenIdx = i;
      }
    }
    if (chosen === null || nextIdx === -1) {
      segments.push({ kind: "plain", text: text.slice(cursor) });
      break;
    }
    if (nextIdx > cursor) segments.push({ kind: "plain", text: text.slice(cursor, nextIdx) });
    segments.push({ kind: "fix", text: chosen.original, fix: chosen.fixed, note: chosen.explanation_ru });
    cursor = nextIdx + chosen.original.length;
    remaining.splice(chosenIdx, 1);
  }
  return (
    <p className="whitespace-pre-wrap leading-relaxed">
      {segments.map((s, i) =>
        s.kind === "plain" ? (
          <span key={i}>{s.text}</span>
        ) : (
          <span
            key={i}
            className="bg-red-100 dark:bg-red-950/40 text-red-900 dark:text-red-200 rounded px-1 cursor-help"
            title={`→ ${s.fix}${s.note ? `\n${s.note}` : ""}`}
          >
            <span className="line-through">{s.text}</span>
            {" → "}
            <span className="font-semibold text-emerald-700 dark:text-emerald-300">{s.fix}</span>
          </span>
        ),
      )}
    </p>
  );
}

export default function WritingPage() {
  const qc = useQueryClient();
  const [task, setTask] = useState<WritingTaskType>("task2");
  const [prompt, setPrompt] = useState<WritingPrompt | null>(null);
  const [text, setText] = useState("");
  const [result, setResult] = useState<WritingResult | null>(null);

  const history = useQuery({
    queryKey: ["writing-history"],
    queryFn: async () => (await api.get<WritingListItem[]>("/api/v1/writing")).data,
  });

  const promptMut = useMutation({
    mutationFn: async (task_type: WritingTaskType) =>
      (await api.post<WritingPrompt>("/api/v1/writing/prompt", { task_type })).data,
    onSuccess: (data) => {
      setPrompt(data);
      setText("");
      setResult(null);
    },
  });

  const submitMut = useMutation({
    mutationFn: async () => {
      if (!prompt) throw new Error("no prompt");
      return (
        await api.post<WritingResult>("/api/v1/writing/submit", {
          task_type: task,
          prompt_en: prompt.prompt_en,
          prompt_ru: prompt.prompt_ru,
          min_words: prompt.min_words,
          user_text: text,
        })
      ).data;
    },
    onSuccess: (data) => {
      setResult(data);
      qc.invalidateQueries({ queryKey: ["writing-history"] });
    },
  });

  const taskMinutes = TASKS.find((t) => t.value === task)?.minutes ?? 40;
  const wc = useMemo(() => countWords(text), [text]);
  const wordPct = prompt ? Math.min(100, Math.round((wc / prompt.min_words) * 100)) : 0;

  function openPast(id: number) {
    api.get<WritingResult>(`/api/v1/writing/${id}`).then((r) => {
      setResult(r.data);
      setPrompt({
        task_type: r.data.task_type as WritingTaskType,
        prompt_en: r.data.prompt_en,
        prompt_ru: r.data.prompt_ru,
        min_words: r.data.min_words,
      });
      setText(r.data.user_text);
      setTask(r.data.task_type as WritingTaskType);
    });
  }

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Writing — IELTS</h1>
        <Link href="/">
          <Button variant="ghost" size="sm">← На главную</Button>
        </Link>
      </div>

      {/* Task picker + new prompt */}
      <Card>
        <CardContent className="py-4 space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium">Тип задания:</span>
            <div className="flex rounded-md border overflow-hidden text-sm">
              {TASKS.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTask(t.value)}
                  className={`px-3 py-1 ${task === t.value ? "bg-primary text-primary-foreground" : "hover:bg-accent"}`}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <Button
              onClick={() => promptMut.mutate(task)}
              disabled={promptMut.isPending}
              size="sm"
            >
              {promptMut.isPending ? "Генерирую…" : prompt ? "Новое задание" : "Получить задание"}
            </Button>
            <span className="text-xs text-muted-foreground ml-auto">
              ~{taskMinutes} мин · мин. {task === "task2" ? 250 : 150} слов
            </span>
          </div>

          {promptMut.isPending && (
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <div className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />
              <span>Claude составляет задание (5–15 сек)…</span>
            </div>
          )}

          {prompt && (
            <div className="rounded-md border bg-muted/40 p-3 space-y-2">
              <p className="text-base">{prompt.prompt_en}</p>
              {prompt.prompt_ru && (
                <p className="text-xs text-muted-foreground italic">{prompt.prompt_ru}</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Editor */}
      {prompt && !result && (
        <Card>
          <CardContent className="py-4 space-y-3">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Write your answer here…"
              rows={14}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm font-mono resize-y focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <div className="text-xs text-muted-foreground mb-1">
                  Слов: <span className={wc >= prompt.min_words ? "text-emerald-600 font-medium" : "font-medium text-foreground"}>{wc}</span> / {prompt.min_words}
                </div>
                <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full transition-all ${wc >= prompt.min_words ? "bg-emerald-600" : "bg-primary"}`}
                    style={{ width: `${wordPct}%` }}
                  />
                </div>
              </div>
              <Button
                onClick={() => submitMut.mutate()}
                disabled={submitMut.isPending || wc < 20}
              >
                {submitMut.isPending ? "Оцениваю…" : "Отправить"}
              </Button>
            </div>
            {submitMut.isPending && (
              <div className="rounded-md border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/20 px-3 py-2 text-sm text-blue-900 dark:text-blue-200 flex items-center gap-3">
                <div className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />
                <div>
                  <div className="font-medium">Экзаменатор-Claude проверяет работу…</div>
                  <div className="text-xs opacity-80">30–90 сек. Не закрывай вкладку.</div>
                </div>
              </div>
            )}
            {submitMut.isError && (
              <p className="text-sm text-destructive">Не удалось получить оценку. Попробуй ещё раз.</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Result */}
      {result && (
        <>
          <Card>
            <CardContent className="py-4 space-y-4">
              <div className="flex items-end gap-4 flex-wrap">
                <div>
                  <div className="text-xs text-muted-foreground">Overall band</div>
                  <div className={`text-5xl font-bold leading-none ${bandColor(result.overall_band)}`}>
                    {result.overall_band ?? "—"}
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  {result.word_count} слов · мин. {result.min_words} ·{" "}
                  {new Date(result.created_at).toLocaleString("ru-RU")}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-auto"
                  onClick={() => {
                    setResult(null);
                  }}
                >
                  Новая попытка
                </Button>
              </div>

              <div className="space-y-2">
                {result.criteria.map((c) => (
                  <div key={c.name} className="rounded-md border px-3 py-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{c.name}</span>
                      <span className={`font-semibold ${bandColor(c.band)}`}>{c.band ?? "—"}</span>
                    </div>
                    {c.comment_ru && (
                      <p className="text-xs text-muted-foreground mt-1">{c.comment_ru}</p>
                    )}
                  </div>
                ))}
              </div>

              {result.tip_ru && (
                <div className="rounded-md bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 px-3 py-2 text-sm">
                  💡 {result.tip_ru}
                </div>
              )}
            </CardContent>
          </Card>

          {result.corrections.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Твой текст с исправлениями ({result.corrections.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <HighlightedText text={result.user_text} corrections={result.corrections} />
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* History */}
      {(history.data ?? []).length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Прошлые работы</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm">
              {(history.data ?? []).map((it) => (
                <li key={it.id}>
                  <button
                    onClick={() => openPast(it.id)}
                    className="w-full flex items-center justify-between gap-2 rounded px-2 py-1 hover:bg-accent text-left"
                  >
                    <span>
                      <span className={`font-semibold ${bandColor(it.overall_band)}`}>{it.overall_band ?? "—"}</span>
                      <span className="text-muted-foreground ml-2">{it.task_type === "task2" ? "Task 2" : "Task 1"}</span>
                      <span className="text-muted-foreground ml-2">· {it.word_count} слов</span>
                    </span>
                    <span className="text-xs text-muted-foreground">{new Date(it.created_at).toLocaleDateString("ru-RU")}</span>
                  </button>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
