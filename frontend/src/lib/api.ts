import axios from "axios";

// Dynamically use the host IP so that it works across the local network
const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
const API_BASE_URL = `http://${host}:8000`;

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

// Quotations
export const quotationsAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/quotations?page=${page}&size=${size}`),
  get: (id: string) => api.get(`/crm/quotations/${id}`),
  create: (data: any) => api.post("/crm/quotations", data),
  update: (id: string, data: any) => api.put(`/crm/quotations/${id}`, data),
  delete: (id: string) => api.delete(`/crm/quotations/${id}`),
};

// Sales Process
export const salesAPI = {
  salesOrders: (page = 1, size = 20) => api.get(`/crm/sales-orders?page=${page}&size=${size}`),
  getSalesOrder: (id: string) => api.get(`/crm/sales-orders/${id}`),
  createSalesOrder: (data: any) => api.post("/crm/sales-orders", data),
  updateSalesOrder: (id: string, data: any) => api.put(`/crm/sales-orders/${id}`, data),
  deleteSalesOrder: (id: string) => api.delete(`/crm/sales-orders/${id}`),
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

// Users
export const usersAPI = {
  list: () => api.get("/crm/users"),
  create: (data: any) => api.post("/crm/users", data),
  update: (id: string, data: any) => api.put(`/crm/users/${id}`, data),
  delete: (id: string) => api.delete(`/crm/users/${id}`),
};

// Roles
export const rolesAPI = {
  list: () => api.get("/crm/roles"),
};

// Calendar
export const calendarAPI = {
  getEvents: (start?: string, end?: string) => {
    let url = "/crm/calendar";
    const params = new URLSearchParams();
    if (start) params.append("start_date", start);
    if (end) params.append("end_date", end);
    if (params.toString()) url += `?${params.toString()}`;
    return api.get(url);
  },
};

// Meetings
export const meetingsAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/meetings?page=${page}&size=${size}`),
  create: (data: any) => api.post("/crm/meetings", data),
};

// Calls
export const callsAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/calls?page=${page}&size=${size}`),
  create: (data: any) => api.post("/crm/calls", data),
};

// Emails
export const emailsAPI = {
  logs: (page = 1, size = 20) => api.get(`/crm/email-logs?page=${page}&size=${size}`),
  send: (data: { to_email: string; subject: string; body: string }) => api.post("/crm/emails/send", data),
};

// Knowledge Base
export const knowledgeBaseAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/knowledge-base?page=${page}&size=${size}`),
  get: (id: string) => api.get(`/crm/knowledge-base/${id}`),
  create: (data: any) => api.post("/crm/knowledge-base", data),
  update: (id: string, data: any) => api.put(`/crm/knowledge-base/${id}`, data),
  delete: (id: string) => api.delete(`/crm/knowledge-base/${id}`),
};

// Documents
export const documentsAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/documents?page=${page}&size=${size}`),
  upload: (data: any) => api.post("/crm/documents", data),
};

// Workflows
export const workflowsAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/workflows?page=${page}&size=${size}`),
  create: (data: any) => api.post("/crm/workflows", data),
  delete: (id: string) => api.delete(`/crm/workflows/${id}`),
};

// Integrations
export const integrationsAPI = {
  list: () => api.get("/crm/integrations"),
  connect: (provider: string, data: any) => api.post(`/crm/integrations/${provider}/connect`, data),
  disconnect: (provider: string) => api.post(`/crm/integrations/${provider}/disconnect`),
};

// Notifications
export const notificationsAPI = {
  list: (page = 1, size = 20) => api.get(`/crm/notifications?page=${page}&size=${size}`),
  readAll: () => api.post("/crm/notifications/read-all"),
  read: (id: string) => api.post(`/crm/notifications/${id}/read`),
};
