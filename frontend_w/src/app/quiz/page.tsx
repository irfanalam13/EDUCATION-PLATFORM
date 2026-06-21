import { AppFrame } from "@/components/layout/AppFrame";
import { Card } from "@/components/ui/Card";
import { QuizPlayer } from "@/features/quiz/QuizPlayer";


export default async function QuizPage({
  searchParams,
}: {
  searchParams: Promise<{ topic?: string }>;
}) {
  const params = await searchParams;
  const topicId = params.topic ? Number(params.topic) : 0;

  return (
    <AppFrame>
      {topicId ? (
        <QuizPlayer topicId={topicId} />
      ) : (
        <Card className="p-6">
          <h1 className="text-2xl font-semibold">Quiz workspace</h1>
          <p className="mt-2 text-sm text-muted">Open this page with a topic id, like <code>?topic=1</code>, from the learning catalog.</p>
        </Card>
      )}
    </AppFrame>
  );
}
