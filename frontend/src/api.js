import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api",
  timeout: 20000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original?._retry) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        original._retry = true;
        try {
          const response = await axios.post(
            `${api.defaults.baseURL}/auth/token/refresh/`,
            { refresh },
          );
          localStorage.setItem("access_token", response.data.access);
          if (response.data.refresh) localStorage.setItem("refresh_token", response.data.refresh);
          original.headers.Authorization = `Bearer ${response.data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  },
);

export function listData(response) {
  return Array.isArray(response.data) ? response.data : response.data.results || [];
}

export function errorMessage(error) {
  const data = error.response?.data;
  if (!data) return error.message || "Unexpected error";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  return Object.entries(data)
    .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`)
    .join(" | ");
}

export default api;
