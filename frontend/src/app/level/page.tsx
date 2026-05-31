"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Level } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

const CEFR_SCALE = ["A1", "A2", "B1", "B2", "C1", "C2"];
const IELTS_BANDS = ["4.0", "4.5", "5.0", "5.5", "6.0", "6.5", "7.0", "7.5", "8.0", "8.5", "9.0"];
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

export default function LevelPage() {
  const qc = useQueryClient();
  const level = useQuery({
    queryKey: ["level"],
    queryFn: async () => (await api.get<Level>("/api/v1/level")).data,
  });
  const assess = useMutation({
    mutationFn: async () => (await api.post<Level>("/api/v1/level/assess")).data,
    onSuccess: (data) => qc.setQueryData(["level"], data),
  });
  const setTarget = useMutation({
    mutationFn: async (band: string) =>
      (await api.patch<Level>("/api/v1/level/target", { target_band: band })).data,
    onSuccess: (data) => qc.setQueryData(["level"], data),
  });

  const lvl = level.data;
  const a = lvl?.assessment;
  const currentIdx = a ? CEFR_SCALE.indexOf(a.cefr_level) : -1;
  // Roadmap is stale if the chosen target differs from what the stored roadmap was built for.
  const roadmapStale = !!a && !!lvl?.target_band && a.target_band !== lvl.target_band;

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Уровень и план подготовки</h1>
        <div className="flex gap-2">
          <Link href="/">
            <Button variant="ghost" size="sm">← На главную</Button>
          </Link>
          <Button size="sm" variant="outline" onClick={() => assess.mutate()} disabled={assess.isPending}>
            {assess.isPending ? "Оцениваю…" : a ? "Переоценить" : "Оценить уровень"}
          </Button>
        </div>
      </div>

      {assess.isPending && (
        <div className="rounded-md border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/20 px-3 py-2 text-sm text-blue-900 dark:text-blue-200 flex items-center gap-3">
          <div className="h-4 w-4 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
          <div>
            <div className="font-medium">Claude анализирует твою речь и составляет план…</div>
            <div className="text-xs opacity-80">Это занимает 60–120 секунд. Не закрывай вкладку.</div>
          </div>
        </div>
      )}

      {/* Target band selector */}
      <Card>
        <CardContent className="py-4 flex flex-wrap items-center gap-3">
          <span className="text-sm font-medium">Целевой балл IELTS:</span>
          <select
            value={lvl?.target_band ?? ""}
            onChange={(e) => setTarget.mutate(e.target.value)}
            disabled={setTarget.isPending}
            className="h-9 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="">— не задана —</option>
            {IELTS_BANDS.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
          {setTarget.isPending && <span className="text-xs text-muted-foreground">сохраняю…</span>}
          <span className="text-xs text-muted-foreground">
            план подготовки строится до этого балла
          </span>
        </CardContent>
      </Card>

      {roadmapStale && (
        <div className="rounded-md border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/20 px-3 py-2 text-sm text-blue-900 dark:text-blue-200 flex items-center justify-between gap-3">
          <span>
            Цель изменилась (план составлен для IELTS {a?.target_band}). Переоцени, чтобы
            обновить роудмеп до {lvl?.target_band}.
          </span>
          <Button size="sm" onClick={() => assess.mutate()} disabled={assess.isPending}>
            {assess.isPending ? "…" : "Обновить план"}
          </Button>
        </div>
      )}

      {!a ? (
        <Card>
          <CardContent className="py-8 text-sm text-muted-foreground">
            Уровень ещё не оценён. Нажми «Оценить уровень» — Claude проанализирует твою
            письменную речь из чатов по критериям IELTS и составит план подготовки.
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Headline + scale */}
          <Card>
            <CardContent className="py-6 space-y-4">
              <div className="flex flex-wrap items-end gap-x-6 gap-y-2">
                <div>
                  <div className="text-xs text-muted-foreground">CEFR</div>
                  <div className="text-5xl font-bold text-primary leading-none">{a.cefr_level}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">IELTS (письмо)</div>
                  <div className="text-5xl font-bold leading-none">{a.ielts_band ?? "—"}</div>
                </div>
                {a.target_band && (
                  <div>
                    <div className="text-xs text-muted-foreground">Цель</div>
                    <div className="text-3xl font-semibold leading-none text-emerald-600">{a.target_band}</div>
                  </div>
                )}
                <span className={`px-2 py-1 rounded text-xs font-medium ${CONFIDENCE_CLASS[a.confidence] ?? CONFIDENCE_CLASS.low}`}>
                  {CONFIDENCE_LABEL[a.confidence] ?? a.confidence}
                </span>
              </div>

              <div className="flex gap-1">
                {CEFR_SCALE.map((band, i) => (
                  <div key={band} className="flex-1 text-center">
                    <div
                      className={
                        "h-2 rounded-full " +
                        (i < currentIdx ? "bg-primary/40" : i === currentIdx ? "bg-primary" : "bg-muted")
                      }
                    />
                    <div className={"mt-1 text-xs " + (i === currentIdx ? "font-bold text-primary" : "text-muted-foreground")}>
                      {band}
                    </div>
                  </div>
                ))}
              </div>

              <p className="text-sm leading-relaxed">{a.summary_ru}</p>

              <div className="rounded-md bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900 px-3 py-2 text-xs text-amber-900 dark:text-amber-200">
                ⚠️ Оценка только по письменной речи в чате — это не полный IELTS (Listening и
                Reading не проверяются, Speaking — приблизительно). Основано на {a.based_on_messages}{" "}
                сообщениях ({a.based_on_words} слов). Оценено: {formatDate(a.created_at)}.
              </div>
            </CardContent>
          </Card>

          {/* Roadmap */}
          {a.roadmap.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Роудмеп до IELTS {a.target_band ?? "следующего уровня"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="relative border-l-2 border-muted ml-2 space-y-5">
                  {a.roadmap.map((p, i) => (
                    <li key={i} className="ml-4">
                      <div className="absolute -left-[9px] mt-1 h-4 w-4 rounded-full bg-primary border-2 border-background" />
                      <div className="flex items-baseline justify-between gap-2">
                        <h3 className="font-semibold">{p.title}</h3>
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                          {p.skill ? p.skill : ""}{p.est_weeks ? ` · ~${p.est_weeks} нед.` : ""}
                        </span>
                      </div>
                      {p.target_ru && (
                        <p className="text-sm text-muted-foreground mt-0.5">🎯 {p.target_ru}</p>
                      )}
                      {p.actions_ru.length > 0 && (
                        <ul className="mt-1 space-y-0.5">
                          {p.actions_ru.map((act, j) => (
                            <li key={j} className="text-sm flex gap-2">
                              <span className="text-primary">›</span>
                              <span>{act}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          )}

          {/* Skill breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Разбор по критериям</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {a.skills.map((s) => (
                <div key={s.name} className="rounded-md border px-3 py-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{s.name}</span>
                    <span className="text-muted-foreground">
                      {s.cefr ?? "—"}{s.ielts ? ` · IELTS ${s.ielts}` : ""}
                    </span>
                  </div>
                  {s.comment_ru && <p className="text-xs text-muted-foreground mt-1">{s.comment_ru}</p>}
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Recommendations */}
          <div className="grid gap-4 md:grid-cols-2">
            {a.strengths.length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-sm">Сильные стороны</CardTitle></CardHeader>
                <CardContent>
                  <ul className="space-y-1">
                    {a.strengths.map((it, i) => (
                      <li key={i} className="text-sm flex gap-2"><span className="text-emerald-600">•</span><span>{it}</span></li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
            {a.weaknesses.length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-sm">Слабые места</CardTitle></CardHeader>
                <CardContent>
                  <ul className="space-y-1">
                    {a.weaknesses.map((it, i) => (
                      <li key={i} className="text-sm flex gap-2"><span className="text-destructive">•</span><span>{it}</span></li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>

          {a.next_steps.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Рекомендации</CardTitle></CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {a.next_steps.map((it, i) => (
                    <li key={i} className="text-sm flex gap-2"><span className="text-primary">→</span><span>{it}</span></li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Evidence */}
          {a.evidence.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Доказательства (твои фразы)</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {a.evidence.map((e, i) => (
                  <div key={i} className="text-sm border-l-2 border-muted-foreground/30 pl-3">
                    <div className="font-mono text-xs bg-muted/40 rounded px-2 py-1 inline-block">“{e.quote}”</div>
                    {e.issue_ru && <div className="text-xs text-muted-foreground mt-1">{e.issue_ru}</div>}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
