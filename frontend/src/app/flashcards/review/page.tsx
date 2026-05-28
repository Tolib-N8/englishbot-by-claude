"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Flashcard } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

type Quality = 0 | 3 | 4 | 5;

const QUALITY_BUTTONS: { q: Quality; label: string; variant: "destructive" | "outline" | "default" | "secondary" }[] = [
  { q: 0, label: "Again", variant: "destructive" },
  { q: 3, label: "Hard", variant: "outline" },
  { q: 4, label: "Good", variant: "default" },
  { q: 5, label: "Easy", variant: "secondary" },
];

export default function ReviewPage() {
  const qc = useQueryClient();
  const [revealed, setRevealed] = useState(false);

  const due = useQuery({
    queryKey: ["due-cards"],
    queryFn: async () => (await api.get<Flashcard[]>("/api/v1/flashcards/due", { params: { limit: 50 } })).data,
  });

  const review = useMutation({
    mutationFn: async ({ id, quality }: { id: number; quality: Quality }) =>
      (await api.post(`/api/v1/flashcards/${id}/review`, { quality })).data,
    onSuccess: () => {
      setRevealed(false);
      qc.invalidateQueries({ queryKey: ["due-cards"] });
      qc.invalidateQueries({ queryKey: ["flashcard-stats"] });
      qc.invalidateQueries({ queryKey: ["level"] });
    },
  });

  const cards = due.data ?? [];
  const current = cards[0];

  if (due.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;

  if (!current) {
    return (
      <div className="max-w-xl space-y-4">
        <h1 className="text-2xl font-bold">All done!</h1>
        <p className="text-sm text-muted-foreground">No cards are due right now. Come back later.</p>
      </div>
    );
  }

  return (
    <div className="max-w-xl space-y-6">
      <div className="text-sm text-muted-foreground">
        {cards.length} card{cards.length !== 1 ? "s" : ""} to go
      </div>

      <Card>
        <CardContent className="py-10 text-center space-y-4">
          <div className="text-3xl font-semibold">{current.word_en}</div>
          {current.part_of_speech && (
            <div className="text-xs text-muted-foreground">{current.part_of_speech}</div>
          )}

          {revealed && (
            <div className="space-y-3 pt-4 border-t">
              <div className="text-xl">{current.translation_ru}</div>
              {current.example_en && (
                <div className="text-sm italic text-muted-foreground">
                  “{current.example_en}”
                  {current.example_ru ? <div>— {current.example_ru}</div> : null}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {!revealed ? (
        <Button onClick={() => setRevealed(true)} className="w-full">
          Show answer
        </Button>
      ) : (
        <div className="grid grid-cols-4 gap-2">
          {QUALITY_BUTTONS.map((b) => (
            <Button
              key={b.q}
              variant={b.variant}
              disabled={review.isPending}
              onClick={() => review.mutate({ id: current.id, quality: b.q })}
            >
              {b.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
