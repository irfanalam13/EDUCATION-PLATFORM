import { apiRequest } from "./api";

export type TrendPoint = {
  date: string;
  active_users: number;
  learning_minutes: number;
  avg_quiz_score: number;
};

export type AssignmentStats = {
  published_assignments: number;
  expected_submissions: number;
  submissions: number;
  graded: number;
  completion_rate: number;
};

export type InstitutionOverview = {
  institution_id: number;
  window_days: number;
  metrics: {
    active_students: number;
    daily_active_users: number;
    monthly_active_users: number;
    learning_hours: number;
    quiz_performance: number;
    avg_mastery: number;
    attendance_rate: number;
    assignments: AssignmentStats;
  };
  trend: TrendPoint[];
};

export type TeacherOverview = {
  institution_id: number;
  teacher_id: number;
  batches: number;
  metrics: {
    students_taught: number;
    average_student_score: number;
    quiz_performance: number;
    engagement_rate: number;
    assignment_completion: AssignmentStats;
    weak_topics: { topic_id: number; topic: string; avg_mastery?: number; learners?: number }[];
  };
};

export type Institution = { id: number; name: string; slug: string };

export type AnalyticsReport = {
  id: number;
  scope: string;
  period: string;
  file_format: string;
  period_start: string;
  period_end: string;
  status: string;
  download_url: string | null;
  created_at: string;
};

export const fetchMyInstitutions = () => apiRequest<Institution[]>("/api/institutions/me/");

export const fetchInstitutionOverview = (institutionId: number, days = 30) =>
  apiRequest<InstitutionOverview>(`/api/analytics/institution/?institution_id=${institutionId}&days=${days}`);

export const fetchTeacherOverview = (institutionId: number, days = 30) =>
  apiRequest<TeacherOverview>(`/api/analytics/teacher/?institution_id=${institutionId}&days=${days}`);

export const fetchReports = (institutionId: number) =>
  apiRequest<AnalyticsReport[]>(`/api/analytics/reports/?institution_id=${institutionId}`);

export const generateReport = (institutionId: number, period: string, fileFormat: string) =>
  apiRequest<AnalyticsReport>("/api/analytics/report/generate/", {
    method: "POST",
    body: { institution_id: institutionId, scope: "INSTITUTION", period, file_format: fileFormat },
  });
