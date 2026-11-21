export type UserRole = 'student' | 'professor' | 'admin';

export type SessionState = 'attempt' | 'guided' | 'validate' | 'done' | 'abandoned';

export type UnlockReason = 'effort' | 'stuck_declared' | 'policy';

export type TutorRung = 'guide' | 'help' | 'hint' | 'critical_hint';

export type ProblemType = 'theory' | 'numeric' | 'coding';

export type AIPolicy = 'locked' | 'guided' | 'open';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  institution_id?: string | null;
  locale: string;
  created_at: string;
  consent_flags: {
    audio_retention: boolean;
    analytics_sharing: boolean;
    professor_sharing: boolean;
  };
}

export interface Problem {
  id: string;
  title: string;
  statement_md: string;
  subject: string;
  difficulty_b: number;
  type: ProblemType;
  concept_ids: string[];
  created_by?: string | null;
  visibility: 'public' | 'course' | 'private';
  created_at?: string;
  rubric?: Record<string, unknown>;
  test_cases?: Array<{
    input: string;
    expected_output: string;
    is_hidden?: boolean;
  }>;
}

export interface Session {
  id: string;
  student_id: string;
  problem_id: string;
  assignment_id?: string | null;
  state: SessionState;
  started_at: string;
  attempt_started_at: string;
  unlocked_at?: string | null;
  validate_started_at?: string | null;
  ended_at?: string | null;
  unlock_reason?: UnlockReason | null;
  effort_score: number;
  help_cost: number;
}

export interface TutorMessage {
  id: string;
  session_id: string;
  role: 'student' | 'tutor';
  rung?: TutorRung | null;
  content: string;
  leak_check?: {
    passed: boolean;
    method: string;
    score?: number;
    details?: string;
  } | null;
  ts: string;
}

export interface ValidationResult {
  id: string;
  session_id: string;
  mode: 'explain' | 'similar';
  variant_id?: string | null;
  transcript?: string | null;
  audio_uri?: string | null;
  rubric_scores: Record<string, number>;
  confidence: number;
  passed: boolean;
  consistency_score: number;
  created_at: string;
}

export interface DailyStats {
  date: string;
  active_minutes: number;
  flow_minutes: number;
  self_solves: number;
  ai_assisted: number;
  its: number;
  adr: number;
}
