"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Exercise, type ExerciseStats, type TopicSuggestion } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ExerciseCard } from "@/components/exercises/ExerciseCard";

const COUNTS = [4, 6, 8, 10];

export default function ExercisesPage() {
  const qc = useQueryClient();
  const [topic, setTopic] = useState("");
  const [count, setCount] = useState(6);
  const [batch, setBatch] = useState<Exercise[]>([]);

  const topics = useQuery({
    queryKey: ["exercise-topics"],
    queryFn: async () => (await api.get<TopicSuggestion[]>("/api/v1/exercises/topics")).data,
  });
  const stats = useQuery({
    queryKey: ["exercise-stats"],
    queryFn: async () => (await api.get<ExerciseStats>("/api/v1/exercises/stats")).data,
  });

  const generate = useMutation({
    mutationFn: async () =>
      (await api.post<Exercise[]>("/api/v1/exercises/generate", { topic, count })).data,
    onSuccess: (data) => {
      setBatch(data);
      qc.invalidateQueries({ queryKey: ["exercise-stats"] });
    },
  });

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Грамматические упражнения</h1>
        {stats.data && stats.data.attempted > 0 && (
          <span className="text-sm text-muted-foreground">
            Точность: <span className="font-semibold text-foreground">{stats.data.accuracy}%</span>{" "}
            ({stats.data.correct}/{stats.data.attempted})
          </span>
        )}
      </div>

      {/* Generator */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Тема (из твоего плана подготовки)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {(topics.data ?? []).map((t) => (
              <button
                key={t.topic}
                onClick={() => setTopic(t.topic)}
                className={
                  "text-xs rounded-full px-3 py-1 border transition-colors " +
                  (topic === t.topic
                    ? "bg-primary text-primary-foreground border-primary"
                    : "hover:bg-accent") +
                  (t.source === "roadmap" ? " border-primary/40" : "")
                }
                title={t.source === "roadmap" ? "Из роудмепа" : "Общая тема"}
              >
                {t.source === "roadmap" ? "★ " : ""}
                {t.topic}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <Input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Или впиши свою тему…"
            />
            <select
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            >
              {COUNTS.map((c) => (
                <option key={c} value={c}>{c} шт</option>
              ))}
            </select>
            <Button onClick={() => generate.mutate()} disabled={generate.isPending || !topic.trim()}>
              {generate.isPending ? "Генерирую…" : "Создать"}
            </Button>
          </div>
          {generate.isError && (
            <p className="text-xs text-destructive">Не удалось сгенерировать. Попробуй ещё раз.</p>
          )}
        </CardContent>
      </Card>

      {/* Exercises */}
      {batch.length > 0 ? (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">
            {topic} <span className="text-sm text-muted-foreground">· {batch.length} заданий</span>
          </h2>
          {batch.map((ex) => (
            <ExerciseCard
              key={ex.id}
              ex={ex}
              onAnswered={() => qc.invalidateQueries({ queryKey: ["exercise-stats"] })}
            />
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          Выбери тему выше (★ — из твоего роудмепа) и нажми «Создать». Claude составит
          упражнения под твой уровень.
        </p>
      )}
    </div>
  );
}
