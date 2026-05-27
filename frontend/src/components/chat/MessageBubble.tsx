import { cn } from "@/lib/utils";
import type { Message } from "@/lib/api";
import { CorrectionPanel } from "./CorrectionPanel";

export function MessageBubble({ m }: { m: Pick<Message, "role" | "content" | "corrections_json"> }) {
  const isUser = m.role === "user";
  return (
    <div className={cn("flex flex-col gap-2", isUser ? "items-end" : "items-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2 whitespace-pre-wrap text-sm",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted",
        )}
      >
        {m.content}
      </div>
      {!isUser && m.corrections_json && m.corrections_json.length > 0 && (
        <div className="max-w-[80%]">
          <CorrectionPanel items={m.corrections_json} />
        </div>
      )}
    </div>
  );
}
