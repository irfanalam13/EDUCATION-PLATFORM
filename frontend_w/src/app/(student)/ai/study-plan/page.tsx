import { AppFrame } from "@/components/layout/AppFrame";
import { StudyPlanView } from "@/features/ai/screens/StudyPlanView";


export default function AiStudyPlanPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Study Plan</h1>
        <p className="mt-2 text-sm text-muted">Your AI-scheduled daily timetable.</p>
      </div>
      <StudyPlanView />
    </AppFrame>
  );
}
