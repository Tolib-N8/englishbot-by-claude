"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api, type LessonSummary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function LessonsListPage() {
  const list = useQuery({
    queryKey: ["writing-lessons"],
    queryFn: async () => (await api.get<LessonSummary[]>("/api/v1/writing/lessons")).data,
  });

  const lessons = list.data ?? [];
  const readCount = lessons.filter((l) => l.read).length;

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Гайды по IELTS Writing</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Курс из {lessons.length} уроков · прочитано {readCount} / {lessons.length}
          </p>
        </div>
        <Link href="/writing">
          <Button variant="ghost" size="sm">← К практике</Button>
        </Link>
      </div>

      {list.isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}

      <div className="space-y-2">
        {lessons.map((l) => (
          <Link key={l.slug} href={`/writing/lessons/${l.slug}`}>
            <Card className="hover:bg-accent/40 transition-colors cursor-pointer">
              <CardContent className="py-3 flex items-center gap-3">
                <div
                  className={
                    "h-8 w-8 rounded-full flex items-center justify-center font-semibold text-sm shrink-0 " +
                    (l.read
                      ? "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300"
                      : l.generated
                      ? "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300"
                      : "bg-muted text-muted-foreground")
                  }
                >
                  {l.read ? "✓" : l.order}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{l.title}</div>
                  <div className="text-xs text-muted-foreground">{l.summary}</div>
                </div>
                <span className="text-muted-foreground">›</span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
