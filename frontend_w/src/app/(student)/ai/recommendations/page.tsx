import { AppFrame } from "@/components/layout/AppFrame";
import { RecommendationsList } from "@/features/ai/screens/RecommendationsList";


export default function AiRecommendationsPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Recommendations</h1>
        <p className="mt-2 text-sm text-muted">Ranked next-best actions for your learning.</p>
      </div>
      <RecommendationsList />
    </AppFrame>
  );
}
