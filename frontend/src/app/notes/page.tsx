"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api, type NoteSummary } from "@/lib/api";
import { Card } from "@/components/ui/card";

const FOLDERS = [
  { key: "topics", label: "Темы (Topics)" },
  { key: "vocabulary", label: "Лексика (Vocabulary)" },
  { key: "sessions", label: "Сессии (Sessions)" },
];

export default function NotesIndexPage() {
  const all = useQuery({
    queryKey: ["notes-all"],
    queryFn: async () => (await api.get<NoteSummary[]>("/api/v1/notes")).data,
  });

  const grouped = new Map<string, NoteSummary[]>();
  for (const n of all.data ?? []) {
    const k = n.folder || "_root";
    (grouped.get(k) ?? grouped.set(k, []).get(k)!)!.push(n);
  }

  return (
    <div className="max-w-4xl space-y-6">
      <h1 className="text-2xl font-bold">Vault — knowledge graph</h1>
      <p className="text-sm text-muted-foreground">
        Заметки, которые мы накапливаем вместе с ботом. Темы и слова связаны через{" "}
        <code className="text-xs">[[wiki-ссылки]]</code>. Папку{" "}
        <code className="text-xs">vault/</code> можно открыть в Obsidian.
      </p>

      {FOLDERS.map((f) => {
        const items = grouped.get(f.key) ?? [];
        return (
          <section key={f.key}>
            <h2 className="text-lg font-semibold mb-2">
              {f.label}{" "}
              <span className="text-muted-foreground text-sm">({items.length})</span>
            </h2>
            {items.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">пусто</p>
            ) : (
              <div className="grid gap-2 grid-cols-1 sm:grid-cols-2">
                {items.map((n) => (
                  <Link key={n.path} href={`/notes/view?path=${encodeURIComponent(n.path)}`}>
                    <Card className="px-4 py-3 hover:bg-accent transition-colors">
                      <div className="font-medium">{n.title}</div>
                      <div className="text-xs text-muted-foreground">
                        {n.date || n.cefr || n.type || ""}
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}
