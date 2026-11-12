import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

export function getApiErrorMessage(error) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "Dữ liệu chưa hợp lệ. Bạn kiểm tra lại các trường đã nhập.";
  return "Chưa kết nối được máy chủ. Bạn thử lại sau nhé.";
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("familyconnect.token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const token = localStorage.getItem("familyconnect.token");
    if (error.response?.status === 401 && token && error.config?.headers?.Authorization === `Bearer ${token}`) {
      localStorage.removeItem("familyconnect.token");
      localStorage.removeItem("familyconnect.user");
      window.dispatchEvent(new Event("familyconnect:unauthorized"));
    }
    return Promise.reject(error);
  },
);
