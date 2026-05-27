import { API_BASE } from "@/lib/api";

export type SseEvent =
  | { type: "token"; text: string }
  | { type: "corrections"; items: Array<{ original: string; fixed: string; explanation_ru: string }> }
  | { type: "user_message_saved"; id: number }
  | { type: "done"; message_id: number; tokens_in: number; tokens_out: number }
  | { type: "error"; detail: string };

export async function streamChat(
  body: { conversation_id: number; content: string },
  onEvent: (e: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
    onEvent({ type: "error", detail: `HTTP ${res.status}` });
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const parsed = parseSseFrame(raw);
      if (parsed) onEvent(parsed);
    }
  }
}

function parseSseFrame(frame: string): SseEvent | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length === 0) return null;
  const data = dataLines.join("\n");
  try {
    const json = JSON.parse(data);
    return { type: event, ...json } as SseEvent;
  } catch {
    return null;
  }
}
