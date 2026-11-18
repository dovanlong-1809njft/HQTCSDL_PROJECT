import json
import re
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from google import genai
from google.genai import types
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
import time

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_CHAT_MODEL,
    GEMINI_EMBEDDING_DIM,
    GEMINI_EMBEDDING_MODEL,
)
from app.core.family_access import require_family_access
from app.domains.ai_assistant.repository import (
    clear_stale_knowledge_chunks,
    compute_cosine_similarity,
    find_relationship_path,
    get_source_document,
    get_source_family,
    list_pending_knowledge_sources,
    recommend_related_family_members,
    save_ai_chat_message,
    semantic_search_chunks,
    update_source_summary_in_chunks,
    upsert_knowledge_chunk,
)
from app.domains.ai_assistant.schemas import (
    ChunkAndIndexRequest,
    ChunkAndIndexResponse,
    CosineTestRequest,
    CosineTestResponse,
    EmbeddingTestResponse,
    IndexedChunkItem,
    RecommendationRequest,
    RecommendationResponse,
    RecommendedMemberItem,
    RelationshipExplainRequest,
    RelationshipExplainResponse,
    RelationshipPathData,
    SemanticSearchHit,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SummarizeRequest,
    SummarizeResponse,
    SyncedSourceSummary,
    SyncPendingRequest,
    SyncPendingResponse,
    UpsertChunkRequest,
    UpsertChunkResponse,
)
from app.domains.identity.models import User

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def get_gemini_client() -> genai.Client:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "replace_with_your_gemini_api_key":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chưa cấu hình GEMINI_API_KEY trong file .env.",
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def load_prompt_template(template_name: str) -> str:
    """Đọc nội dung file Prompt Template từ thư mục domains/ai_assistant/prompts/."""
    prompt_path = PROMPTS_DIR / template_name
    if not prompt_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không tìm thấy file Prompt Template: {template_name}",
        )
    return prompt_path.read_text(encoding="utf-8")


def split_text_into_sentence_chunks(
    text_content: str,
    *,
    sentences_per_chunk: int = 3,
    max_chars: int = 1200,
    title: str | None = None,
) -> list[str]:
    """
    Pipeline Cắt đoạn (Chunking):
    Tách văn bản dài từ bài viết (community.Posts) hoặc tư liệu di sản (heritage.Items)
    thành các đoạn ngắn khoảng 3-4 câu (tối đa max_chars ký tự mỗi đoạn).
    """
    cleaned = re.sub(r"\s+", " ", (text_content or "").strip())
    if not cleaned:
        return []

    raw_sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?…;])\s+|\n+", cleaned)
        if s and s.strip()
    ]
    if not raw_sentences:
        raw_sentences = [cleaned]

    chunks: list[str] = []
    current_group: list[str] = []
    current_len = 0
    prefix = f"[{title.strip()}] " if title and title.strip() else ""

    for sentence in raw_sentences:
        sentence_len = len(sentence)
        would_exceed_chars = (
            current_group and (current_len + 1 + sentence_len + len(prefix) > max_chars)
        )
        would_exceed_sentences = len(current_group) >= sentences_per_chunk

        if would_exceed_chars or would_exceed_sentences:
            body = " ".join(current_group).strip()
            chunk_str = f"{prefix}{body}" if prefix and not body.startswith(title.strip()) else body
            chunks.append(chunk_str[:2000])
            current_group = [sentence]
            current_len = sentence_len
        else:
            current_group.append(sentence)
            current_len += (1 if current_len > 0 else 0) + sentence_len

    if current_group:
        body = " ".join(current_group).strip()
        chunk_str = f"{prefix}{body}" if prefix and not body.startswith(title.strip()) else body
        chunks.append(chunk_str[:2000])

    return chunks


def generate_embedding(text_content: str) -> list[float]:
    """Gọi Google Gemini API để chuyển 1 đoạn văn bản thành Vector."""
    vectors = generate_embeddings_batch([text_content.strip()])
    return vectors[0]


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Gửi toàn bộ danh sách các đoạn văn bản trong 1 lần gọi API duy nhất để tiết kiệm RPM."""
    if not texts:
        return []
    client = get_gemini_client()
    cleaned_texts = [t.strip() for t in texts if t and t.strip()]
    try:
        response = client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=cleaned_texts,
            config=types.EmbedContentConfig(
                output_dimensionality=GEMINI_EMBEDDING_DIM,
            ),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Lỗi khi gọi Gemini Embedding API: {exc}",
        ) from exc

    if not response.embeddings or len(response.embeddings) != len(cleaned_texts):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini không trả về đủ dữ liệu Vector.",
        )
    return [[round(float(v), 6) for v in emb.values] for emb in response.embeddings]

def generate_gemini_answer(prompt: str, fallback_text: str | None = None) -> str:
    """
    Gọi Gemini với thinking_budget=0 (tắt suy nghĩ ngầm gây tốn token và cụt câu),
    tự động retry khi gặp lỗi 503 quá tải từ Google.
    """
    client = get_gemini_client()

    # Tắt thinking_budget để toàn bộ token dành cho câu trả lời tiếng Việt và phản hồi nhanh hơn
    try:
        gen_config = types.GenerateContentConfig(
            max_output_tokens=1024,
            temperature=0.3,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
    except Exception:
        gen_config = types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.3,
        )

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=GEMINI_CHAT_MODEL,
                contents=prompt,
                config=gen_config,
            )
            answer = (response.text or "").strip()
            if answer:
                return answer
        except Exception as exc:
            last_exc = exc
            err_msg = str(exc)
            # Nếu máy chủ Google báo 503 UNAVAILABLE (quá tải tạm thời), đợi 1.5s rồi thử lại
            if ("503" in err_msg or "UNAVAILABLE" in err_msg) and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            break

    err_str = str(last_exc) if last_exc else ""
    if any(k in err_str for k in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")):
        if fallback_text:
            return fallback_text
        return (
            "Máy chủ Google Gemini hiện đang quá tải tạm thời (503/429). "
            "Tuy nhiên dữ liệu truy xuất từ SQL Server ở bên dưới vẫn được đảm bảo chính xác."
        )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Lỗi khi gọi Gemini Chat API ({GEMINI_CHAT_MODEL}): {last_exc}",
    ) from last_exc


# =====================================================================
# Tuần 1 Services
# =====================================================================
def test_embedding_service(text_content: str) -> EmbeddingTestResponse:
    vector = generate_embedding(text_content)
    return EmbeddingTestResponse(
        model=GEMINI_EMBEDDING_MODEL,
        dimensions=len(vector),
        preview_first_5=vector[:5],
        embedding_json=json.dumps(vector),
    )


def test_sql_cosine_service(payload: CosineTestRequest, db: Session) -> CosineTestResponse:
    vec_a = generate_embedding(payload.text_a)
    vec_b = generate_embedding(payload.text_b)
    score = compute_cosine_similarity(db, json.dumps(vec_a), json.dumps(vec_b))
    return CosineTestResponse(
        text_a=payload.text_a,
        text_b=payload.text_b,
        dimensions=len(vec_a),
        cosine_similarity=score,
    )


def embed_and_upsert_chunk_service(
    payload: UpsertChunkRequest,
    actor: User | None,
    db: Session,
) -> UpsertChunkResponse:
    if actor is not None:
        require_family_access(db, actor, payload.family_id, manage=True)
        source_family = get_source_family(db, payload.source_type, payload.source_id)
        if source_family is None:
            raise HTTPException(404, "Không tìm thấy dữ liệu nguồn để lập chỉ mục.")
        if str(source_family).lower() != str(payload.family_id).lower():
            raise HTTPException(403, "Dữ liệu nguồn không thuộc gia đình đã chọn.")
    vector = generate_embedding(payload.chunk_text)
    saved = upsert_knowledge_chunk(
        db,
        family_id=payload.family_id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        chunk_index=payload.chunk_index,
        chunk_text=payload.chunk_text,
        embedding_json=json.dumps(vector),
        summary_text=payload.summary_text,
    )
    return UpsertChunkResponse(
        chunk_id=UUID(saved["chunk_id"]),
        action_taken=saved["action_taken"],
        dimensions=len(vector),
    )


# =====================================================================
# Tuần 2 Services (Đã vá RBAC + Cô lập FamilyId)
# =====================================================================
def chunk_and_index_source_service(
    payload: ChunkAndIndexRequest,
    db: Session,
    actor: User | None = None,
) -> ChunkAndIndexResponse:
    if actor is not None:
        require_family_access(db, actor, payload.family_id, manage=True)
        source_family = get_source_family(db, payload.source_type, payload.source_id)
        if source_family is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dữ liệu nguồn để lập chỉ mục.")
        if str(source_family).lower() != str(payload.family_id).lower():
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Dữ liệu nguồn không thuộc gia đình đã chọn.")

    chunks = split_text_into_sentence_chunks(
        payload.content,
        sentences_per_chunk=payload.sentences_per_chunk,
        title=payload.title,
    )
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nội dung văn bản không hợp lệ hoặc rỗng sau khi cắt đoạn.",
        )

    vectors = generate_embeddings_batch(chunks)
    indexed_items: list[IndexedChunkItem] = []

    for idx, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
        saved = upsert_knowledge_chunk(
            db,
            family_id=payload.family_id,
            source_type=payload.source_type,
            source_id=payload.source_id,
            chunk_index=idx,
            chunk_text=chunk_text,
            embedding_json=json.dumps(vector),
            summary_text=payload.summary_text if idx == 0 else None,
            auto_commit=False,
        )
        indexed_items.append(
            IndexedChunkItem(
                chunk_id=UUID(saved["chunk_id"]),
                chunk_index=idx,
                chunk_text=chunk_text,
                action_taken=saved["action_taken"],
                dimensions=len(vector),
            )
        )

    deleted_stale = clear_stale_knowledge_chunks(
        db,
        source_type=payload.source_type,
        source_id=payload.source_id,
        keep_chunk_count=len(chunks),
        auto_commit=True,
    )

    return ChunkAndIndexResponse(
        family_id=payload.family_id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        total_chunks=len(indexed_items),
        deleted_stale_chunks=deleted_stale,
        chunks=indexed_items,
    )


def sync_pending_knowledge_service(
    payload: SyncPendingRequest,
    db: Session,
    actor: User | None = None,
) -> SyncPendingResponse:
    if actor is not None:
        if payload.family_id is not None:
            require_family_access(db, actor, payload.family_id, manage=True)
        elif actor.role != "admin":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Chỉ quản trị viên hệ thống mới được đồng bộ toàn bộ các gia đình cùng lúc.",
            )

    pending_sources = list_pending_knowledge_sources(
        db,
        family_id=payload.family_id,
        limit=payload.limit,
    )
    summaries: list[SyncedSourceSummary] = []
    total_chunks = 0

    for src in pending_sources:
        res = chunk_and_index_source_service(
            ChunkAndIndexRequest(
                family_id=UUID(str(src["FamilyId"])),
                source_type=str(src["SourceType"]),
                source_id=UUID(str(src["SourceId"])),
                title=src.get("Title"),
                content=str(src["RawContent"]),
                sentences_per_chunk=payload.sentences_per_chunk,
            ),
            db=db,
            actor=None,
        )
        total_chunks += res.total_chunks
        summaries.append(
            SyncedSourceSummary(
                source_type=res.source_type,
                source_id=res.source_id,
                title=str(src.get("Title") or ""),
                chunks_indexed=res.total_chunks,
            )
        )

    return SyncPendingResponse(
        sources_processed=len(summaries),
        total_chunks_upserted=total_chunks,
        items=summaries,
    )


def semantic_search_service(
    payload: SemanticSearchRequest,
    db: Session,
    actor: User | None = None,
) -> SemanticSearchResponse:
    if actor is not None:
        require_family_access(db, actor, payload.family_id, manage=False)

    query_vector = generate_embedding(payload.query)
    raw_rows = semantic_search_chunks(
        db,
        family_id=payload.family_id,
        query_vector_json=json.dumps(query_vector),
        top_k=payload.top_k,
        min_score=payload.min_score,
        source_type=payload.source_type,
    )

    hits = [
        SemanticSearchHit(
            chunk_id=UUID(str(r["ChunkId"])),
            family_id=UUID(str(r["FamilyId"])),
            source_type=str(r["SourceType"]),
            source_id=UUID(str(r["SourceId"])),
            source_title=str(r.get("SourceTitle") or ""),
            chunk_index=int(r["ChunkIndex"]),
            chunk_text=str(r["ChunkText"]),
            summary_text=r.get("SummaryText"),
            similarity_score=float(r["SimilarityScore"]),
            updated_at=r.get("UpdatedAt"),
        )
        for r in raw_rows
    ]

    ai_answer: str | None = None
    prompt_used: str | None = None
    chat_message_id: UUID | None = None

    if payload.generate_answer:
        template = load_prompt_template("knowledge_assistant.txt")
        if hits:
            context_lines = [
                f"[Đoạn #{idx + 1} | Nguồn: {h.source_title} ({h.source_type}) | "
                f"Cosine Similarity: {h.similarity_score:.4f}]\n{h.chunk_text}"
                for idx, h in enumerate(hits)
            ]
            chunks_context = "\n\n".join(context_lines)
        else:
            chunks_context = "(Không tìm thấy đoạn tư liệu nào vượt ngưỡng tương đồng ngữ nghĩa trong CSDL)"

        prompt_used = template.format(
            retrieved_chunks_context=chunks_context,
            user_question=payload.query,
        )
        ai_answer = generate_gemini_answer(prompt_used)

        effective_user_id = actor.id if actor is not None else payload.user_id
        if effective_user_id is not None:
            ref_ids = json.dumps([str(h.source_id) for h in hits])
            chat_message_id = save_ai_chat_message(
                db,
                family_id=payload.family_id,
                user_id=effective_user_id,
                query_type="semantic_search",
                question=payload.query,
                answer=ai_answer,
                referenced_source_ids_json=ref_ids,
            )

    return SemanticSearchResponse(
        family_id=payload.family_id,
        query=payload.query,
        top_k=payload.top_k,
        total_matches=len(hits),
        matches=hits,
        ai_answer=ai_answer,
        prompt_used=prompt_used,
        chat_message_id=chat_message_id,
    )


def explain_relationship_service(
    payload: RelationshipExplainRequest,
    db: Session,
    actor: User | None = None,
) -> RelationshipExplainResponse:
    if actor is not None:
        require_family_access(db, actor, payload.family_id, manage=False)
        for mid in (payload.member_a_id, payload.member_b_id):
            member_family = get_source_family(db, "member", mid)
            if member_family is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Thành viên không tồn tại trong gia phả.")
            if str(member_family).lower() != str(payload.family_id).lower():
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    "Thành viên được chọn không thuộc gia đình hiện tại.",
                )

    try:
        row = find_relationship_path(
            db,
            member_a_id=payload.member_a_id,
            member_b_id=payload.member_b_id,
        )
    except DBAPIError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Một hoặc cả hai thành viên không tồn tại trong gia phả.",
        ) from exc

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy dữ liệu thành viên để tra cứu quan hệ.",
        )

    path_data = RelationshipPathData(
        member_a_id=UUID(str(row["MemberAId"])),
        member_a_name=str(row["MemberAName"]),
        member_a_birth_date=row.get("MemberABirthDate"),
        member_a_branch_name=row.get("MemberABranchName"),
        member_b_id=UUID(str(row["MemberBId"])),
        member_b_name=str(row["MemberBName"]),
        member_b_birth_date=row.get("MemberBBirthDate"),
        member_b_branch_name=row.get("MemberBBranchName"),
        relationship_category=str(row["RelationshipCategory"]),
        common_ancestor_id=UUID(str(row["CommonAncestorId"])) if row.get("CommonAncestorId") else None,
        common_ancestor_name=row.get("CommonAncestorName"),
        depth_from_ancestor_to_a=row.get("DepthFromAncestorToA"),
        depth_from_ancestor_to_b=row.get("DepthFromAncestorToB"),
        total_generation_distance=row.get("TotalGenerationDistance"),
        path_from_ancestor_to_a=str(row.get("PathFromAncestorToA") or row["MemberAName"]),
        path_from_ancestor_to_b=str(row.get("PathFromAncestorToB") or row["MemberBName"]),
        suggested_kinship=str(row["SuggestedKinship"]),
    )

    template = load_prompt_template("relationship_explanation.txt")
    user_question = (
        payload.question
        or f"Giải thích quan hệ họ hàng và cách xưng hô giữa {path_data.member_a_name} và {path_data.member_b_name}."
    )

    prompt_used = template.format(
        member_a_name=path_data.member_a_name,
        member_a_birth_date=str(path_data.member_a_birth_date or "Chưa rõ"),
        member_a_branch=str(path_data.member_a_branch_name or "Chưa phân nhánh"),
        member_b_name=path_data.member_b_name,
        member_b_birth_date=str(path_data.member_b_birth_date or "Chưa rõ"),
        member_b_branch=str(path_data.member_b_branch_name or "Chưa phân nhánh"),
        relationship_category=path_data.relationship_category,
        common_ancestor_name=str(path_data.common_ancestor_name or "Không áp dụng / Qua hôn nhân"),
        depth_a=str(path_data.depth_from_ancestor_to_a if path_data.depth_from_ancestor_to_a is not None else "N/A"),
        depth_b=str(path_data.depth_from_ancestor_to_b if path_data.depth_from_ancestor_to_b is not None else "N/A"),
        total_generation_distance=str(
            path_data.total_generation_distance if path_data.total_generation_distance is not None else "N/A"
        ),
        path_to_a=path_data.path_from_ancestor_to_a,
        path_to_b=path_data.path_from_ancestor_to_b,
        suggested_kinship=path_data.suggested_kinship,
        user_question=user_question,
    )

    sql_fallback = (
        f"Theo dữ liệu Bảng bao đóng từ SQL Server:\n"
        f"- Mối quan hệ giữa {path_data.member_a_name} và {path_data.member_b_name}: {path_data.suggested_kinship}.\n"
        f"- Tổ tiên chung gần nhất: {path_data.common_ancestor_name or 'Quan hệ qua hôn nhân'}.\n"
        f"- Đường đi phả hệ tới {path_data.member_a_name}: {path_data.path_from_ancestor_to_a}.\n"
        f"- Đường đi phả hệ tới {path_data.member_b_name}: {path_data.path_from_ancestor_to_b}."
    )
    ai_explanation = generate_gemini_answer(prompt_used, fallback_text=sql_fallback)

    chat_message_id: UUID | None = None
    effective_user_id = actor.id if actor is not None else payload.user_id
    if effective_user_id is not None:
        refs = json.dumps([str(path_data.member_a_id), str(path_data.member_b_id)])
        chat_message_id = save_ai_chat_message(
            db,
            family_id=payload.family_id,
            user_id=effective_user_id,
            query_type="kinship_explain",
            question=user_question,
            answer=ai_explanation,
            referenced_source_ids_json=refs,
        )

    return RelationshipExplainResponse(
        relationship_path=path_data,
        ai_explanation=ai_explanation,
        prompt_used=prompt_used,
        chat_message_id=chat_message_id,
    )


def summarize_content_service(
    payload: SummarizeRequest,
    db: Session,
    actor: User | None = None,
) -> SummarizeResponse:
    if actor is not None:
        require_family_access(db, actor, payload.family_id, manage=False)

    title = (payload.title or "").strip()
    content = (payload.content or "").strip()

    if not content:
        if payload.source_type and payload.source_id:
            try:
                doc = get_source_document(
                    db,
                    family_id=payload.family_id,
                    source_type=payload.source_type,
                    source_id=payload.source_id,
                )
            except DBAPIError as exc:
                db.rollback()
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "Loại nguồn tư liệu không hợp lệ.",
                ) from exc

            if doc is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    "Không tìm thấy tư liệu hoặc bài viết cần tóm tắt trong gia đình này.",
                )
            title = title or str(doc.get("Title") or "Tư liệu gia đình")
            content = str(doc.get("Content") or "").strip()
        else:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Cần cung cấp nội dung văn bản (content) hoặc mã tư liệu (source_type + source_id).",
            )

    if not content:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Tư liệu được chọn không có nội dung văn bản để tóm tắt.",
        )

    template = load_prompt_template("summarize_content.txt")
    prompt = template.format(
        title=title or "Tư liệu dòng họ",
        content=content,
        max_sentences=payload.max_sentences,
    )
    summary = generate_gemini_answer(prompt)

    updated_chunks = 0
    if payload.save_to_chunks and payload.source_type and payload.source_id:
        updated_chunks = update_source_summary_in_chunks(
            db,
            family_id=payload.family_id,
            source_type=payload.source_type,
            source_id=payload.source_id,
            summary_text=summary,
        )

    chat_message_id: UUID | None = None
    if actor is not None:
        refs = json.dumps([str(payload.source_id)]) if payload.source_id else None
        chat_message_id = save_ai_chat_message(
            db,
            family_id=payload.family_id,
            user_id=actor.id,
            query_type="summarize",
            question=f"Tóm tắt tư liệu: {title}",
            answer=summary,
            referenced_source_ids_json=refs,
        )

    return SummarizeResponse(
        family_id=payload.family_id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        title=title or "Tư liệu dòng họ",
        summary=summary,
        updated_chunks=updated_chunks,
        chat_message_id=chat_message_id,
    )


def recommend_related_service(
    payload: RecommendationRequest,
    db: Session,
    actor: User | None = None,
) -> RecommendationResponse:
    if actor is not None:
        require_family_access(db, actor, payload.family_id, manage=False)

    try:
        member_rows = recommend_related_family_members(
            db,
            family_id=payload.family_id,
            anchor_member_id=payload.member_id,
            top_k=payload.top_k,
        )
    except DBAPIError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hồ sơ thành viên trong gia đình này.",
        ) from exc

    db_synthesized_query = (
        str(member_rows[0].get("SynthesizedQuery") or "").strip()
        if member_rows
        else ""
    )
    synthesized_query = (
        payload.topic_query.strip()
        if payload.topic_query and payload.topic_query.strip()
        else db_synthesized_query or "Truyền thống lịch sử, nghề nghiệp và sự kiện dòng họ"
    )

    related_members = [
        RecommendedMemberItem(
            member_id=UUID(str(m["MemberId"])),
            full_name=str(m["FullName"]),
            birth_date=m.get("BirthDate"),
            location=m.get("Location"),
            branch_name=m.get("BranchName"),
            latest_position=m.get("LatestPosition"),
            latest_company=m.get("LatestCompany"),
            latest_institution=m.get("LatestInstitution"),
            match_reason=str(m["MatchReason"]),
        )
        for m in member_rows
    ]

    query_vector = generate_embedding(synthesized_query)
    raw_chunks = semantic_search_chunks(
        db,
        family_id=payload.family_id,
        query_vector_json=json.dumps(query_vector),
        top_k=payload.top_k,
        min_score=payload.min_score,
        source_type=None,
    )
    related_resources = [
        SemanticSearchHit(
            chunk_id=UUID(str(r["ChunkId"])),
            family_id=UUID(str(r["FamilyId"])),
            source_type=str(r["SourceType"]),
            source_id=UUID(str(r["SourceId"])),
            source_title=str(r.get("SourceTitle") or ""),
            chunk_index=int(r["ChunkIndex"]),
            chunk_text=str(r["ChunkText"]),
            summary_text=r.get("SummaryText"),
            similarity_score=float(r["SimilarityScore"]),
            updated_at=r.get("UpdatedAt"),
        )
        for r in raw_chunks
    ]

    member_names = ", ".join(m.full_name for m in related_members[:3]) or "chưa có"
    resource_titles = ", ".join(dict.fromkeys(r.source_title for r in related_resources)) or "chưa có"
    ai_note = (
        f"Kết quả từ Stored Procedure đề xuất kết nối với các thành viên ({member_names}) "
        f"và các tư liệu tương đồng ngữ nghĩa ({resource_titles})."
    )

    return RecommendationResponse(
        family_id=payload.family_id,
        anchor_member_id=payload.member_id,
        synthesized_query=synthesized_query,
        related_members=related_members,
        related_resources=related_resources,
        ai_recommendation_note=ai_note,
    )