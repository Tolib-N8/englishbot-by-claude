"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type Vocabulary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

type Direction = "en2ru" | "ru2en";

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export default function VocabPracticePage() {
  const all = useQuery({
    queryKey: ["vocab-all"],
    queryFn: async () => (await api.get<Vocabulary[]>("/api/v1/vocab")).data,
  });

  const [direction, setDirection] = useState<Direction>("en2ru");
  const [order, setOrder] = useState<number[]>([]);
  const [idx, setIdx] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [know, setKnow] = useState(0);
  const [skip, setSkip] = useState(0);

  // (re)shuffle whenever the vocab list or direction changes
  useEffect(() => {
    if (!all.data) return;
    setOrder(shuffle(all.data.map((_, i) => i)));
    setIdx(0);
    setRevealed(false);
    setKnow(0);
    setSkip(0);
  }, [all.data, direction]);

  const list = all.data ?? [];
  const word = useMemo(
    () => (list.length && order.length ? list[order[idx % order.length]] : null),
    [list, order, idx],
  );

  if (all.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;

  if (!word) {
    return (
      <div className="max-w-xl space-y-4">
        <h1 className="text-2xl font-bold">Повторение словаря</h1>
        <p className="text-sm text-muted-foreground">
          Пока нет слов. Добавь их через чат («Извлечь слова в словарь») или вручную в /vocab.
        </p>
        <Link href="/vocab">
          <Button variant="outline">← К словарю</Button>
        </Link>
      </div>
    );
  }

  const front = direction === "en2ru" ? word.word_en : word.translation_ru;
  const back = direction === "en2ru" ? word.translation_ru : word.word_en;

  function next(counted: "know" | "skip") {
    if (counted === "know") setKnow((v) => v + 1);
    else setSkip((v) => v + 1);
    setIdx((v) => v + 1);
    setRevealed(false);
  }

  function reshuffle() {
    setOrder(shuffle(list.map((_, i) => i)));
    setIdx(0);
    setRevealed(false);
    setKnow(0);
    setSkip(0);
  }

  const seen = idx + (revealed ? 0 : 0);
  const totalSeen = know + skip;

  return (
    <div className="max-w-xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Повторение словаря</h1>
        <Link href="/vocab">
          <Button variant="ghost" size="sm">← К списку</Button>
        </Link>
      </div>

      {/* Mode + stats */}
      <div className="flex items-center gap-2 text-sm">
        <div className="flex rounded-md border overflow-hidden">
          <button
            onClick={() => setDirection("en2ru")}
            className={`px-3 py-1 ${direction === "en2ru" ? "bg-primary text-primary-foreground" : "hover:bg-accent"}`}
          >
            EN → RU
          </button>
          <button
            onClick={() => setDirection("ru2en")}
            className={`px-3 py-1 ${direction === "ru2en" ? "bg-primary text-primary-foreground" : "hover:bg-accent"}`}
          >
            RU → EN
          </button>
        </div>
        <Button variant="outline" size="sm" onClick={reshuffle}>🔀 Заново</Button>
        <span className="ml-auto text-xs text-muted-foreground">
          {seen + 1} / {list.length} · ✓ {know} · ✗ {skip}
        </span>
      </div>

      <Card>
        <CardContent className="py-10 text-center space-y-4 min-h-[200px]">
          <div className="text-3xl font-semibold">{front}</div>
          {word.part_of_speech && (
            <div className="text-xs text-muted-foreground">{word.part_of_speech}</div>
          )}

          {revealed && (
            <div className="pt-4 border-t space-y-2">
              <div className="text-2xl">{back}</div>
              {word.example_en && (
                <div className="text-sm italic text-muted-foreground">
                  “{word.example_en}”
                  {word.example_ru ? <div>— {word.example_ru}</div> : null}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {!revealed ? (
        <Button onClick={() => setRevealed(true)} className="w-full">
          Показать перевод
        </Button>
      ) : (
        <div className="grid grid-cols-2 gap-2">
          <Button variant="destructive" onClick={() => next("skip")}>
            Не знал
          </Button>
          <Button onClick={() => next("know")}>
            Знал
          </Button>
        </div>
      )}

      {totalSeen >= list.length && totalSeen > 0 && (
        <div className="rounded-md border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/20 px-3 py-2 text-sm text-emerald-900 dark:text-emerald-200">
          🎉 Прошёл весь словарь. Знал {know} из {list.length} ({Math.round((know / list.length) * 100)}%).{" "}
          <button onClick={reshuffle} className="underline">Ещё раз</button>
        </div>
      )}
    </div>
  );
}
