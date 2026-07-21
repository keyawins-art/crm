import { authAPI } from "./api";

export function getToken(): string | null {
  return localStorage.getItem("crm_token");
}

export function getUser(): any | null {
  const raw = localStorage.getItem("crm_user");
  return raw ? JSON.parse(raw) : null;
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export async function login(email: string, password: string) {
  const res = await authAPI.login(email, password);
  const { access_token, refresh_token } = res.data;
  localStorage.setItem("crm_token", access_token);
  if (refresh_token) localStorage.setItem("crm_refresh_token", refresh_token);

  // Fetch user profile
  const meRes = await authAPI.me();
  localStorage.setItem("crm_user", JSON.stringify(meRes.data));
  return meRes.data;
}

export async function logout() {
  try {
    const refreshToken = localStorage.getItem("crm_refresh_token");
    // Revoke the token server-side before clearing local storage
    await authAPI.logout(refreshToken ? { refresh_token: refreshToken } : undefined);
  } catch {
    // Even if the API call fails (e.g. token already expired), clear local state
  }
  localStorage.removeItem("crm_token");
  localStorage.removeItem("crm_refresh_token");
  localStorage.removeItem("crm_user");
  window.location.href = "/login";
}
