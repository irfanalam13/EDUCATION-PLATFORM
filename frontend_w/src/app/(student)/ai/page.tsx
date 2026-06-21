import { AppFrame } from "@/components/layout/AppFrame";
import { AiDashboard } from "@/features/ai/screens/AiDashboard";


export default function AiDashboardPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">AI Study Coach</h1>
        <p className="mt-2 text-sm text-muted">Personalized guidance on what to study next.</p>
      </div>
      <AiDashboard />
    </AppFrame>
  );
}
