import type { Correction } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function CorrectionPanel({ items }: { items: Correction[] }) {
  if (!items?.length) return null;
  return (
    <Card className="border-amber-300 bg-amber-50/50 dark:bg-amber-950/20">
      <CardHeader>
        <CardTitle className="text-sm text-amber-900 dark:text-amber-100">
          Корректировки ({items.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.map((c, i) => (
          <div key={i} className="text-sm space-y-1">
            <div>
              <span className="line-through text-destructive">{c.original}</span>
              <span className="mx-2">→</span>
              <span className="font-medium text-emerald-700 dark:text-emerald-300">{c.fixed}</span>
            </div>
            <div className="text-muted-foreground">{c.explanation_ru}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
