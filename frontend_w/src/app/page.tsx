import Link from "next/link";

import { AppFrame } from "@/components/layout/AppFrame";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";


const pillars = [
  { title: "Curriculum Browser", body: "Move from level to subject, chapter, and topic without getting lost." },
  { title: "Focused Practice", body: "Answer topic-wise MCQs and revisit weak areas from one place." },
  { title: "Notes Workspace", body: "Keep lesson notes, markdown drafts, and revision snippets together." },
  { title: "AI Study Assistant", body: "Use a guided chat surface for course questions and uploaded material." },
];

export default function HomePage() {
  return (
    <AppFrame>
      <div className="grid gap-6 lg:grid-cols-[1.3fr_0.9fr]">
        <section className="rounded-lg border border-app bg-card p-8 shadow-panel">
          <div className="inline-flex rounded-full bg-cyan-50 px-3 py-1 text-xs font-medium text-cyan-700 dark:bg-cyan-950/60 dark:text-cyan-200">
            Built for structured, repeatable learning
          </div>
          <h1 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
            A practical learning workspace for Nepal-focused digital education.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
            Start with the curriculum browser, move into topic study, practice with quizzes, keep notes in sync, and
            stay on track with a lightweight dashboard.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/academics">
              <Button>Browse curriculum</Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="secondary">Open dashboard</Button>
            </Link>
            <Link href="/assistant">
              <Button variant="secondary">Try AI chat</Button>
            </Link>
          </div>
        </section>

        <Card className="p-6">
          <h2 className="text-lg font-semibold">Today&apos;s workflow</h2>
          <div className="mt-5 space-y-4 text-sm">
            <div className="rounded-md border border-app p-4">
              <div className="font-medium">1. Pick a topic</div>
              <div className="mt-1 text-muted">Open a chapter, read the concept summary, and jump into notes or quiz.</div>
            </div>
            <div className="rounded-md border border-app p-4">
              <div className="font-medium">2. Practice with intent</div>
              <div className="mt-1 text-muted">Use topic-wise MCQs to see what still needs work.</div>
            </div>
            <div className="rounded-md border border-app p-4">
              <div className="font-medium">3. Close the loop</div>
              <div className="mt-1 text-muted">Capture notes, check dashboard trends, and queue the next review.</div>
            </div>
          </div>
        </Card>
      </div>

      <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {pillars.map((pillar) => (
          <Card key={pillar.title} className="p-5">
            <h3 className="text-base font-semibold">{pillar.title}</h3>
            <p className="mt-2 text-sm leading-6 text-muted">{pillar.body}</p>
          </Card>
        ))}
      </section>
    </AppFrame>
  );
}
