"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api, type FlashcardStats } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function FlashcardsHomePage() {
  const stats = useQuery({
    queryKey: ["flashcard-stats"],
    queryFn: async () => (await api.get<FlashcardStats>("/api/v1/flashcards/stats")).data,
  });
  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Flashcards</h1>

      <div className="grid gap-4 grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Due now</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats.data?.due_now ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Total</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats.data?.total ?? 0}</div>
          </CardContent>
        </Card>
      </div>

      <Link href="/flashcards/review">
        <Button disabled={(stats.data?.due_now ?? 0) === 0}>
          Start review
        </Button>
      </Link>
    </div>
  );
}
