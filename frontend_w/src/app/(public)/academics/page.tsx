import { AppFrame } from "@/components/layout/AppFrame";
import { LearnBrowser } from "@/features/learn/LearnBrowser";


export default function AcademicsPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Learning catalog</h1>
        <p className="mt-2 text-sm text-muted">Browse the curriculum hierarchy and open the content workspace where notes and resources live.</p>
      </div>
      <LearnBrowser />
    </AppFrame>
  );
}
