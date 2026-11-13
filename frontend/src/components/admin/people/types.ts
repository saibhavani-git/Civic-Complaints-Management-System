export type StaffRow = {
  id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  department_id?: string | null;
  department_name?: string | null;
  department_code?: string | null;
  phone?: string | null;
  active_assigned_count?: number;
  service_area?: string | null;
};

export type PersonCase = {
  id: string;
  complaint_id: string;
  title: string;
  status: string;
  priority: string;
  category?: string | null;
  address?: string | null;
  department_name?: string | null;
  department_code?: string | null;
  citizen_name?: string | null;
  officer_name?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type PersonCaseSummary = {
  total: number;
  solved: number;
  current: number;
  critical: number;
  critical_solved: number;
  high: number;
  medium: number;
  low: number;
  rejected: number;
  awaiting_close: number;
  assigned: number;
  in_progress: number;
  waiting_assignment: number;
  resolution_rate: number;
};

export type PersonCaseReport = {
  person: StaffRow & { scope: "assigned" | "reported" | "department" | "none" };
  summary: PersonCaseSummary;
  list_limit: number;
  critical: PersonCase[];
  current: PersonCase[];
  solved: PersonCase[];
};
