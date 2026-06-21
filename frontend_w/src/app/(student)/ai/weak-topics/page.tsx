import { AppFrame } from "@/components/layout/AppFrame";
import { WeakTopicsList } from "@/features/ai/screens/WeakTopicsList";


export default function AiWeakTopicsPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Weak Topics</h1>
        <p className="mt-2 text-sm text-muted">Topics most at risk, scored by the AI engine.</p>
      </div>
      <WeakTopicsList />
    </AppFrame>
  );
}
