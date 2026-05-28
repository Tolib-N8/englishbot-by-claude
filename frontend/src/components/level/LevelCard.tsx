"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Level } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

const CONFIDENCE_LABEL: Record<string, string> = {
  low: "низкая надёжность",
  medium: "средняя надёжность",
  high: "высокая надёжность",
};

const CONFIDENCE_CLASS: Record<string, string> = {
  low: "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200",
  medium: "bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-200",
  high: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200",
};

export function LevelCard() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);

  const level = useQuery({
    queryKey: ["level"],
    queryFn: async () => (await api.get<Level>("/api/v1/level")).data,
  });

  const assess = useMutation({
    mutationFn: async () => (await api.post<Level>("/api/v1/level/assess")).data,
    onSuccess: (data) => qc.setQueryData(["level"], data),
  });

  const lvl = level.data;
  const a = lvl?.assessment;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center justify-between">
          <span>Уровень — оценка по IELTS / CEFR</span>
          <Button size="sm" variant="outline" onClick={() => assess.mutate()} disabled={assess.isPending}>
            {assess.isPending ? "Оцениваю…" : a ? "Переоценить" : "Оценить уровень"}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!a ? (
          <p className="text-sm text-muted-foreground">
            Уровень ещё не оценён. Нажми «Оценить уровень» — Claude проанализирует твою
            письменную речь из чатов по критериям IELTS.
          </p>
        ) : (
          <>
            <div className="flex flex-wrap items-end gap-x-6 gap-y-2">
              <div>
                <div className="text-xs text-muted-foreground">CEFR</div>
                <div className="text-4xl font-bold text-primary leading-none">{a.cefr_level}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">IELTS (письмо)</div>
                <div className="text-4xl font-bold leading-none">{a.ielts_band ?? "—"}</div>
              </div>
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${CONFIDENCE_CLASS[a.confidence] ?? CONFIDENCE_CLASS.low}`}
              >
                {CONFIDENCE_LABEL[a.confidence] ?? a.confidence}
              </span>
            </div>

            <p className="text-sm leading-relaxed">{a.summary_ru}</p>

            <div className="rounded-md bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900 px-3 py-2 text-xs text-amber-900 dark:text-amber-200">
              ⚠️ Оценка только по письменной речи в чате — это не полный IELTS (Listening и
              Reading не проверяются, Speaking — лишь приблизительно). Основано на{" "}
              {a.based_on_messages} сообщениях ({a.based_on_words} слов).
            </div>

            {/* Skill breakdown */}
            <div className="space-y-2">
              {a.skills.map((s) => (
                <div key={s.name} className="rounded-md border px-3 py-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{s.name}</span>
                    <span className="text-muted-foreground">
                      {s.cefr ?? "—"}
                      {s.ielts ? ` · IELTS ${s.ielts}` : ""}
                    </span>
                  </div>
                  {s.comment_ru && (
                    <p className="text-xs text-muted-foreground mt-1">{s.comment_ru}</p>
                  )}
                </div>
              ))}
            </div>

            <Button variant="ghost" size="sm" onClick={() => setOpen((v) => !v)}>
              {open ? "Скрыть детали" : "Показать сильные/слабые стороны и план"}
            </Button>

            {open && (
              <div className="space-y-4">
                {a.strengths.length > 0 && (
                  <Section title="Сильные стороны" items={a.strengths} tone="good" />
                )}
                {a.weaknesses.length > 0 && (
                  <Section title="Слабые места" items={a.weaknesses} tone="bad" />
                )}
                {a.next_steps.length > 0 && (
                  <Section title="Что подтянуть для IELTS" items={a.next_steps} tone="plan" />
                )}
                {a.evidence.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Доказательства (твои фразы)</h3>
                    <div className="space-y-2">
                      {a.evidence.map((e, i) => (
                        <div key={i} className="text-sm border-l-2 border-muted-foreground/30 pl-3">
                          <div className="font-mono text-xs bg-muted/40 rounded px-2 py-1 inline-block">
                            “{e.quote}”
                          </div>
                          {e.issue_ru && (
                            <div className="text-xs text-muted-foreground mt-1">{e.issue_ru}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="text-xs text-muted-foreground pt-1">
              Оценено: {formatDate(a.created_at)} · слов в словаре: {lvl?.words_total ?? 0} ·
              тем: {lvl?.topics ?? 0} · уроков: {lvl?.sessions ?? 0}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function Section({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "good" | "bad" | "plan";
}) {
  const dot =
    tone === "good" ? "text-emerald-600" : tone === "bad" ? "text-destructive" : "text-primary";
  return (
    <div>
      <h3 className="text-sm font-semibold mb-1">{title}</h3>
      <ul className="space-y-1">
        {items.map((it, i) => (
          <li key={i} className="text-sm flex gap-2">
            <span className={dot}>•</span>
            <span>{it}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
