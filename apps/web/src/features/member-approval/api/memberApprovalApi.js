import { api } from "@/shared/api/client";

export async function getPendingVerifications(params, signal) {
  const { data } = await api.get("/admin/verifications/pending", { params, signal });
  return data;
}

export async function reviewVerification(id, decision) {
  const { data } = await api.patch(`/admin/verifications/${id}/review`, { decision });
  return data;
}
