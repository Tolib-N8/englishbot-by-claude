"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Vocabulary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";

export default function VocabPage() {
  const qc = useQueryClient();
  const [q, setQ] = useState("");

  const list = useQuery({
    queryKey: ["vocab", q],
    queryFn: async () =>
      (await api.get<Vocabulary[]>("/api/v1/vocab", { params: q ? { q } : {} })).data,
  });

  const addToDeck = useMutation({
    mutationFn: async (id: number) => (await api.post(`/api/v1/vocab/${id}/add-to-deck`)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["vocab"] });
      qc.invalidateQueries({ queryKey: ["flashcard-stats"] });
    },
  });

  return (
    <div className="max-w-3xl space-y-4">
      <h1 className="text-2xl font-bold">Vocabulary</h1>

      <Input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search words…"
      />

      <div className="space-y-2">
        {(list.data ?? []).map((v) => (
          <Card key={v.id}>
            <CardContent className="py-3 flex items-center justify-between">
              <div className="flex-1">
                <div className="font-medium">
                  {v.word_en}{" "}
                  <span className="text-muted-foreground text-sm">— {v.translation_ru}</span>
                </div>
                {v.example_en && (
                  <div className="text-xs text-muted-foreground italic mt-1">
                    “{v.example_en}”
                    {v.example_ru ? ` — ${v.example_ru}` : ""}
                  </div>
                )}
                <div className="text-xs text-muted-foreground mt-1">
                  {v.part_of_speech ?? ""} {v.cefr_level ? `· ${v.cefr_level}` : ""}
                </div>
              </div>
              {!v.has_flashcard ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => addToDeck.mutate(v.id)}
                  disabled={addToDeck.isPending}
                >
                  + В колоду
                </Button>
              ) : (
                <span className="text-xs text-muted-foreground">в колоде</span>
              )}
            </CardContent>
          </Card>
        ))}
        {(list.data ?? []).length === 0 && (
          <p className="text-sm text-muted-foreground">
            Пусто. Извлеки слова из чата (кнопка «Извлечь слова в словарь» под твоим сообщением).
          </p>
        )}
      </div>
    </div>
  );
}
