"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, type NoteSummary } from "@/lib/api";
import { Fragment, useMemo } from "react";

/**
 * Minimal markdown renderer with [[wiki-link]] support.
 * We deliberately don't pull in react-markdown — the vault content is
 * authored by Claude in a constrained format and we want full control over
 * how wiki-links resolve.
 */
export function MarkdownView({ body }: { body: string }) {
  const router = useRouter();

  const allNotes = useQuery({
    queryKey: ["notes-all"],
    queryFn: async () => (await api.get<NoteSummary[]>("/api/v1/notes")).data,
  });

  const titleToPath = useMemo(() => {
    const m = new Map<string, string>();
    for (const n of allNotes.data ?? []) {
      m.set(n.title.toLowerCase(), n.path);
      m.set(n.name.toLowerCase(), n.path);
    }
    return m;
  }, [allNotes.data]);

  function renderInline(text: string): React.ReactNode[] {
    const parts: React.ReactNode[] = [];
    const re = /\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]/g;
    let last = 0;
    let m: RegExpExecArray | null;
    let key = 0;
    while ((m = re.exec(text)) !== null) {
      if (m.index > last) parts.push(text.slice(last, m.index));
      const target = m[1].trim();
      const display = (m[2] || target).trim();
      const path = titleToPath.get(target.toLowerCase());
      parts.push(
        <button
          key={`l-${key++}`}
          className={
            "underline underline-offset-2 " +
            (path
              ? "text-primary hover:text-primary/80"
              : "text-muted-foreground italic cursor-default")
          }
          onClick={() => {
            if (path) router.push(`/notes/view?path=${encodeURIComponent(path)}`);
          }}
          disabled={!path}
          title={path ? `Open ${target}` : `Note "${target}" not in vault yet`}
        >
          {display}
        </button>,
      );
      last = re.lastIndex;
    }
    if (last < text.length) parts.push(text.slice(last));
    return parts;
  }

  const lines = body.split("\n");
  const elems: React.ReactNode[] = [];
  let i = 0;
  let key = 0;
  while (i < lines.length) {
    const ln = lines[i];
    if (ln.startsWith("# ")) {
      elems.push(<h1 key={key++} className="text-2xl font-bold mt-4 mb-2">{renderInline(ln.slice(2))}</h1>);
    } else if (ln.startsWith("## ")) {
      elems.push(<h2 key={key++} className="text-xl font-semibold mt-4 mb-2">{renderInline(ln.slice(3))}</h2>);
    } else if (ln.startsWith("### ")) {
      elems.push(<h3 key={key++} className="text-lg font-medium mt-3 mb-1">{renderInline(ln.slice(4))}</h3>);
    } else if (ln.startsWith("- ") || ln.startsWith("* ")) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && (lines[i].startsWith("- ") || lines[i].startsWith("* "))) {
        items.push(<li key={`li-${key++}`}>{renderInline(lines[i].slice(2))}</li>);
        i++;
      }
      elems.push(<ul key={key++} className="list-disc pl-6 space-y-1 my-2">{items}</ul>);
      continue;
    } else if (ln.startsWith("> ")) {
      elems.push(
        <blockquote key={key++} className="border-l-4 border-muted-foreground/30 pl-3 my-2 italic">
          {renderInline(ln.slice(2))}
        </blockquote>,
      );
    } else if (ln.trim() === "") {
      // skip empties
    } else {
      elems.push(<p key={key++} className="my-2 leading-relaxed">{renderInline(ln)}</p>);
    }
    i++;
  }
  return <Fragment>{elems}</Fragment>;
}
