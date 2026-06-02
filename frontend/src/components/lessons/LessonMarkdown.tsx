"use client";

import { Fragment } from "react";

/**
 * Minimal markdown renderer for lesson bodies. We control the generation,
 * so we only need: # h1, ## h2, ### h3, bullet/numbered lists, **bold**,
 * *italic*, `code`, blockquotes, code fences. Good enough for IELTS lessons
 * — no need to pull in react-markdown.
 */
export function LessonMarkdown({ body }: { body: string }) {
  const lines = body.split("\n");
  const out: React.ReactNode[] = [];
  let i = 0;
  let key = 0;

  function inline(text: string): React.ReactNode[] {
    const parts: React.ReactNode[] = [];
    // Order matters: bold > italic > code so ** doesn't get eaten by *.
    const re = /(\*\*([^*]+?)\*\*|`([^`]+)`|\*([^*]+?)\*)/g;
    let last = 0;
    let m: RegExpExecArray | null;
    let kk = 0;
    while ((m = re.exec(text)) !== null) {
      if (m.index > last) parts.push(text.slice(last, m.index));
      if (m[2] !== undefined) parts.push(<strong key={`b-${kk++}`}>{m[2]}</strong>);
      else if (m[3] !== undefined) parts.push(
        <code key={`c-${kk++}`} className="px-1 py-0.5 rounded bg-muted/60 text-xs font-mono">{m[3]}</code>
      );
      else if (m[4] !== undefined) parts.push(<em key={`i-${kk++}`}>{m[4]}</em>);
      last = re.lastIndex;
    }
    if (last < text.length) parts.push(text.slice(last));
    return parts;
  }

  while (i < lines.length) {
    const ln = lines[i];

    // Fenced code block
    if (ln.startsWith("```")) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        buf.push(lines[i]);
        i++;
      }
      i++;
      out.push(
        <pre key={key++} className="bg-muted/60 rounded-md p-3 my-3 text-xs font-mono overflow-x-auto">
          <code>{buf.join("\n")}</code>
        </pre>,
      );
      continue;
    }

    if (ln.startsWith("# ")) {
      out.push(<h1 key={key++} className="text-2xl font-bold mt-6 mb-3">{inline(ln.slice(2))}</h1>);
      i++;
      continue;
    }
    if (ln.startsWith("## ")) {
      out.push(<h2 key={key++} className="text-xl font-semibold mt-5 mb-2">{inline(ln.slice(3))}</h2>);
      i++;
      continue;
    }
    if (ln.startsWith("### ")) {
      out.push(<h3 key={key++} className="text-lg font-medium mt-4 mb-2">{inline(ln.slice(4))}</h3>);
      i++;
      continue;
    }
    if (ln.startsWith("- ") || ln.startsWith("* ")) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && (lines[i].startsWith("- ") || lines[i].startsWith("* "))) {
        items.push(<li key={`li-${key++}`}>{inline(lines[i].slice(2))}</li>);
        i++;
      }
      out.push(<ul key={key++} className="list-disc pl-6 space-y-1 my-2">{items}</ul>);
      continue;
    }
    if (/^\d+\.\s/.test(ln)) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        items.push(<li key={`li-${key++}`}>{inline(lines[i].replace(/^\d+\.\s/, ""))}</li>);
        i++;
      }
      out.push(<ol key={key++} className="list-decimal pl-6 space-y-1 my-2">{items}</ol>);
      continue;
    }
    if (ln.startsWith("> ")) {
      out.push(
        <blockquote key={key++} className="border-l-4 border-muted-foreground/30 pl-3 italic my-2">
          {inline(ln.slice(2))}
        </blockquote>,
      );
      i++;
      continue;
    }
    if (ln.trim() === "") {
      i++;
      continue;
    }
    // Paragraph: collect consecutive non-empty non-special lines
    const buf: string[] = [ln];
    i++;
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].startsWith("#") &&
      !lines[i].startsWith("- ") &&
      !lines[i].startsWith("* ") &&
      !/^\d+\.\s/.test(lines[i]) &&
      !lines[i].startsWith("> ") &&
      !lines[i].startsWith("```")
    ) {
      buf.push(lines[i]);
      i++;
    }
    out.push(
      <p key={key++} className="my-2 leading-relaxed">
        {inline(buf.join(" "))}
      </p>,
    );
  }
  return <Fragment>{out}</Fragment>;
}
