import { AppFrame } from "@/components/layout/AppFrame";
import { NotesWorkspace } from "@/features/notes/NotesWorkspace";


export default async function NotesPage({
  searchParams,
}: {
  searchParams: Promise<{ topic?: string }>;
}) {
  const params = await searchParams;
  const topicId = params.topic ? Number(params.topic) : undefined;

  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Notes</h1>
        <p className="mt-2 text-sm text-muted">Write markdown-style lesson notes and keep them grouped by content topic.</p>
      </div>
      <NotesWorkspace initialTopicId={topicId} />
    </AppFrame>
  );
}
