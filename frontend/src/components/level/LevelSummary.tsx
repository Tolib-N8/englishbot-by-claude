"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api, type Level } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const CEFR_SCALE = ["A1", "A2", "B1", "B2", "C1", "C2"];

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

export function LevelSummary() {
  const level = useQuery({
    queryKey: ["level"],
    queryFn: async () => (await api.get<Level>("/api/v1/level")).data,
  });

  const a = level.data?.assessment;
  const currentIdx = a ? CEFR_SCALE.indexOf(a.cefr_level) : -1;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center justify-between">
          <span>Уровень — IELTS / CEFR</span>
          <Link href="/level">
            <Button size="sm" variant="ghost">Подробнее →</Button>
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!a ? (
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">Уровень ещё не оценён.</p>
            <Link href="/level">
              <Button size="sm">Оценить</Button>
            </Link>
          </div>
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
              <span className={`px-2 py-1 rounded text-xs font-medium ${CONFIDENCE_CLASS[a.confidence] ?? CONFIDENCE_CLASS.low}`}>
                {CONFIDENCE_LABEL[a.confidence] ?? a.confidence}
              </span>
            </div>

            {/* CEFR scale */}
            <div>
              <div className="flex gap-1">
                {CEFR_SCALE.map((band, i) => (
                  <div key={band} className="flex-1 text-center">
                    <div
                      className={
                        "h-2 rounded-full " +
                        (i < currentIdx
                          ? "bg-primary/40"
                          : i === currentIdx
                            ? "bg-primary"
                            : "bg-muted")
                      }
                    />
                    <div
                      className={
                        "mt-1 text-xs " +
                        (i === currentIdx ? "font-bold text-primary" : "text-muted-foreground")
                      }
                    >
                      {band}
                    </div>
                  </div>
                ))}
              </div>
              {a.target_band && (
                <p className="text-xs text-muted-foreground mt-2">
                  Цель: IELTS <span className="font-medium text-foreground">{a.target_band}</span> —
                  план на странице{" "}
                  <Link href="/level" className="text-primary underline">Уровень</Link>.
                </p>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
