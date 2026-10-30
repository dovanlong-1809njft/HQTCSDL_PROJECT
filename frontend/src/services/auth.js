import axios from "axios";
import { api } from "./api";

function normalizeRole(role) {
  if (role === "admin" || role === "family_head" || role === "guest") return role;
  return "member";
}

function toSession(response, email) {
  const user = response.user ?? {};
  const token = response.access_token ?? response.token;
  if (!token) throw new Error("Máy chủ chưa trả về access token.");

  return {
    accessToken: token,
    user: {
      id: String(user.id ?? user.email ?? email),
      fullName: user.fullName ?? user.full_name ?? user.name ?? email.split("@")[0],
      email: user.email ?? email,
      role: normalizeRole(user.role),
      avatarUrl: user.avatarUrl ?? user.avatar_url,
    },
  };
}

export async function login(payload) {
  try {
    const { data } = await api.post("/auth/login", payload);
    return toSession(data, payload.email);
  } catch (error) {
    const mockEnabled = import.meta.env.VITE_ENABLE_MOCK_AUTH === "true";
    if (!mockEnabled || (axios.isAxiosError(error) && error.response)) throw error;

    // Demo giúp đăng nhập khi API chưa sẵn sàng.
    const role = payload.email.startsWith("admin")
      ? "admin"
      : payload.email.startsWith("truongchi")
        ? "family_head"
        : "member";
    return {
      accessToken: `demo-token-${Date.now()}`,
      user: {
        id: `demo-${payload.email}`,
        fullName: payload.email.split("@")[0].replace(/[._-]/g, " "),
        email: payload.email,
        role,
      },
    };
  }
}

export async function register(payload) {
  const { data } = await api.post("/auth/register", payload);
  return toSession(data, payload.email);
}
