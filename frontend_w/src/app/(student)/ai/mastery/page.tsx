import { AppFrame } from "@/components/layout/AppFrame";
import { MasteryMap } from "@/features/ai/screens/MasteryMap";


export default function AiMasteryPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Mastery Map</h1>
        <p className="mt-2 text-sm text-muted">Heatmap of your strengths across the curriculum.</p>
      </div>
      <MasteryMap />
    </AppFrame>
  );
}
