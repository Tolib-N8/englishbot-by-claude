"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api, type NoteDetail } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MarkdownView } from "@/components/notes/MarkdownView";

function NoteViewInner() {
  const sp = useSearchParams();
  const path = sp.get("path") ?? "";

  const note = useQuery({
    queryKey: ["note", path],
    enabled: !!path,
    queryFn: async () =>
      (await api.get<NoteDetail>("/api/v1/notes/by-path", { params: { path } })).data,
  });

  if (!path) return <p className="text-sm text-muted-foreground">No path.</p>;
  if (note.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (note.error) return <p className="text-sm text-destructive">Not found.</p>;
  if (!note.data) return null;

  const n = note.data;

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <Link href="/notes">
          <Button variant="ghost" size="sm">
            ← Back to vault
          </Button>
        </Link>
        <code className="text-xs text-muted-foreground">{n.path}</code>
      </div>

      <Card>
        <CardContent className="py-6">
          <MarkdownView body={n.body} />
        </CardContent>
      </Card>

      {Object.keys(n.frontmatter).length > 0 && (
        <details className="text-xs text-muted-foreground">
          <summary className="cursor-pointer">Frontmatter</summary>
          <pre className="bg-muted/30 rounded p-3 mt-2 overflow-auto">
            {JSON.stringify(n.frontmatter, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

export default function NoteViewPage() {
  return (
    <Suspense fallback={null}>
      <NoteViewInner />
    </Suspense>
  );
}
