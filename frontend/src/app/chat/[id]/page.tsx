"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ConversationDetail, type Correction, type Message } from "@/lib/api";
import { streamChat } from "@/lib/sse";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const convId = Number(id);
  const qc = useQueryClient();
  const scrollRef = useRef<HTMLDivElement>(null);

  const [draft, setDraft] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [streamingCorr, setStreamingCorr] = useState<Correction[] | null>(null);
  const [busy, setBusy] = useState(false);

  const conv = useQuery({
    queryKey: ["conversation", convId],
    queryFn: async () => (await api.get<ConversationDetail>(`/api/v1/conversations/${convId}`)).data,
  });

  const extractVocab = useMutation({
    mutationFn: async (messageId: number) =>
      (await api.post(`/api/v1/vocab/from-chat/${messageId}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["vocab"] }),
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [conv.data, streamingText]);

  async function send() {
    if (!draft.trim() || busy) return;
    const content = draft.trim();
    setDraft("");
    setBusy(true);
    setStreamingText("");
    setStreamingCorr(null);
    try {
      await streamChat({ conversation_id: convId, content }, (e) => {
        if (e.type === "token") setStreamingText((s) => s + e.text);
        else if (e.type === "corrections") setStreamingCorr(e.items);
        else if (e.type === "error") setStreamingText((s) => s + `\n[error: ${e.detail}]`);
      });
    } finally {
      setBusy(false);
      setStreamingText("");
      setStreamingCorr(null);
      await qc.invalidateQueries({ queryKey: ["conversation", convId] });
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)] max-w-3xl">
      <h1 className="text-xl font-bold mb-3 truncate">
        {conv.data?.title || "New conversation"}
      </h1>

      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 pr-2">
        {(conv.data?.messages ?? []).map((m: Message) => (
          <div key={m.id} className="group">
            <MessageBubble m={m} />
            {m.role === "user" && (
              <div className="opacity-0 group-hover:opacity-100 transition-opacity mt-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => extractVocab.mutate(m.id)}
                  disabled={extractVocab.isPending}
                >
                  Извлечь слова в словарь
                </Button>
              </div>
            )}
          </div>
        ))}
        {streamingText && (
          <MessageBubble
            m={{ role: "assistant", content: streamingText, corrections_json: streamingCorr }}
          />
        )}
      </div>

      <div className="flex gap-2 mt-4 pt-3 border-t">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Type in English (or Russian if stuck)…"
          disabled={busy}
        />
        <Button onClick={send} disabled={busy || !draft.trim()}>
          {busy ? "…" : "Send"}
        </Button>
      </div>
    </div>
  );
}
