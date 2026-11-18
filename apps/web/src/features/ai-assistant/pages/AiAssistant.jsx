import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { getApiErrorMessage } from "@/shared/api/client";
import {
  explainRelationship,
  getAccessibleFamilies,
  getFamilyMembers,
  getHeritageItems,
  getRecommendations,
  semanticSearch,
  summarizeContent,
  syncPendingKnowledge,
} from "../api/aiAssistantApi";

const TABS = [
  { id: "search", label: "Trợ lý Tri thức & Tìm kiếm" },
  { id: "kinship", label: "Giải thích Quan hệ" },
  { id: "summarize", label: "Tóm tắt Nội dung" },
  { id: "recommend", label: "Đề xuất Liên quan" },
];

export function AiAssistant() {
  const { user } = useAuth();
  const isManager = user?.role === "admin" || user?.role === "family_head";

  const [activeTab, setActiveTab] = useState("search");
  const [familyId, setFamilyId] = useState("");

  // States cho Tab 1: Tìm kiếm ngữ nghĩa
  const [queryText, setQueryText] = useState(
    "Dòng họ Nguyễn Văn có nghề truyền thống gì và nhà thờ họ được dựng năm nào?"
  );
  const [topK, setTopK] = useState(3);

  // States cho Tab 2: Giải thích quan hệ
  const [memberAId, setMemberAId] = useState("");
  const [memberBId, setMemberBId] = useState("");
  const [kinshipQuestion, setKinshipQuestion] = useState("");

  // States cho Tab 3: Tóm tắt nội dung
  const [selectedItemId, setSelectedItemId] = useState("");
  const [customTitle, setCustomTitle] = useState("");
  const [customContent, setCustomContent] = useState("");
  const [maxSentences, setMaxSentences] = useState(3);

  // States cho Tab 4: Đề xuất
  const [anchorMemberId, setAnchorMemberId] = useState("");
  const [topicQuery, setTopicQuery] = useState("");

  // Tải danh sách gia đình
  const familiesQuery = useQuery({
    queryKey: ["ai-families"],
    queryFn: ({ signal }) => getAccessibleFamilies(signal),
  });

  useEffect(() => {
    if (!familyId && familiesQuery.data?.length > 0) {
      setFamilyId(familiesQuery.data[0].id);
    }
  }, [familiesQuery.data, familyId]);

  // Tải danh sách thành viên trong gia đình đang chọn
  const membersQuery = useQuery({
    queryKey: ["ai-members", familyId],
    queryFn: ({ signal }) => getFamilyMembers(familyId, signal),
    enabled: Boolean(familyId),
  });

  useEffect(() => {
    const list = membersQuery.data || [];
    if (list.length > 0) {
      if (!memberAId) setMemberAId(list[0].id);
      if (!memberBId) setMemberBId(list[list.length > 1 ? 1 : 0].id);
      if (!anchorMemberId) setAnchorMemberId(list[0].id);
    }
  }, [membersQuery.data, memberAId, memberBId, anchorMemberId]);

  // Tải danh sách tư liệu di sản trong gia đình đang chọn
  const itemsQuery = useQuery({
    queryKey: ["ai-heritage-items", familyId],
    queryFn: ({ signal }) => getHeritageItems(familyId, signal),
    enabled: Boolean(familyId),
  });

  useEffect(() => {
    const items = itemsQuery.data || [];
    if (items.length > 0 && !selectedItemId) {
      setSelectedItemId(items[0].id);
    }
  }, [itemsQuery.data, selectedItemId]);

  // Mutations gọi API AI
  const syncMutation = useMutation({
    mutationFn: () =>
      syncPendingKnowledge({ family_id: familyId, sentences_per_chunk: 3, limit: 20 }),
  });

  const searchMutation = useMutation({
    mutationFn: (e) => {
      e.preventDefault();
      return semanticSearch({
        family_id: familyId,
        query: queryText,
        top_k: Number(topK),
        min_score: 0.25,
        generate_answer: true,
      });
    },
  });

  const kinshipMutation = useMutation({
    mutationFn: (e) => {
      e.preventDefault();
      return explainRelationship({
        family_id: familyId,
        member_a_id: memberAId,
        member_b_id: memberBId,
        question: kinshipQuestion.trim() || undefined,
      });
    },
  });

  const summarizeMutation = useMutation({
    mutationFn: (e) => {
      e.preventDefault();
      return summarizeContent({
        family_id: familyId,
        source_type: selectedItemId ? "heritage" : null,
        source_id: selectedItemId || null,
        title: customTitle.trim() || null,
        content: customContent.trim() || null,
        max_sentences: Number(maxSentences),
        save_to_chunks: true,
      });
    },
  });

  const recommendMutation = useMutation({
    mutationFn: (e) => {
      e.preventDefault();
      return getRecommendations({
        family_id: familyId,
        member_id: anchorMemberId || null,
        topic_query: topicQuery.trim() || null,
        top_k: 4,
        min_score: 0.2,
      });
    },
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Trợ lý AI Dòng họ (Gemini RAG)
          </h1>
          <p className="text-sm text-slate-600">
            Tìm kiếm ngữ nghĩa, giải thích vai vế gia phả, tóm tắt di sản và đề xuất kết nối
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-slate-700">Gia đình:</label>
          <select
            value={familyId}
            onChange={(e) => {
              setFamilyId(e.target.value);
              setMemberAId("");
              setMemberBId("");
              setAnchorMemberId("");
              setSelectedItemId("");
            }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            {(familiesQuery.data || []).map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>

          {isManager && (
            <button
              type="button"
              onClick={() => syncMutation.mutate()}
              disabled={!familyId || syncMutation.isPending}
              className="rounded-lg bg-emerald-700 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
            >
              {syncMutation.isPending ? "Đang lập chỉ mục..." : "Đồng bộ Vector AI"}
            </button>
          )}
        </div>
      </div>

      {syncMutation.isSuccess && (
        <div className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">
          Đã đồng bộ {syncMutation.data.sources_processed} tư liệu/bài viết (
          {syncMutation.data.total_chunks_upserted} đoạn Vector).
        </div>
      )}
      {syncMutation.isError && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {getApiErrorMessage(syncMutation.error)}
        </div>
      )}

      {/* Thanh chuyển Tab */}
      <div className="flex flex-wrap gap-2 border-b pb-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setActiveTab(t.id)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              activeTab === t.id
                ? "bg-slate-900 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* TAB 1: TÌM KIẾM NGỮ NGHĨA & HỎI ĐÁP RAG */}
      {activeTab === "search" && (
        <section className="space-y-4 rounded-xl border bg-white p-5 shadow-sm">
          <form onSubmit={(e) => searchMutation.mutate(e)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Câu hỏi về lịch sử, di sản hoặc tin tức dòng họ
              </label>
              <textarea
                rows={3}
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 p-3 text-sm"
                placeholder="Nhập câu hỏi bằng tiếng Việt tự nhiên..."
                required
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm">
                <span>Số đoạn trích xuất (Top-K):</span>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={topK}
                  onChange={(e) => setTopK(e.target.value)}
                  className="w-20 rounded border px-2 py-1"
                />
              </div>
              <button
                type="submit"
                disabled={!familyId || searchMutation.isPending}
                className="rounded-lg bg-slate-900 px-5 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {searchMutation.isPending ? "AI đang suy nghĩ..." : "Hỏi Trợ lý AI"}
              </button>
            </div>
          </form>

          {searchMutation.isError && (
            <p className="text-sm text-red-600">{getApiErrorMessage(searchMutation.error)}</p>
          )}

          {searchMutation.data && (
            <div className="space-y-4 border-t pt-4">
              {searchMutation.data.ai_answer && (
                <div className="rounded-lg bg-amber-50/70 border border-amber-200 p-4">
                  <h3 className="font-semibold text-slate-900">Câu trả lời từ Trợ lý AI:</h3>
                  <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-slate-800">
                    {searchMutation.data.ai_answer}
                  </p>
                </div>
              )}

              <div>
                <h4 className="text-sm font-semibold text-slate-700">
                  Các đoạn tư liệu khớp ngữ nghĩa trong CSDL ({searchMutation.data.total_matches}):
                </h4>
                <div className="mt-2 grid gap-3">
                  {searchMutation.data.matches.map((hit) => (
                    <div key={hit.chunk_id} className="rounded-lg border p-3 text-sm">
                      <div className="flex justify-between font-medium text-slate-900">
                        <span>
                          [{hit.source_type}] {hit.source_title} (Đoạn #{hit.chunk_index})
                        </span>
                        <span className="text-emerald-700">
                          Cosine: {(hit.similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <p className="mt-1 text-slate-600">{hit.chunk_text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {/* TAB 2: GIẢI THÍCH MỐI QUAN HỆ GIA PHẢ */}
      {activeTab === "kinship" && (
        <section className="space-y-4 rounded-xl border bg-white p-5 shadow-sm">
          <form onSubmit={(e) => kinshipMutation.mutate(e)} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Thành viên thứ nhất (A)
                </label>
                <select
                  value={memberAId}
                  onChange={(e) => setMemberAId(e.target.value)}
                  className="mt-1 w-full rounded-lg border p-2.5 text-sm"
                  required
                >
                  {(membersQuery.data || []).map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.full_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Thành viên thứ hai (B)
                </label>
                <select
                  value={memberBId}
                  onChange={(e) => setMemberBId(e.target.value)}
                  className="mt-1 w-full rounded-lg border p-2.5 text-sm"
                  required
                >
                  {(membersQuery.data || []).map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.full_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">
                Câu hỏi bổ sung (tùy chọn)
              </label>
              <input
                type="text"
                value={kinshipQuestion}
                onChange={(e) => setKinshipQuestion(e.target.value)}
                placeholder="Ví dụ: Trong dịp lễ giỗ tổ, hai người xưng hô thế nào cho đúng vai vế?"
                className="mt-1 w-full rounded-lg border p-2.5 text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={!memberAId || !memberBId || kinshipMutation.isPending}
              className="rounded-lg bg-slate-900 px-5 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {kinshipMutation.isPending
                ? "Đang tra cứu Bảng bao đóng & gọi AI..."
                : "Giải thích Quan hệ & Cách xưng hô"}
            </button>
          </form>

          {kinshipMutation.isError && (
            <p className="text-sm text-red-600">{getApiErrorMessage(kinshipMutation.error)}</p>
          )}

          {kinshipMutation.data && (
            <div className="space-y-4 border-t pt-4 text-sm">
              <div className="rounded-lg bg-slate-50 p-3">
                <p>
                  <strong>Tổ tiên chung gần nhất (LCA):</strong>{" "}
                  {kinshipMutation.data.relationship_path.common_ancestor_name || "Qua hôn nhân"}
                </p>
                <p>
                  <strong>Đường đi tới A:</strong>{" "}
                  {kinshipMutation.data.relationship_path.path_from_ancestor_to_a}
                </p>
                <p>
                  <strong>Đường đi tới B:</strong>{" "}
                  {kinshipMutation.data.relationship_path.path_from_ancestor_to_b}
                </p>
                <p>
                  <strong>Gợi ý từ SQL Server:</strong>{" "}
                  {kinshipMutation.data.relationship_path.suggested_kinship}
                </p>
              </div>

              <div className="rounded-lg border border-emerald-200 bg-emerald-50/60 p-4">
                <h3 className="font-semibold text-slate-900">Lời giải thích từ AI:</h3>
                <p className="mt-2 whitespace-pre-line leading-relaxed text-slate-800">
                  {kinshipMutation.data.ai_explanation}
                </p>
              </div>
            </div>
          )}
        </section>
      )}

      {/* TAB 3: TÓM TẮT NỘI DUNG BẰNG AI */}
      {activeTab === "summarize" && (
        <section className="space-y-4 rounded-xl border bg-white p-5 shadow-sm">
          <form onSubmit={(e) => summarizeMutation.mutate(e)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Chọn tư liệu di sản có sẵn trong CSDL
              </label>
              <select
                value={selectedItemId}
                onChange={(e) => setSelectedItemId(e.target.value)}
                className="mt-1 w-full rounded-lg border p-2.5 text-sm"
              >
                <option value="">-- Hoặc tự nhập văn bản bên dưới --</option>
                {(itemsQuery.data || [])
                  .filter((it) => it.type !== "photo")
                  .map((it) => (
                    <option key={it.id} value={it.id}>
                      [{it.type}] {it.title}
                    </option>
                  ))}
              </select>
            </div>

            {!selectedItemId && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Tiêu đề</label>
                  <input
                    type="text"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                    className="mt-1 w-full rounded-lg border p-2.5 text-sm"
                    placeholder="Nhập tiêu đề văn bản..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">
                    Nội dung cần tóm tắt
                  </label>
                  <textarea
                    rows={4}
                    value={customContent}
                    onChange={(e) => setCustomContent(e.target.value)}
                    className="mt-1 w-full rounded-lg border p-2.5 text-sm"
                    placeholder="Dán nội dung câu chuyện hoặc tài liệu dài vào đây..."
                  />
                </div>
              </>
            )}

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm">
                <span>Độ dài đoạn tóm tắt (số câu):</span>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={maxSentences}
                  onChange={(e) => setMaxSentences(e.target.value)}
                  className="w-20 rounded border px-2 py-1"
                />
              </div>
              <button
                type="submit"
                disabled={summarizeMutation.isPending}
                className="rounded-lg bg-slate-900 px-5 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {summarizeMutation.isPending ? "Đang tóm tắt..." : "Tóm tắt bằng AI"}
              </button>
            </div>
          </form>

          {summarizeMutation.isError && (
            <p className="text-sm text-red-600">{getApiErrorMessage(summarizeMutation.error)}</p>
          )}

          {summarizeMutation.data && (
            <div className="rounded-lg border bg-slate-50 p-4 text-sm">
              <h3 className="font-semibold text-slate-900">
                Bản tóm tắt: {summarizeMutation.data.title}
              </h3>
              <p className="mt-2 whitespace-pre-line leading-relaxed text-slate-800">
                {summarizeMutation.data.summary}
              </p>
              <p className="mt-2 text-xs text-slate-500">
                Đã cập nhật vào {summarizeMutation.data.updated_chunks} bản ghi KnowledgeChunks.
              </p>
            </div>
          )}
        </section>
      )}

      {/* TAB 4: AI ĐỀ XUẤT THÀNH VIÊN & TÀI NGUYÊN LIÊN QUAN */}
      {activeTab === "recommend" && (
        <section className="space-y-4 rounded-xl border bg-white p-5 shadow-sm">
          <form onSubmit={(e) => recommendMutation.mutate(e)} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Chọn thành viên làm mốc gợi ý
                </label>
                <select
                  value={anchorMemberId}
                  onChange={(e) => setAnchorMemberId(e.target.value)}
                  className="mt-1 w-full rounded-lg border p-2.5 text-sm"
                >
                  <option value="">-- Không chọn (Gợi ý theo chủ đề) --</option>
                  {(membersQuery.data || []).map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.full_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Từ khóa / Chủ đề quan tâm (tùy chọn)
                </label>
                <input
                  type="text"
                  value={topicQuery}
                  onChange={(e) => setTopicQuery(e.target.value)}
                  placeholder="Để trống sẽ tự động tổng hợp từ nghề nghiệp & chi họ..."
                  className="mt-1 w-full rounded-lg border p-2.5 text-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={!familyId || recommendMutation.isPending}
              className="rounded-lg bg-slate-900 px-5 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {recommendMutation.isPending ? "Đang phân tích đề xuất..." : "Lấy Đề xuất từ AI"}
            </button>
          </form>

          {recommendMutation.isError && (
            <p className="text-sm text-red-600">{getApiErrorMessage(recommendMutation.error)}</p>
          )}

          {recommendMutation.data && (
            <div className="space-y-4 border-t pt-4 text-sm">
              <div className="rounded-lg bg-blue-50 p-3 text-blue-900">
                <p>
                  <strong>Ngữ cảnh tổng hợp từ SQL:</strong>{" "}
                  {recommendMutation.data.synthesized_query}
                </p>
                {recommendMutation.data.ai_recommendation_note && (
                  <p className="mt-1">{recommendMutation.data.ai_recommendation_note}</p>
                )}
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-semibold text-slate-900">
                    Thành viên liên quan ({recommendMutation.data.related_members.length})
                  </h4>
                  <div className="mt-2 space-y-2">
                    {recommendMutation.data.related_members.map((m) => (
                      <div key={m.member_id} className="rounded-lg border p-3">
                        <div className="font-semibold text-slate-900">{m.full_name}</div>
                        <div className="text-xs text-emerald-700">{m.match_reason}</div>
                        <div className="mt-1 text-xs text-slate-600">
                          {[m.branch_name, m.latest_position, m.latest_company, m.location]
                            .filter(Boolean)
                            .join(" · ")}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-slate-900">
                    Tư liệu & Bài viết liên quan ({recommendMutation.data.related_resources.length})
                  </h4>
                  <div className="mt-2 space-y-2">
                    {recommendMutation.data.related_resources.map((r) => (
                      <div key={r.chunk_id} className="rounded-lg border p-3">
                        <div className="flex justify-between font-semibold text-slate-900">
                          <span>{r.source_title}</span>
                          <span className="text-xs text-emerald-700">
                            {(r.similarity_score * 100).toFixed(1)}%
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-slate-600">{r.chunk_text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}