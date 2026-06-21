import { AppFrame } from "@/components/layout/AppFrame";
import { LoginForm } from "@/features/auth/LoginForm";


export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const params = await searchParams;

  return (
    <AppFrame>
      <LoginForm nextTo={params.next} />
    </AppFrame>
  );
}
