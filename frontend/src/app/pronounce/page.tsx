"use client";

import { useEffect, useRef, useState } from "react";
import { api, API_BASE, type PronunciationResult } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function PronouncePage() {
  const [phrase, setPhrase] = useState<string>("");
  const [loadingPhrase, setLoadingPhrase] = useState(false);
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<PronunciationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function newPhrase() {
    setLoadingPhrase(true);
    setResult(null);
    setError(null);
    try {
      const res = await api.get<{ phrase: string }>("/api/v1/pronounce/practice");
      setPhrase(res.data.phrase);
    } catch (_e) {
      setError("Не удалось получить фразу");
    } finally {
      setLoadingPhrase(false);
    }
  }

  useEffect(() => {
    newPhrase();
  }, []);

  // Pick the first MIME type the browser actually supports.
  // Safari/iOS doesn't do webm at all; it speaks mp4. Chrome/Firefox prefer webm.
  function pickRecorderMime(): { mime: string; ext: string } | null {
    const candidates: { mime: string; ext: string }[] = [
      { mime: "audio/webm;codecs=opus", ext: "webm" },
      { mime: "audio/webm", ext: "webm" },
      { mime: "audio/mp4;codecs=mp4a.40.2", ext: "m4a" },
      { mime: "audio/mp4", ext: "m4a" },
      { mime: "audio/aac", ext: "aac" },
      { mime: "audio/ogg;codecs=opus", ext: "ogg" },
    ];
    for (const c of candidates) {
      try {
        if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(c.mime)) {
          return c;
        }
      } catch {
        // some browsers throw rather than returning false
      }
    }
    return null;
  }

  async function startRecording() {
    setError(null);
    setResult(null);

    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setError("Браузер не поддерживает запись с микрофона");
      return;
    }
    const picked = pickRecorderMime();
    if (!picked) {
      setError("Этот браузер не умеет записывать аудио. Попробуй Chrome/Safari/Firefox.");
      return;
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`Нет доступа к микрофону: ${msg}`);
      return;
    }

    try {
      const rec = new MediaRecorder(stream, { mimeType: picked.mime });
      chunksRef.current = [];
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: picked.mime });
        await upload(blob, picked.ext);
      };
      recorderRef.current = rec;
      rec.start();
      setRecording(true);
    } catch (e) {
      stream.getTracks().forEach((t) => t.stop());
      const msg = e instanceof Error ? e.message : String(e);
      setError(`Не удалось запустить запись: ${msg}`);
    }
  }

  function stopRecording() {
    recorderRef.current?.stop();
    setRecording(false);
  }

  async function upload(blob: Blob, ext: string) {
    if (blob.size === 0) {
      setError("Запись пустая — попробуй ещё раз");
      return;
    }
    setProcessing(true);
    try {
      const form = new FormData();
      form.append("audio", blob, `rec.${ext}`);
      form.append("target_text", phrase);
      const res = await fetch(`${API_BASE}/api/v1/pronounce/transcribe`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const body = await res.text().catch(() => "");
        setError(`Ошибка: HTTP ${res.status}${body ? " — " + body.slice(0, 200) : ""}`);
        return;
      }
      const data: PronunciationResult = await res.json();
      setResult(data);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`Не удалось отправить запись: ${msg}`);
    } finally {
      setProcessing(false);
    }
  }

  const scorePct = result ? Math.round(result.overall_score * 100) : 0;

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Произношение</h1>
        <Button variant="outline" size="sm" onClick={newPhrase} disabled={loadingPhrase}>
          {loadingPhrase ? "..." : "Новая фраза"}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Прочитай вслух</CardTitle>
        </CardHeader>
        <CardContent>
          {phrase ? (
            <p className="text-xl font-medium leading-relaxed">{phrase}</p>
          ) : loadingPhrase ? (
            <div className="flex items-center gap-3 text-muted-foreground">
              <div className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />
              <div>
                <div className="text-sm">Claude придумывает фразу…</div>
                <div className="text-xs opacity-70">обычно 5–15 секунд</div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Не удалось получить фразу. Нажми «Новая фраза».</p>
          )}
          <div className="mt-4 flex gap-2">
            {!recording ? (
              <Button onClick={startRecording} disabled={processing || !phrase}>
                🎤 Запись
              </Button>
            ) : (
              <Button onClick={stopRecording} variant="destructive">
                ⏹ Стоп
              </Button>
            )}
            {processing && <span className="text-sm text-muted-foreground self-center">Анализирую…</span>}
          </div>
          {error && <p className="text-sm text-destructive mt-2">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center justify-between">
              <span>Результат</span>
              <span className={
                scorePct >= 80 ? "text-emerald-600 text-2xl font-bold" :
                scorePct >= 50 ? "text-amber-600 text-2xl font-bold" :
                "text-destructive text-2xl font-bold"
              }>{scorePct}%</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-sm">
              <div className="text-xs text-muted-foreground mb-1">Whisper расслышал:</div>
              <p className="font-mono bg-muted/40 rounded px-2 py-1">{result.transcript || "(тишина)"}</p>
            </div>
            <div className="flex flex-wrap gap-1">
              {result.per_word.map((w, i) => {
                const color =
                  w.status === "matched"
                    ? "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-200"
                    : w.status === "substituted"
                    ? "bg-amber-100 text-amber-900 dark:bg-amber-900/30 dark:text-amber-200"
                    : "bg-red-100 text-red-900 dark:bg-red-900/30 dark:text-red-200";
                return (
                  <span key={i} className={`px-2 py-1 rounded text-sm ${color}`} title={w.heard ? `услышано: ${w.heard}` : undefined}>
                    {w.word}
                    {w.heard ? ` → ${w.heard}` : ""}
                  </span>
                );
              })}
            </div>
            {result.tip_ru && (
              <div className="rounded-md bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 px-3 py-2 text-sm">
                💡 {result.tip_ru}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
