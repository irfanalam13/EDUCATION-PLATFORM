import { api } from "@/shared/lib/http";

export type MeDTO = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: "STUDENT" | "TEACHER" | "ADMIN";
  profile?: {
    student_class?: string;
    college?: string;
    avatar?: string | null;
    bio?: string;
  };
};


export const accountsApi = {
  me() {
    return api("/api/accounts/me/", { auth: true });
  },
};
