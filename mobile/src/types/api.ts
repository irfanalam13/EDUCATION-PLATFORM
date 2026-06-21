export type Role = "STUDENT" | "TEACHER" | "AUTHOR" | "ADMIN";

// ---- AI Learning Intelligence ----
export type MasteryBand = "beginner" | "developing" | "proficient" | "mastered";
export type AiMasteryTopic = {
  topic_id: number;
  topic_title: string;
  chapter: string;
  subject: string;
  mastery: number;
  accuracy: number;
  band: MasteryBand;
};
export type AiMastery = {
  overall_mastery: number;
  band_distribution: Record<MasteryBand, number>;
  topics: AiMasteryTopic[];
};
export type AiWeakTopic = {
  topic: number;
  topic_title: string;
  weak_score: number;
  mastery: number;
  accuracy: number;
  band: MasteryBand;
  reason: string;
};
export type AiRecommendation = {
  id: number;
  topic: number | null;
  topic_title: string | null;
  kind: "learn" | "revise" | "practice" | "prerequisite";
  title: string;
  message: string;
  priority: number;
};
export type AiStudySession = {
  id: number;
  topic_title: string | null;
  start_time: string;
  duration_min: number;
  activity_type: string;
  title: string;
};
export type AiStudyPlan = {
  id: number;
  date: string;
  total_minutes: number;
  sessions: AiStudySession[];
};

export type User = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  email_verified: boolean;
  auth_provider: "password" | "google";
  profile?: {
    student_class?: string;
    college?: string;
    bio?: string;
    avatar?: string | null;
  };
};

export type DashboardPayload = {
  today: {
    date?: string;
    minutes: number;
    attempted: number;
    correct: number;
    xp_earned: number;
  };
  streak: {
    current_streak: number;
    best_streak: number;
    last_active_date: string | null;
  };
  goals: {
    daily_minutes_goal: number;
    daily_attempt_goal: number;
    weekly_topics_mastered_goal: number;
  };
  totals: {
    topics: number;
    total_answered: number;
    correct: number;
    avg_mastery: number;
  };
  mastery_buckets: Record<string, number>;
  weak_topics: Array<{ topic: number; weakness_score: number }>;
  due_topics: Array<{ topic: number; mastery: number; accuracy: number; next_review_at: string | null }>;
  activity_7d: Array<{ date: string; minutes: number; xp_earned: number }>;
};

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Level = { id: number; name: string; order: number; is_active: boolean };

export type Subject = {
  id: number;
  name: string;
  code: string;
  order: number;
  level: number;
  level_name: string;
  stream: number | null;
  stream_name: string | null;
};

export type Chapter = {
  id: number;
  title: string;
  number: number;
  order: number;
  subject: number;
  subject_name: string;
};

export type AcademicTopic = {
  id: number;
  title: string;
  order: number;
  content: string;
  chapter: number;
  chapter_title: string;
  tags: string[];
};

export type ContentTopic = { id: number; chapter: number; title: string };

export type ContentNote = {
  id: number;
  topic: number;
  title: string;
  content_richtext: string;
  visibility: "public" | "unlisted" | "private";
  created_at: string;
  updated_at: string;
};

export type McqChoice = { id: number; choice_text: string };

export type McqQuestion = {
  id: number;
  topic: number;
  question_text: string;
  difficulty: "easy" | "medium" | "hard";
  choices: McqChoice[];
};
