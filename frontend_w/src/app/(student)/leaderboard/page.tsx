import { AppFrame } from "@/components/layout/AppFrame";
import { LeaderboardView } from "@/features/gamification/screens/LeaderboardView";


export default function LeaderboardPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Leaderboard</h1>
        <p className="mt-2 text-sm text-muted">See how you rank against other learners by XP.</p>
      </div>
      <LeaderboardView />
    </AppFrame>
  );
}
