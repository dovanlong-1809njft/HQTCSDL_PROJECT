import { api } from "@/shared/api/client";

export async function getStatistics(signal) {
  const { data } = await api.get("/admin/statistics", { signal });
  return data;
}
