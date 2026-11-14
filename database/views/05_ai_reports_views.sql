USE [$(DB_NAME)];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

/* =====================================================================
   1. Function: heritage.fn_CosineSimilarity
   Tính độ tương đồng Cosine giữa 2 mảng Vector lưu ở dạng chuỗi JSON
   (ví dụ: '[0.12, -0.34, 0.56]') bằng hàm chuẩn OPENJSON.
   Giá trị trả về nằm trong khoảng [-1.0, 1.0] (1.0 là giống hệt nhau).
   ===================================================================== */
CREATE OR ALTER FUNCTION [heritage].[fn_CosineSimilarity]
(
    @VecAJson NVARCHAR(MAX),
    @VecBJson NVARCHAR(MAX)
)
RETURNS FLOAT
AS
BEGIN
    IF @VecAJson IS NULL OR @VecBJson IS NULL
       OR ISJSON(@VecAJson) <> 1 OR ISJSON(@VecBJson) <> 1
    BEGIN
        RETURN NULL;
    END;

    DECLARE @Similarity FLOAT;

    SELECT @Similarity =
        SUM(TRY_CAST(a.[value] AS FLOAT) * TRY_CAST(b.[value] AS FLOAT))
        / NULLIF(
            SQRT(SUM(POWER(TRY_CAST(a.[value] AS FLOAT), 2)))
            * SQRT(SUM(POWER(TRY_CAST(b.[value] AS FLOAT), 2))),
            0.0
          )
    FROM OPENJSON(@VecAJson) AS a
    INNER JOIN OPENJSON(@VecBJson) AS b
        ON a.[key] = b.[key];

    RETURN @Similarity;
END;
GO

/* =====================================================================
   2. Function: genealogy.fn_SuggestVietnameseKinship
   Gợi ý danh xưng và cách xưng hô họ hàng truyền thống Việt Nam dựa trên
   khoảng cách thế hệ từ Tổ tiên chung gần nhất (LCA) đến Thành viên A
   (@DepthA) và Thành viên B (@DepthB).
   ===================================================================== */
CREATE OR ALTER FUNCTION [genealogy].[fn_SuggestVietnameseKinship]
(
    @DepthA INT,
    @DepthB INT
)
RETURNS NVARCHAR(300)
AS
BEGIN
    IF @DepthA IS NULL OR @DepthB IS NULL OR @DepthA < 0 OR @DepthB < 0
        RETURN N'Chưa xác định được khoảng cách thế hệ';

    IF @DepthA = 0 AND @DepthB = 0
        RETURN N'Cùng một người (chính bản thân)';

    -- Quan hệ trực hệ (một người là tổ tiên trực tiếp của người kia)
    IF @DepthA = 0
    BEGIN
        RETURN CASE @DepthB
            WHEN 1 THEN N'Trực hệ: A là Cha/Mẹ ruột của B (B gọi A là Bố/Cha/Mẹ, xưng Con)'
            WHEN 2 THEN N'Trực hệ: A là Ông/Bà (nội/ngoại) của B (B gọi A là Ông/Bà, xưng Cháu)'
            WHEN 3 THEN N'Trực hệ: A là Cụ (Cố) của B (B gọi A là Cụ/Cố, xưng Chắt)'
            WHEN 4 THEN N'Trực hệ: A là Kỵ (Sơ) của B (B gọi A là Kỵ/Sơ, xưng Chút)'
            ELSE CONCAT(N'Trực hệ: A là tổ tiên đời thứ ', @DepthB, N' tính từ B')
        END;
    END;

    IF @DepthB = 0
    BEGIN
        RETURN CASE @DepthA
            WHEN 1 THEN N'Trực hệ: A là Con ruột của B (A gọi B là Bố/Cha/Mẹ, xưng Con)'
            WHEN 2 THEN N'Trực hệ: A là Cháu (nội/ngoại) của B (A gọi B là Ông/Bà, xưng Cháu)'
            WHEN 3 THEN N'Trực hệ: A là Chắt của B (A gọi B là Cụ/Cố, xưng Chắt)'
            WHEN 4 THEN N'Trực hệ: A là Chút của B (A gọi B là Kỵ/Sơ, xưng Chút)'
            ELSE CONCAT(N'Trực hệ: A là hậu duệ cách B ', @DepthA, N' đời')
        END;
    END;

    -- Quan hệ ngang hàng hoặc bàng hệ (cùng tổ tiên chung)
    IF @DepthA = 1 AND @DepthB = 1
        RETURN N'Ngang hàng: Anh/Chị/Em ruột (cùng cha hoặc mẹ)';

    IF @DepthA = 1 AND @DepthB = 2
        RETURN N'Bàng hệ: A là Bác/Chú/Cô/Cậu/Dì ruột của B (A ngang hàng cha/mẹ của B, B xưng Cháu)';

    IF @DepthA = 2 AND @DepthB = 1
        RETURN N'Bàng hệ: A là Cháu ruột của B (B là Bác/Chú/Cô/Cậu/Dì ruột, ngang hàng cha/mẹ của A)';

    IF @DepthA = 1 AND @DepthB = 3
        RETURN N'Bàng hệ: A là Ông/Bà trẻ (Bác/Chú/Cô/Cậu/Dì của cha/mẹ B), B là Cháu/Chắt họ';

    IF @DepthA = 3 AND @DepthB = 1
        RETURN N'Bàng hệ: A là Cháu/Chắt họ, B là Ông/Bà trẻ (ngang hàng ông/bà của A)';

    IF @DepthA = 2 AND @DepthB = 2
        RETURN N'Ngang hàng bàng hệ: Anh/Chị/Em họ (con chú con bác / con cô con cậu / con dì)';

    IF @DepthA = 2 AND @DepthB = 3
        RETURN N'Bàng hệ: A thuộc hàng Chú/Bác/Cô/Cậu/Dì họ của B (cùng cụ tổ, lệch 1 đời)';

    IF @DepthA = 3 AND @DepthB = 2
        RETURN N'Bàng hệ: A là Cháu họ của B (B thuộc hàng Chú/Bác/Cô/Cậu/Dì họ của A, cùng cụ tổ)';

    IF @DepthA = 3 AND @DepthB = 3
        RETURN N'Ngang hàng bàng hệ: Anh/Chị/Em họ đời thứ 3 (cùng cụ tổ, cháu chú cháu bác)';

    IF @DepthA = @DepthB
        RETURN CONCAT(N'Ngang hàng bàng hệ: Anh/Chị/Em họ (cùng tổ tiên cách ', @DepthA, N' đời)');

    RETURN CONCAT(
        N'Họ hàng bàng hệ: A cách tổ tiên chung ', @DepthA,
        N' đời, B cách tổ tiên chung ', @DepthB, N' đời'
    );
END;
GO

/* =====================================================================
   3. View: heritage.vw_PendingKnowledgeSources
   Liệt kê các Bài viết (community.Posts) và Tư liệu di sản (heritage.Items)
   có nội dung văn bản nhưng chưa được cắt đoạn/nhúng Vector hoặc đang ở
   trạng thái 'pending' / 'failed' cần Pipeline AI đồng bộ.
   ===================================================================== */
CREATE OR ALTER VIEW [heritage].[vw_PendingKnowledgeSources]
AS
    -- Nguồn 1: Bài viết cộng đồng (community.Posts) của Thành viên 3
    SELECT
        p.[FamilyId]                                     AS [FamilyId],
        CAST(N'post' AS NVARCHAR(20))                    AS [SourceType],
        p.[Id]                                           AS [SourceId],
        CONCAT(N'Bài viết cộng đồng #', LEFT(CONVERT(NVARCHAR(36), p.[Id]), 8)) AS [Title],
        p.[Content]                                      AS [RawContent],
        COALESCE(kc.[CurrentStatus], N'unindexed')       AS [SyncStatus],
        CAST(p.[CreatedAt] AS DATETIME2(0))              AS [CreatedAt]
    FROM [community].[Posts] AS p
    OUTER APPLY (
        SELECT TOP (1) c.[SyncStatus] AS [CurrentStatus]
        FROM [heritage].[KnowledgeChunks] AS c
        WHERE c.[SourceType] = N'post'
          AND c.[SourceId] = p.[Id]
        ORDER BY
            CASE WHEN c.[SyncStatus] IN (N'pending', N'failed') THEN 0 ELSE 1 END,
            c.[ChunkIndex] ASC
    ) AS kc
    WHERE LEN(LTRIM(RTRIM(ISNULL(p.[Content], N'')))) > 0
      AND (kc.[CurrentStatus] IS NULL OR kc.[CurrentStatus] IN (N'pending', N'failed'))

    UNION ALL

    -- Nguồn 2: Tư liệu di sản (heritage.Items) của Thành viên 4
    SELECT
        i.[FamilyId]                                     AS [FamilyId],
        CAST(N'heritage' AS NVARCHAR(20))                AS [SourceType],
        i.[Id]                                           AS [SourceId],
        i.[Title]                                        AS [Title],
        CONCAT(
            i.[Title], N'. ',
            ISNULL(NULLIF(LTRIM(RTRIM(i.[Description])), N'') + N'. ', N''),
            ISNULL(LTRIM(RTRIM(i.[Content])), N'')
        )                                                AS [RawContent],
        COALESCE(kc.[CurrentStatus], N'unindexed')       AS [SyncStatus],
        CAST(i.[CreatedAt] AS DATETIME2(0))              AS [CreatedAt]
    FROM [heritage].[Items] AS i
    OUTER APPLY (
        SELECT TOP (1) c.[SyncStatus] AS [CurrentStatus]
        FROM [heritage].[KnowledgeChunks] AS c
        WHERE c.[SourceType] = N'heritage'
          AND c.[SourceId] = i.[Id]
        ORDER BY
            CASE WHEN c.[SyncStatus] IN (N'pending', N'failed') THEN 0 ELSE 1 END,
            c.[ChunkIndex] ASC
    ) AS kc
    WHERE (
            LEN(LTRIM(RTRIM(ISNULL(i.[Content], N'')))) > 0
            OR LEN(LTRIM(RTRIM(ISNULL(i.[Description], N'')))) > 0
          )
      AND (kc.[CurrentStatus] IS NULL OR kc.[CurrentStatus] IN (N'pending', N'failed'));
GO
