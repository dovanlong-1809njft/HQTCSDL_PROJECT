import { api } from "@/shared/api/client";

// Lấy danh sách gia đình và thành viên để hiển thị vào ô chọn (Dropdown)
export async function getAccessibleFamilies(signal) {
  const { data } = await api.get("/heritage/families", { signal });
  return data;
}

export async function getFamilyMembers(familyId, signal) {
  const { data } = await api.get("/heritage/members", {
    params: { family_id: familyId, page: 1, page_size: 100 },
    signal,
  });
  return data?.items || [];
}

export async function getHeritageItems(familyId, signal) {
  const { data } = await api.get("/heritage/items", {
    params: { family_id: familyId, page: 1, page_size: 50 },
    signal,
  });
  return data?.items || [];
}

// 1. Đồng bộ Vector cho các bài viết/di sản đang chờ (Pending)
export async function syncPendingKnowledge(payload) {
  const { data } = await api.post("/ai/sync-pending", payload);
  return data;
}

// 2. Tìm kiếm ngữ nghĩa & Trợ lý tri thức RAG
export async function semanticSearch(payload) {
  const { data } = await api.post("/ai/semantic-search", payload);
  return data;
}

// 3. Giải thích mối quan hệ gia phả & cách xưng hô
export async function explainRelationship(payload) {
  const { data } = await api.post("/ai/explain-relationship", payload);
  return data;
}

// 4. Tóm tắt nội dung tư liệu di sản / bài viết bằng AI
export async function summarizeContent(payload) {
  const { data } = await api.post("/ai/summarize", payload);
  return data;
}

// 5. AI Đề xuất thành viên & tài nguyên di sản liên quan
export async function getRecommendations(payload) {
  const { data } = await api.post("/ai/recommendations", payload);
  return data;
}
