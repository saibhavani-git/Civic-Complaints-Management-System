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
