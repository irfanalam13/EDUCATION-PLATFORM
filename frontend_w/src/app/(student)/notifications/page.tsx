import { AppFrame } from "@/components/layout/AppFrame";
import { NotificationCenter } from "@/features/notifications/screens/NotificationCenter";


export default function NotificationsPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Notifications</h1>
        <p className="mt-2 text-sm text-muted">Quiz results, level-ups, badges, and announcements.</p>
      </div>
      <NotificationCenter />
    </AppFrame>
  );
}
