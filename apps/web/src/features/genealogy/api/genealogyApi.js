import { api } from "@/shared/api/client";

export const genealogyApi = {
  branches: async (familyId) => {
    const items=[];let batch;
    for(let page=1;!batch || items.length<batch.total;page++){
      batch=await genealogyApi.list("branches",familyId,{page,page_size:200});
      items.push(...batch.items);
      if(!batch.items.length)break;
    }
    return {items};
  },
  profile: async () => (await api.get("/genealogy/me")).data,
  saveProfile: async (payload) => (await api.put("/genealogy/me", payload)).data,
  candidates: async (params) => (await api.get("/genealogy/verification-candidates", { params })).data,
  verify: async (memberId) => (await api.post("/genealogy/verifications", { member_id: memberId })).data,
  list: async (resource, familyId, params = {}) => (await api.get(`/genealogy/${resource}`, { params: { family_id: familyId, ...params } })).data,
  save: async (resource, familyId, id, payload) => {
    const path = resource === "families" && id ? `/genealogy/families/${familyId}` : `/genealogy/${resource}${id ? `/${id}` : ""}`;
    return (await api[id ? "put" : "post"](path, payload, { params: { family_id: familyId } })).data;
  },
  remove: async (resource, familyId, id) => api.delete(`/genealogy/${resource}/${id}`, { params: { family_id: familyId } }),
  relations: async (familyId, memberId) => (await api.get("/genealogy/relationships", { params: { family_id: familyId, member_id: memberId || undefined } })).data,
  addRelation: async (familyId, kind, payload) => (await api.post(`/genealogy/relationships/${kind}`, payload, { params: { family_id: familyId } })).data,
  removeRelation: async (familyId, kind, id) => api.delete(`/genealogy/relationships/${kind}/${id}`, { params: { family_id: familyId } }),
};
