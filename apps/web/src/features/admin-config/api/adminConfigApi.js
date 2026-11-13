import { api } from "@/shared/api/client";

export async function getConfigs(params, signal) {
  const { data } = await api.get("/admin/configs", { params, signal });
  return data;
}

export async function createConfig(payload) {
  const { data } = await api.post("/admin/configs", payload);
  return data;
}

export async function updateConfig(key, payload) {
  const { data } = await api.put(`/admin/configs/${encodeURIComponent(key)}`, payload);
  return data;
}

export async function deleteConfig(key) {
  await api.delete(`/admin/configs/${encodeURIComponent(key)}`);
}
