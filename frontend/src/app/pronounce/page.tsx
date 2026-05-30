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

  async function startRecording() {
    setError(null);
    setResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      chunksRef.current = [];
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await upload(blob);
      };
      recorderRef.current = rec;
      rec.start();
      setRecording(true);
    } catch (_e) {
      setError("Нет доступа к микрофону");
    }
  }

  function stopRecording() {
    recorderRef.current?.stop();
    setRecording(false);
  }

  async function upload(blob: Blob) {
    setProcessing(true);
    try {
      const form = new FormData();
      form.append("audio", blob, "rec.webm");
      form.append("target_text", phrase);
      const res = await fetch(`${API_BASE}/api/v1/pronounce/transcribe`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        setError(`Ошибка: HTTP ${res.status}`);
        return;
      }
      const data: PronunciationResult = await res.json();
      setResult(data);
    } catch (_e) {
      setError("Не удалось отправить запись");
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
          <p className="text-xl font-medium leading-relaxed">{phrase || "..."}</p>
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
            {processing && <span className="text-sm text-muted-foreground self-center">Анализирую...</span>}
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
