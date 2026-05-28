"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api, type Conversation, type FlashcardStats, type AppSettings, type Level } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

export default function HomePage() {
  const stats = useQuery({
    queryKey: ["flashcard-stats"],
    queryFn: async () => (await api.get<FlashcardStats>("/api/v1/flashcards/stats")).data,
  });
  const conversations = useQuery({
    queryKey: ["conversations"],
    queryFn: async () => (await api.get<Conversation[]>("/api/v1/conversations")).data,
  });
  const settings = useQuery({
    queryKey: ["settings"],
    queryFn: async () => (await api.get<AppSettings>("/api/v1/settings")).data,
  });
  const level = useQuery({
    queryKey: ["level"],
    queryFn: async () => (await api.get<Level>("/api/v1/level")).data,
  });

  const lvl = level.data;

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Welcome back</h1>
        <p className="text-sm text-muted-foreground">
          Model: <span className="font-mono">{settings.data?.model ?? "…"}</span>
        </p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center justify-between">
            <span>Твой уровень</span>
            <span className="text-xs font-normal text-muted-foreground">
              определяется автоматически по прогрессу
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-end gap-3">
            <div className="text-4xl font-bold text-primary">{lvl?.level ?? "…"}</div>
            {lvl?.next_level && (
              <div className="text-sm text-muted-foreground pb-1">
                → следующий: <span className="font-medium">{lvl.next_level}</span>
              </div>
            )}
          </div>

          {lvl?.next_level ? (
            <div className="space-y-1">
              <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${lvl?.progress_to_next ?? 0}%` }}
                />
              </div>
              <div className="text-xs text-muted-foreground">
                {lvl?.progress_to_next ?? 0}% до уровня {lvl.next_level}
              </div>
            </div>
          ) : (
            <div className="text-xs text-muted-foreground">Максимальный уровень достигнут 🎉</div>
          )}

          <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground pt-1">
            <span>📚 слов: <span className="font-medium text-foreground">{lvl?.words_total ?? 0}</span> (освоено {lvl?.words_mastered ?? 0})</span>
            <span>🧩 тем: <span className="font-medium text-foreground">{lvl?.topics ?? 0}</span></span>
            <span>💬 уроков: <span className="font-medium text-foreground">{lvl?.sessions ?? 0}</span></span>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Due cards</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats.data?.due_now ?? 0}</div>
            <p className="text-xs text-muted-foreground">to review now</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Reviewed today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats.data?.reviewed_today ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Total cards</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats.data?.total ?? 0}</div>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-3">
        <Link href="/chat">
          <Button>Start a chat</Button>
        </Link>
        <Link href="/flashcards/review">
          <Button variant="outline" disabled={(stats.data?.due_now ?? 0) === 0}>
            Review {stats.data?.due_now ?? 0} cards
          </Button>
        </Link>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-3">Recent conversations</h2>
        {(conversations.data ?? []).length === 0 ? (
          <p className="text-sm text-muted-foreground">No conversations yet.</p>
        ) : (
          <div className="space-y-2">
            {(conversations.data ?? []).slice(0, 5).map((c) => (
              <Link
                key={c.id}
                href={`/chat/${c.id}`}
                className="flex justify-between items-center rounded-md border bg-card px-4 py-3 hover:bg-accent"
              >
                <span className="truncate">{c.title || "Untitled"}</span>
                <span className="text-xs text-muted-foreground">{formatDate(c.updated_at)}</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
