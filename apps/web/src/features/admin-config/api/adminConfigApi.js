import { api } from "@/shared/api/client";

export async function getSiteSettings(signal) {
  const { data } = await api.get("/settings", { signal });
  return data;
}

export async function saveSiteSettings(payload) {
  const { data } = await api.put("/admin/site-settings", payload);
  return data;
}

export async function getConfigs(params, signal) {
  const { data } = await api.get("/admin/configs", { params, signal });
  return data;
}

export async function deleteConfig(key) {
  await api.delete(`/admin/configs/${encodeURIComponent(key)}`);
}
