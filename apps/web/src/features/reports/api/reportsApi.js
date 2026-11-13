import { api } from "@/shared/api/client";

export async function getReports(params, signal) {
  const { data } = await api.get("/admin/reports", { params, signal });
  return data;
}

export async function resolveReport(id, decision) {
  const { data } = await api.patch(`/admin/reports/${id}/resolve`, { decision });
  return data;
}
