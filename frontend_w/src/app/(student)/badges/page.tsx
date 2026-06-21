import { AppFrame } from "@/components/layout/AppFrame";
import { GamificationView } from "@/features/gamification/screens/GamificationView";


export default function BadgesPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Achievements</h1>
        <p className="mt-2 text-sm text-muted">Your XP, level, streak, badges, and quests.</p>
      </div>
      <GamificationView />
    </AppFrame>
  );
}
