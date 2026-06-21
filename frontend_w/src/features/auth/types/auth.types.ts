export type Role = "STUDENT" | "TEACHER" | "AUTHOR" | "ADMIN";

export type TeacherStatus =
  | "NONE"
  | "PENDING"
  | "APPROVED"
  | "REJECTED";

export interface Profile {
  teacher_status: TeacherStatus;
  teacher_message?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: Role;
  email_verified: boolean;
  auth_provider: "password" | "google";
  profile: Profile;
}
