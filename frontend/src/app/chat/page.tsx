"use client";

import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api, type Conversation } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";

export default function ChatListPage() {
  const router = useRouter();
  const qc = useQueryClient();

  const conversations = useQuery({
    queryKey: ["conversations"],
    queryFn: async () => (await api.get<Conversation[]>("/api/v1/conversations")).data,
  });

  const create = useMutation({
    mutationFn: async () => (await api.post<Conversation>("/api/v1/conversations", {})).data,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["conversations"] });
      router.push(`/chat/${data.id}`);
    },
  });

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Chats</h1>
        <Button onClick={() => create.mutate()} disabled={create.isPending}>
          New conversation
        </Button>
      </div>

      {conversations.isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
      {(conversations.data ?? []).length === 0 && !conversations.isLoading && (
        <p className="text-sm text-muted-foreground">
          No conversations yet. Click <strong>New conversation</strong> to start.
        </p>
      )}

      <div className="space-y-2">
        {(conversations.data ?? []).map((c) => (
          <Link key={c.id} href={`/chat/${c.id}`}>
            <Card className="px-4 py-3 hover:bg-accent transition-colors flex justify-between items-center">
              <span className="truncate">{c.title || "Untitled"}</span>
              <span className="text-xs text-muted-foreground">{formatDate(c.updated_at)}</span>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
