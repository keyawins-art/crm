import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Auto-inject JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("crm_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("crm_token");
      localStorage.removeItem("crm_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth
export const authAPI = {
  login: (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);
    return api.post("/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  register: (data: { email: string; first_name: string; last_name: string; password: string; phone?: string }) =>
    api.post("/auth/register", data),
  me: () => api.get("/auth/me"),
};

// Accounts
export const accountsAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/accounts?page=${page}&size=${size}`),
  get: (id: string) => api.get(`/crm/accounts/${id}`),
  create: (data: any) => api.post("/crm/accounts", data),
  update: (id: string, data: any) => api.put(`/crm/accounts/${id}`, data),
  delete: (id: string) => api.delete(`/crm/accounts/${id}`),
};

// Contacts
export const contactsAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/contacts?page=${page}&size=${size}`),
  get: (id: string) => api.get(`/crm/contacts/${id}`),
  create: (data: any) => api.post("/crm/contacts", data),
  update: (id: string, data: any) => api.put(`/crm/contacts/${id}`, data),
  delete: (id: string) => api.delete(`/crm/contacts/${id}`),
};

// Leads
export const leadsAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/leads?page=${page}&size=${size}`),
  get: (id: string) => api.get(`/crm/leads/${id}`),
  create: (data: any) => api.post("/crm/leads", data),
  update: (id: string, data: any) => api.put(`/crm/leads/${id}`, data),
  delete: (id: string) => api.delete(`/crm/leads/${id}`),
  convert: (id: string, data: any) => api.post(`/crm/leads/${id}/convert`, data),
  activities: (id: string) => api.get(`/crm/leads/${id}/activities`),
  notes: (id: string) => api.get(`/crm/leads/${id}/notes`),
};

// Opportunities
export const opportunitiesAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/opportunities?page=${page}&size=${size}`),
  get: (id: string) => api.get(`/crm/opportunities/${id}`),
  create: (data: any) => api.post("/crm/opportunities", data),
  update: (id: string, data: any) => api.put(`/crm/opportunities/${id}`, data),
  delete: (id: string) => api.delete(`/crm/opportunities/${id}`),
};

// Tasks
export const tasksAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/tasks?page=${page}&size=${size}`),
  create: (data: any) => api.post("/crm/tasks", data),
  update: (id: string, data: any) => api.put(`/crm/tasks/${id}`, data),
  delete: (id: string) => api.delete(`/crm/tasks/${id}`),
};

// Reports
export const reportsAPI = {
  sales: () => api.get("/crm/reports/sales"),
  revenue: () => api.get("/crm/reports/revenue"),
  opportunities: () => api.get("/crm/reports/opportunities"),
};

// Dashboard
export const dashboardAPI = {
  stats: () => api.get("/dashboard/stats"),
  auditLogs: (limit = 10) => api.get(`/dashboard/audit-logs?limit=${limit}`),
};

// Sales Process
export const salesAPI = {
  salesOrders: (page = 1, size = 20) => api.get(`/crm/sales-orders?page=${page}&size=${size}`),
  invoices: (page = 1, size = 20) => api.get(`/crm/invoices?page=${page}&size=${size}`),
  convertToOrder: (quotationId: string) => api.post(`/crm/quotations/${quotationId}/convert-to-order`),
  convertToInvoice: (orderId: string) => api.post(`/crm/sales-orders/${orderId}/convert-to-invoice`),
  payInvoice: (invoiceId: string, amount: number, method = "Credit Card") =>
    api.post(`/crm/invoices/${invoiceId}/pay?amount=${amount}&payment_method=${method}`),
};

// Tickets
export const ticketsAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/tickets?page=${page}&size=${size}`),
  get: (id: string) => api.get(`/crm/tickets/${id}`),
  create: (data: any) => api.post("/crm/tickets", data),
  update: (id: string, data: any) => api.put(`/crm/tickets/${id}`, data),
  comments: (id: string) => api.get(`/crm/tickets/${id}/comments`),
  addComment: (id: string, data: any) => api.post(`/crm/tickets/${id}/comments`, data),
};
