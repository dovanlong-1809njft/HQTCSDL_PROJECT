/* =====================================================================
   tests/database/test_05_ai_vector_ssms.sql
   Kịch bản kiểm thử trực tiếp trên SSMS (Không cần Docker / Không cần SQLCMD Mode)
   Hướng dẫn:
     1. Chạy .\database\init.ps1 trong Terminal VSCode để tạo sẵn DB FamilyConnect.
     2. Mở file này trong SSMS (SQL Server Management Studio) và nhấn F5 (Execute).
   ===================================================================== */

USE [FamilyConnect];
GO

-- 1. KIỂM THỬ HÀM TOÁN HỌC: heritage.fn_CosineSimilarity
SELECT
    [heritage].[fn_CosineSimilarity](N'[1, 0, 0]', N'[1, 0, 0]')     AS [GiongHetNhau_KyVong_1],
    [heritage].[fn_CosineSimilarity](N'[1, 0, 0]', N'[0.8, 0.6, 0]') AS [GanGiong_KyVong_0_8],
    [heritage].[fn_CosineSimilarity](N'[1, 0, 0]', N'[0, 1, 0]')     AS [KhongLienQuan_KyVong_0],
    [heritage].[fn_CosineSimilarity](N'json_loi',  N'[1, 0, 0]')     AS [JsonSai_AnToan_Ra_NULL];


-- 2. KIỂM THỬ STORED PROCEDURE UPSERT: heritage.usp_UpsertKnowledgeChunk
DECLARE @FamilyId UNIQUEIDENTIFIER = '22222222-2222-2222-2222-000000000001'; -- Họ Nguyễn Văn (từ 01_seed.sql)

-- Tư liệu A (về Nghề mộc)
EXEC [heritage].[usp_UpsertKnowledgeChunk]
    @FamilyId      = @FamilyId,
    @SourceType    = N'heritage',
    @SourceId      = 'EEEEEEEE-EEEE-EEEE-EEEE-000000000004',
    @ChunkIndex    = 0,
    @ChunkText     = N'Nghề mộc theo họ Nguyễn Văn từ đời cụ tổ. Cụ Cẩn học nghề năm 14 tuổi, truyền cho con cháu.',
    @EmbeddingJson = N'[0.90, 0.40, 0.10]',
    @SummaryText   = N'Lịch sử nghề mộc truyền thống 3 đời của dòng họ.';

-- Tư liệu B (về Nhà thờ họ)
EXEC [heritage].[usp_UpsertKnowledgeChunk]
    @FamilyId      = @FamilyId,
    @SourceType    = N'heritage',
    @SourceId      = 'EEEEEEEE-EEEE-EEEE-EEEE-000000000003',
    @ChunkIndex    = 0,
    @ChunkText     = N'Năm 1975 cụ Cẩn trở về làng, góp gỗ dựng lại nhà thờ họ trên nền cũ, năm 1977 xong phần mái.',
    @EmbeddingJson = N'[0.20, 0.95, 0.15]',
    @SummaryText   = N'Quá trình cụ Cẩn dựng lại nhà thờ họ giai đoạn 1975-1977.';

-- Tư liệu C (về Sắc phong)
EXEC [heritage].[usp_UpsertKnowledgeChunk]
    @FamilyId      = @FamilyId,
    @SourceType    = N'heritage',
    @SourceId      = 'EEEEEEEE-EEEE-EEEE-EEEE-000000000002',
    @ChunkIndex    = 0,
    @ChunkText     = N'Sắc phong thời Nguyễn hiện đang được lưu giữ trang trọng tại nhà thờ họ.',
    @EmbeddingJson = N'[0.10, 0.20, 0.98]',
    @SummaryText   = N'Hiện vật sắc phong thời Nguyễn tại nhà thờ họ.';

-- Gọi lặp lại Tư liệu A để kiểm chứng nhánh UPDATE của lệnh MERGE (không báo lỗi trùng khóa)
EXEC [heritage].[usp_UpsertKnowledgeChunk]
    @FamilyId      = @FamilyId,
    @SourceType    = N'heritage',
    @SourceId      = 'EEEEEEEE-EEEE-EEEE-EEEE-000000000004',
    @ChunkIndex    = 0,
    @ChunkText     = N'Nghề mộc theo họ Nguyễn Văn từ đời cụ tổ. Hiện còn hai xưởng mộc ở Thạch Thất.',
    @EmbeddingJson = N'[0.92, 0.38, 0.08]';


-- 3. MÔ PHỎNG TÌM KIẾM NGỮ NGHĨA (XẾP HẠNG THEO COSINE GẦN BẰNG 1 NHẤT)
DECLARE @VectorCauHoi NVARCHAR(MAX) = N'[0.88, 0.42, 0.05]';

SELECT
    kc.[ChunkIndex],
    kc.[ChunkText],
    kc.[SummaryText],
    kc.[SyncStatus],
    ROUND([heritage].[fn_CosineSimilarity](@VectorCauHoi, kc.[EmbeddingJson]), 4) AS [DiemGiongNhau_Cosine]
FROM [heritage].[KnowledgeChunks] AS kc
WHERE kc.[FamilyId] = @FamilyId
  AND kc.[SyncStatus] = N'synced'
ORDER BY [DiemGiongNhau_Cosine] DESC;
GO
