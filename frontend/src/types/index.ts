export type UserRole = "citizen" | "officer" | "dept_admin" | "admin";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  phone?: string;
  department_id?: string;
  department_name?: string;
  department_code?: string;
  service_area?: string;
  department_area?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export type ComplaintStatus =
  | "submitted"
  | "ai_processing"
  | "routed_to_department"
  | "ai_processed"
  | "verified"
  | "assigned"
  | "work_started"
  | "resolved"
  | "feedback_received"
  | "pending"
  | "in_progress"
  | "closed"
  | "rejected";

export type Priority = "low" | "medium" | "high" | "critical";

export interface AIMetadata {
  summary?: string;
  category?: string;
  category_confidence?: number;
  predicted_department?: string;
  predicted_priority?: string;
  confidence_score?: number;
  is_duplicate: boolean;
  duplicate_of?: string;
  similarity_score?: number;
}

export interface Complaint {
  id: string;
  complaint_id: string;
  category?: string;
  title: string;
  description: string;
  images: { url: string; public_id: string }[];
  location: { coordinates: number[]; address: string };
  status: ComplaintStatus;
  priority: Priority;
  department_id?: string;
  department_name?: string;
  assigned_officer_id?: string;
  assigned_officer_name?: string;
  assigned_officer_email?: string;
  assigned_officer_phone?: string;
  citizen_name?: string;
  citizen_email?: string;
  citizen_phone?: string;
  ai_metadata?: AIMetadata;
  resolution?: { notes: string; resolved_at: string };
  status_history?: { status: string; changed_by: string; changed_at: string; note?: string }[];
  created_at: string;
  updated_at: string;
}

export interface AnalyticsOverview {
  total_complaints: number;
  pending: number;
  in_progress: number;
  resolved: number;
  avg_resolution_hours: number;
  priority_distribution: Record<Priority, number>;
  resolution_rate: number;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  complaint_id?: string;
  is_read: boolean;
  created_at: string;
}
