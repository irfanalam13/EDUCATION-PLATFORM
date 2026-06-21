import { AppFrame } from "@/components/layout/AppFrame";
import { AssistantChat } from "@/features/assistant/AssistantChat";


export default function AssistantPage() {
  return (
    <AppFrame>
      <AssistantChat />
    </AppFrame>
  );
}
