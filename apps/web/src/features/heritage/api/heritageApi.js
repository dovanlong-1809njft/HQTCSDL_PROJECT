import { api } from "@/shared/api/client";

export const heritageApi = {
  families: async () => (await api.get("/heritage/families")).data,
  list: async (resource, familyId, params = {}) =>
    (await api.get(`/heritage/${resource}`, { params: { family_id: familyId, ...params } })).data,
  get: async (resource, familyId, id) =>
    (await api.get(`/heritage/${resource}/${id}`, { params: { family_id: familyId } })).data,
  create: async (resource, familyId, payload) =>
    (await api.post(`/heritage/${resource}`, payload, { params: { family_id: familyId } })).data,
  update: async (resource, familyId, id, payload) =>
    (await api.patch(`/heritage/${resource}/${id}`, payload, { params: { family_id: familyId } })).data,
  remove: async (resource, familyId, row) =>
    api.delete(`/heritage/${resource}/${row.id}`, { params: { family_id: familyId, expected_version: row.version_token } }),
  tree: async (familyId) => (await api.get("/heritage/family-tree", { params: { family_id: familyId } })).data,
};
