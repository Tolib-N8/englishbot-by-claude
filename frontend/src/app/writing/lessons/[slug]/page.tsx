"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type LessonDetail } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { LessonMarkdown } from "@/components/lessons/LessonMarkdown";

export default function LessonDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const qc = useQueryClient();

  const lesson = useQuery({
    queryKey: ["writing-lesson", slug],
    queryFn: async () =>
      (await api.get<LessonDetail>(`/api/v1/writing/lessons/${slug}`)).data,
    // first call may run for 30-60s while Claude generates
    staleTime: Infinity,
  });

  const markRead = useMutation({
    mutationFn: async () =>
      (await api.post<LessonDetail>(`/api/v1/writing/lessons/${slug}/read`)).data,
    onSuccess: (data) => {
      qc.setQueryData(["writing-lesson", slug], data);
      qc.invalidateQueries({ queryKey: ["writing-lessons"] });
    },
  });

  if (lesson.isLoading) {
    return (
      <div className="max-w-3xl space-y-4">
        <h1 className="text-2xl font-bold">Загрузка урока…</h1>
        <Card>
          <CardContent className="py-4 flex items-center gap-3 text-sm text-muted-foreground">
            <div className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />
            <div>
              <div className="font-medium text-foreground">Claude готовит урок</div>
              <div>Первый раз — 30-60 секунд. Дальше открывается мгновенно.</div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (lesson.isError || !lesson.data) {
    return (
      <div className="max-w-3xl space-y-4">
        <p className="text-sm text-destructive">Не удалось загрузить урок.</p>
        <Link href="/writing/lessons">
          <Button variant="outline" size="sm">← К списку</Button>
        </Link>
      </div>
    );
  }

  const l = lesson.data;

  function goNext() {
    if (!l.read) markRead.mutate();
    if (l.next_slug) router.push(`/writing/lessons/${l.next_slug}`);
    else router.push("/writing");
  }

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-xs text-muted-foreground">
          Урок {l.order} · {l.read ? "прочитано ✓" : "новый"}
        </div>
        <Link href="/writing/lessons">
          <Button variant="ghost" size="sm">← Все уроки</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="py-6 prose-sm dark:prose-invert max-w-none">
          <LessonMarkdown body={l.body_md} />
        </CardContent>
      </Card>

      <div className="flex items-center gap-2">
        {l.prev_slug && (
          <Link href={`/writing/lessons/${l.prev_slug}`}>
            <Button variant="outline" size="sm">← Назад</Button>
          </Link>
        )}
        {!l.read && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => markRead.mutate()}
            disabled={markRead.isPending}
          >
            ✓ Отметить прочитанным
          </Button>
        )}
        <div className="flex-1" />
        {l.next_slug ? (
          <Button onClick={goNext}>Следующий урок →</Button>
        ) : (
          <Button onClick={goNext}>К практике →</Button>
        )}
      </div>
    </div>
  );
}
