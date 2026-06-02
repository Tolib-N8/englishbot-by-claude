"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api, type TemplateSummary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function TemplatesListPage() {
  const list = useQuery({
    queryKey: ["writing-templates"],
    queryFn: async () => (await api.get<TemplateSummary[]>("/api/v1/writing/templates")).data,
  });

  const templates = list.data ?? [];

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Шаблоны IELTS Task 2</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Готовые скелеты с [PLACEHOLDERS] и объяснениями для каждого типа вопросов
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/writing/lessons">
            <Button variant="outline" size="sm">📖 Гайды</Button>
          </Link>
          <Link href="/writing">
            <Button variant="ghost" size="sm">← К практике</Button>
          </Link>
        </div>
      </div>

      {list.isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}

      <div className="space-y-2">
        {templates.map((t) => (
          <Link key={t.slug} href={`/writing/templates/${t.slug}`}>
            <Card className="hover:bg-accent/40 transition-colors cursor-pointer">
              <CardContent className="py-3 flex items-center gap-3">
                <div
                  className={
                    "h-8 w-8 rounded-full flex items-center justify-center font-semibold text-sm shrink-0 " +
                    (t.generated
                      ? "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300"
                      : "bg-muted text-muted-foreground")
                  }
                >
                  {t.order}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{t.title}</div>
                  <div className="text-xs text-muted-foreground">{t.summary}</div>
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
