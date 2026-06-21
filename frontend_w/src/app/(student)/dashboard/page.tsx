import { AppFrame } from "@/components/layout/AppFrame";
import { DashboardView } from "@/features/dashboard/DashboardView";


export default function DashboardPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Dashboard</h1>
        <p className="mt-2 text-sm text-muted">Track progress, review goals, and see where to focus next.</p>
      </div>
      <DashboardView />
    </AppFrame>
  );
}
