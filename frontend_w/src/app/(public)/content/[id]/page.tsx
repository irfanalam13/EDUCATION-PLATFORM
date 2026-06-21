import { AppFrame } from "@/components/layout/AppFrame";
import { CourseViewer } from "@/features/content/CourseViewer";


export default async function ContentTopicPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <AppFrame>
      <CourseViewer topicId={Number(id)} />
    </AppFrame>
  );
}
