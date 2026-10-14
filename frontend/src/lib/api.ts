import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (config.data instanceof FormData && config.headers) {
    if (typeof config.headers.setContentType === "function") {
      config.headers.setContentType(false);
    } else {
      delete (config.headers as Record<string, unknown>)["Content-Type"];
    }
  }
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem("access_token", data.access_token);
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; phone: string }) =>
    api.post("/auth/register", data),
  updateProfile: (data: { full_name: string; phone: string }) => api.patch("/auth/me", data),
  login: (data: { email: string; password: string }) => api.post("/auth/login", data),
  logout: (refresh_token: string) => api.post("/auth/logout", { refresh_token }),
  me: () => api.get("/auth/me"),
  forgotPassword: (email: string) => api.post("/auth/forgot-password", { email }),
  resetPassword: (token: string, new_password: string) =>
    api.post("/auth/reset-password", { token, new_password }),
};

export const complaintsApi = {
  list: (params?: {
    page?: number;
    limit?: number;
    status?: string;
    priority?: string;
    awaiting_assignment?: boolean;
  }) => api.get("/complaints", { params }),
  get: (id: string) => api.get(`/complaints/${id}`),
  create: (formData: FormData) =>
    api.post("/complaints", formData, {
      timeout: 90000,
    }),
  updateStatus: (id: string, data: { status: string; note?: string }) =>
    api.patch(`/complaints/${id}/status`, { status: data.status, note: data.note }),
  resolve: (id: string, notes: string) =>
    api.post(`/complaints/${id}/resolve`, { notes }),
  submitFeedback: (id: string, data: { rating: number; comment?: string }) =>
    api.post(`/complaints/${id}/feedback`, data),
  nearby: (id: string, radius?: number) =>
    api.get(`/complaints/${id}/nearby`, { params: { radius } }),
  assign: (id: string, officer_id: string) =>
    api.post(`/complaints/${id}/assign`, { officer_id }),
};

export const staffApi = {
  listOfficers: (department_id?: string) =>
    api.get("/staff/officers", { params: department_id ? { department_id } : {} }),
  listTeam: () => api.get("/staff/team"),
  addWorker: (data: {
    email: string;
    password: string;
    full_name: string;
    phone: string;
    service_area: string;
  }) => api.post("/staff/team", data),
};

export const clustersApi = {
  list: () => api.get("/clusters"),
  updateStatus: (id: string, status: string) => api.patch(`/clusters/${id}/status`, { status }),
};

export const auditApi = {
  chain: (complaintId: string) => api.get(`/audit/complaints/${complaintId}/chain`),
};

export const analyticsApi = {
  overview: () => api.get("/analytics/overview"),
  byDepartment: () => api.get("/analytics/by-department"),
  trends: () => api.get("/analytics/trends"),
  heatmap: () => api.get("/analytics/heatmap"),
  officerWorkload: () => api.get("/analytics/officer-workload"),
};

export const notificationsApi = {
  list: (unread_only?: boolean) =>
    api.get("/notifications", { params: { unread_only } }),
  markRead: (id: string) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch("/notifications/read-all"),
};

export const adminApi = {
  listUsers: () => api.get("/admin/users"),
  createUser: (data: Record<string, unknown>) => api.post("/admin/users", data),
  listDepartments: () => api.get("/admin/departments"),
  createDepartment: (data: Record<string, unknown>) => api.post("/admin/departments", data),
};
