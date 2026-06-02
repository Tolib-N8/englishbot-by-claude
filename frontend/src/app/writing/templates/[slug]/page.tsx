"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, type TemplateDetail } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { LessonMarkdown } from "@/components/lessons/LessonMarkdown";

export default function TemplateDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const tmpl = useQuery({
    queryKey: ["writing-template", slug],
    queryFn: async () =>
      (await api.get<TemplateDetail>(`/api/v1/writing/templates/${slug}`)).data,
    staleTime: Infinity,
  });

  if (tmpl.isLoading) {
    return (
      <div className="max-w-3xl space-y-4">
        <h1 className="text-2xl font-bold">Готовлю шаблон…</h1>
        <Card>
          <CardContent className="py-4 flex items-center gap-3 text-sm text-muted-foreground">
            <div className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />
            <div>
              <div className="font-medium text-foreground">Claude собирает шаблон со скелетом и примерами</div>
              <div>Первый раз — 30-60 секунд. Дальше открывается мгновенно.</div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (tmpl.isError || !tmpl.data) {
    return (
      <div className="max-w-3xl space-y-4">
        <p className="text-sm text-destructive">Не удалось загрузить шаблон.</p>
        <Link href="/writing/templates">
          <Button variant="outline" size="sm">← К шаблонам</Button>
        </Link>
      </div>
    );
  }

  const t = tmpl.data;

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-muted-foreground">Шаблон {t.order}</div>
          <h1 className="text-xl font-bold">{t.title}</h1>
        </div>
        <Link href="/writing/templates">
          <Button variant="ghost" size="sm">← Все шаблоны</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="py-6">
          <LessonMarkdown body={t.body_md} />
        </CardContent>
      </Card>

      <div className="flex items-center gap-2">
        {t.prev_slug && (
          <Link href={`/writing/templates/${t.prev_slug}`}>
            <Button variant="outline" size="sm">← Назад</Button>
          </Link>
        )}
        <div className="flex-1" />
        {t.next_slug ? (
          <Link href={`/writing/templates/${t.next_slug}`}>
            <Button>Следующий →</Button>
          </Link>
        ) : (
          <Link href="/writing">
            <Button>К практике →</Button>
          </Link>
        )}
      </div>
    </div>
  );
}
