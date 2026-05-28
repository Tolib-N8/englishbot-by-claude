"use client";

import { useState } from "react";
import { api, type Exercise, type AttemptResult } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const TYPE_LABEL: Record<string, string> = {
  fill_blank: "Заполни пропуск",
  mcq: "Выбери вариант",
  translate_ru_en: "Перевод RU → EN",
  translate_en_ru: "Перевод EN → RU",
};

export function ExerciseCard({ ex, onAnswered }: { ex: Exercise; onAnswered?: () => void }) {
  const [answer, setAnswer] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(value: string) {
    if (!value.trim() || busy || result) return;
    setBusy(true);
    try {
      const res = await api.post<AttemptResult>(`/api/v1/exercises/${ex.id}/attempt`, {
        user_answer: value,
      });
      setResult(res.data);
      onAnswered?.();
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardContent className="py-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs uppercase tracking-wide text-muted-foreground">
            {TYPE_LABEL[ex.type] ?? ex.type}
          </span>
        </div>

        {/* Prompt */}
        {ex.type === "translate_ru_en" ? (
          <p className="text-base font-medium">{ex.prompt_ru}</p>
        ) : (
          <p className="text-base font-medium">{ex.prompt}</p>
        )}

        {/* Input by type */}
        {!result && ex.type === "mcq" && ex.choices_json && (
          <div className="grid grid-cols-2 gap-2">
            {ex.choices_json.map((c) => (
              <Button
                key={c}
                variant={selected === c ? "default" : "outline"}
                onClick={() => {
                  setSelected(c);
                  submit(c);
                }}
                disabled={busy}
              >
                {c}
              </Button>
            ))}
          </div>
        )}

        {!result && ex.type === "fill_blank" && (
          <div className="flex gap-2">
            <Input
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit(answer)}
              placeholder="Твой ответ…"
              disabled={busy}
            />
            <Button onClick={() => submit(answer)} disabled={busy || !answer.trim()}>
              Проверить
            </Button>
          </div>
        )}

        {!result && (ex.type === "translate_ru_en" || ex.type === "translate_en_ru") && (
          <div className="flex gap-2">
            <Input
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit(answer)}
              placeholder={ex.type === "translate_ru_en" ? "Translate to English…" : "Переведи на русский…"}
              disabled={busy}
            />
            <Button onClick={() => submit(answer)} disabled={busy || !answer.trim()}>
              {busy ? "…" : "Проверить"}
            </Button>
          </div>
        )}

        {/* Result */}
        {result && (
          <div
            className={
              "rounded-md px-3 py-2 text-sm " +
              (result.is_correct
                ? "bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900"
                : "bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900")
            }
          >
            <div className="font-medium mb-1">
              {result.is_correct ? "✓ Верно!" : "✗ Неверно"}
            </div>
            {!result.is_correct && (
              <div className="mb-1">
                Правильный ответ: <span className="font-semibold">{result.answer}</span>
              </div>
            )}
            {result.feedback_ru && <div className="text-muted-foreground">{result.feedback_ru}</div>}
            {result.explanation_ru && (
              <div className="text-muted-foreground mt-1">💡 {result.explanation_ru}</div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
