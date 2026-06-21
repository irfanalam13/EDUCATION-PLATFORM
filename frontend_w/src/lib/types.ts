export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type SessionUser = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: "STUDENT" | "TEACHER" | "AUTHOR" | "ADMIN";
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

export type ContentNote = {
  id: number;
  topic: number;
  title: string;
  content_richtext: string;
  visibility: "public" | "unlisted" | "private";
  created_at: string;
  updated_at: string;
};

export type TopicResource = {
  id: number;
  topic: number;
  resource_type: "note" | "video" | "link" | "attachment";
  note: number | null;
  attachment: number | null;
  url: string;
};

// ---- Gamification ----
export type BadgeInfo = {
  id: number;
  code: string;
  name: string;
  description: string;
  icon: string;
};
export type UserBadge = {
  id: number;
  badge: BadgeInfo;
  awarded_at: string;
  metadata: Record<string, unknown>;
};
export type GamificationProfile = {
  level: number;
  total_xp: number;
  streak_days: number;
  longest_streak: number;
  freeze_tokens: number;
  badges: UserBadge[];
};
export type LeaderboardEntry = {
  user_id: number;
  username: string;
  display_name: string;
  scope: string;
  scope_id: string;
  period: string;
  period_key: string;
  xp_total: number;
  updated_at: string;
};
export type LeaderboardMe = {
  ok: boolean;
  rank_in_top200: number | null;
  count_considered: number;
};
export type QuestProgress = {
  id: number;
  quest: {
    id: number;
    code: string;
    name: string;
    description: string;
    rules: Record<string, unknown>;
    reward: Record<string, unknown>;
    is_active: boolean;
  };
  progress: number;
  is_completed: boolean;
  is_claimed: boolean;
  updated_at: string;
};

// ---- Notifications ----
export type AppNotification = {
  id: string;
  title: string;
  body: string;
  type: "SYSTEM" | "XP" | "BADGE" | "QUIZ" | "ANNOUNCEMENT";
  data: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};

// ---- AI Learning Intelligence ----
export type MasteryBand = "beginner" | "developing" | "proficient" | "mastered";

export type AiMasteryTopic = {
  topic_id: number;
  topic_title: string;
  chapter: string;
  subject: string;
  subject_id: number | null;
  mastery: number;
  accuracy: number;
  band: MasteryBand;
  attempts: number;
  last_practiced_at: string | null;
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
  computed_at: string;
};
export type AiRecommendation = {
  id: number;
  topic: number | null;
  topic_title: string | null;
  kind: "learn" | "revise" | "practice" | "prerequisite";
  title: string;
  message: string;
  priority: number;
  status: string;
  created_at: string;
};
export type AiStudySession = {
  id: number;
  topic: number | null;
  topic_title: string | null;
  order: number;
  start_time: string;
  duration_min: number;
  activity_type: "revision" | "quiz" | "practice" | "notes";
  title: string;
  completed: boolean;
};
export type AiStudyPlan = {
  id: number;
  date: string;
  total_minutes: number;
  status: string;
  generated_at: string;
  sessions: AiStudySession[];
};

export type McqChoice = { id: number; choice_text: string };
export type McqQuestion = {
  id: number;
  topic: number;
  question_text: string;
  difficulty: "easy" | "medium" | "hard";
  choices: McqChoice[];
};
