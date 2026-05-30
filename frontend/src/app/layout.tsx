import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { Providers } from "./providers";
import { BookOpen, MessageSquare, Layers, Languages, Network, Gauge, PencilRuler, Mic } from "lucide-react";

export const metadata: Metadata = {
  title: "English Tutor",
  description: "Personal English tutor powered by Claude",
};

const nav = [
  { href: "/", label: "Home", icon: BookOpen },
  { href: "/level", label: "Level", icon: Gauge },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/exercises", label: "Grammar", icon: PencilRuler },
  { href: "/pronounce", label: "Speak", icon: Mic },
  { href: "/notes", label: "Vault", icon: Network },
  { href: "/flashcards", label: "Cards", icon: Layers },
  { href: "/vocab", label: "Vocab", icon: Languages },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground">
        <Providers>
          <div className="flex min-h-screen">
            <aside className="w-56 border-r bg-muted/30 p-4 flex flex-col gap-1">
              <div className="px-2 py-3 mb-2 text-lg font-semibold">English Tutor</div>
              {nav.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-accent transition-colors"
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                );
              })}
            </aside>
            <main className="flex-1 p-6">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
