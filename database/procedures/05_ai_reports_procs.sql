USE [$(DB_NAME)];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

/* =====================================================================
   1. Stored Procedure: heritage.usp_UpsertKnowledgeChunk
   Thêm mới hoặc cập nhật (MERGE) một đoạn văn bản (Chunk) kèm mảng
   Vector nhúng (EmbeddingJson) và bản tóm tắt (SummaryText) vào bảng
   heritage.KnowledgeChunks trong một giao tác an toàn.
   ===================================================================== */
CREATE OR ALTER PROCEDURE [heritage].[usp_UpsertKnowledgeChunk]
    @FamilyId      UNIQUEIDENTIFIER,
    @SourceType    NVARCHAR(20),            -- 'post', 'heritage', hoặc 'member'
    @SourceId      UNIQUEIDENTIFIER,        -- Id bản ghi gốc
    @ChunkIndex    INT = 0,                 -- Thứ tự đoạn cắt (0, 1, 2...)
    @ChunkText     NVARCHAR(2000),          -- Nội dung văn bản gốc của đoạn
    @EmbeddingJson NVARCHAR(MAX),           -- Chuỗi JSON mảng số thực '[0.12, -0.34, ...]'
    @SummaryText   NVARCHAR(1000) = NULL    -- Bản tóm tắt ngắn do AI tạo (tùy chọn)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF @SourceType NOT IN (N'post', N'heritage', N'member')
        THROW 50711, N'SourceType không hợp lệ (chỉ nhận post, heritage, hoặc member).', 1;

    IF @ChunkText IS NULL OR LEN(LTRIM(RTRIM(@ChunkText))) = 0
        THROW 50712, N'ChunkText không được để trống.', 1;

    IF @EmbeddingJson IS NULL OR ISJSON(@EmbeddingJson) <> 1
        THROW 50713, N'EmbeddingJson phải là chuỗi mảng JSON hợp lệ.', 1;

    BEGIN TRY
        BEGIN TRAN;

        DECLARE @OutputTable TABLE ([Id] UNIQUEIDENTIFIER, [ActionTaken] NVARCHAR(10));

        MERGE INTO [heritage].[KnowledgeChunks] AS target
        USING (
            SELECT
                @FamilyId      AS [FamilyId],
                @SourceType    AS [SourceType],
                @SourceId      AS [SourceId],
                @ChunkIndex    AS [ChunkIndex],
                @ChunkText     AS [ChunkText],
                @SummaryText   AS [SummaryText],
                @EmbeddingJson AS [EmbeddingJson]
        ) AS source
        ON  target.[SourceType] = source.[SourceType]
        AND target.[SourceId]   = source.[SourceId]
        AND target.[ChunkIndex] = source.[ChunkIndex]

        WHEN MATCHED THEN
            UPDATE SET
                target.[FamilyId]      = source.[FamilyId],
                target.[ChunkText]     = source.[ChunkText],
                target.[SummaryText]   = COALESCE(source.[SummaryText], target.[SummaryText]),
                target.[EmbeddingJson] = source.[EmbeddingJson],
                target.[SyncStatus]    = N'synced',
                target.[UpdatedAt]     = SYSUTCDATETIME()

        WHEN NOT MATCHED THEN
            INSERT ([FamilyId], [SourceType], [SourceId], [ChunkIndex], [ChunkText], [SummaryText], [EmbeddingJson], [SyncStatus], [UpdatedAt])
            VALUES (source.[FamilyId], source.[SourceType], source.[SourceId], source.[ChunkIndex], source.[ChunkText], source.[SummaryText], source.[EmbeddingJson], N'synced', SYSUTCDATETIME())

        OUTPUT inserted.[Id], $action INTO @OutputTable;

        COMMIT TRAN;

        SELECT [Id] AS [ChunkId], [ActionTaken] FROM @OutputTable;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRAN;
        THROW;
    END CATCH;
END;
GO

/* =====================================================================
   2. Stored Procedure: heritage.usp_ClearStaleKnowledgeChunks
   Dọn dẹp các đoạn Chunk thừa (ChunkIndex >= @KeepChunkCount) sau khi
   một Bài viết hoặc Tư liệu di sản được cắt đoạn lại.
   ===================================================================== */
CREATE OR ALTER PROCEDURE [heritage].[usp_ClearStaleKnowledgeChunks]
    @SourceType     NVARCHAR(20),
    @SourceId       UNIQUEIDENTIFIER,
    @KeepChunkCount INT = 0
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DELETE FROM [heritage].[KnowledgeChunks]
    WHERE [SourceType] = @SourceType
      AND [SourceId]   = @SourceId
      AND [ChunkIndex] >= @KeepChunkCount;

    SELECT @@ROWCOUNT AS [DeletedChunkCount];
END;
GO

/* =====================================================================
   3. Stored Procedure: heritage.usp_SemanticSearch
   Tìm kiếm ngữ nghĩa (Semantic Vector Search) bằng hàm T-SQL
   heritage.fn_CosineSimilarity. Trả về Top-K đoạn văn bản (mặc định Top 3)
   trong cùng FamilyId có điểm tương đồng Cosine cao nhất (>= @MinScore).
   ===================================================================== */
CREATE OR ALTER PROCEDURE [heritage].[usp_SemanticSearch]
    @FamilyId        UNIQUEIDENTIFIER,
    @QueryVectorJson NVARCHAR(MAX),
    @TopK            INT = 3,
    @MinScore        FLOAT = 0.30,
    @SourceType      NVARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    IF @FamilyId IS NULL
        THROW 50721, N'FamilyId không được để trống.', 1;

    IF @QueryVectorJson IS NULL OR ISJSON(@QueryVectorJson) <> 1
        THROW 50722, N'QueryVectorJson phải là chuỗi mảng JSON hợp lệ.', 1;

    IF @TopK IS NULL OR @TopK < 1
        SET @TopK = 3;
    IF @TopK > 20
        SET @TopK = 20;

    IF @MinScore IS NULL
        SET @MinScore = 0.30;

    ;WITH ScoredChunks AS
    (
        SELECT
            kc.[Id]            AS [ChunkId],
            kc.[FamilyId]      AS [FamilyId],
            kc.[SourceType]    AS [SourceType],
            kc.[SourceId]      AS [SourceId],
            COALESCE(
                hi.[Title],
                m.[FullName],
                CONCAT(N'Bài viết cộng đồng #', LEFT(CONVERT(NVARCHAR(36), kc.[SourceId]), 8))
            )                  AS [SourceTitle],
            kc.[ChunkIndex]    AS [ChunkIndex],
            kc.[ChunkText]     AS [ChunkText],
            kc.[SummaryText]   AS [SummaryText],
            [heritage].[fn_CosineSimilarity](@QueryVectorJson, kc.[EmbeddingJson]) AS [SimilarityScore],
            kc.[UpdatedAt]     AS [UpdatedAt]
        FROM [heritage].[KnowledgeChunks] AS kc
        LEFT JOIN [heritage].[Items] AS hi
            ON kc.[SourceType] = N'heritage' AND hi.[Id] = kc.[SourceId]
        LEFT JOIN [genealogy].[Members] AS m
            ON kc.[SourceType] = N'member' AND m.[Id] = kc.[SourceId]
        WHERE kc.[FamilyId] = @FamilyId
          AND kc.[SyncStatus] = N'synced'
          AND kc.[EmbeddingJson] IS NOT NULL
          AND (@SourceType IS NULL OR kc.[SourceType] = @SourceType)
    )
    SELECT TOP (@TopK)
        [ChunkId],
        [FamilyId],
        [SourceType],
        [SourceId],
        [SourceTitle],
        [ChunkIndex],
        [ChunkText],
        [SummaryText],
        ROUND([SimilarityScore], 6) AS [SimilarityScore],
        [UpdatedAt]
    FROM ScoredChunks
    WHERE [SimilarityScore] IS NOT NULL
      AND [SimilarityScore] >= @MinScore
    ORDER BY [SimilarityScore] DESC, [ChunkIndex] ASC;
END;
GO

/* =====================================================================
   4. Stored Procedure: genealogy.usp_FindRelationshipPath
   Truy vấn bảng bao đóng genealogy.MemberClosure (của Thành viên 2) kết hợp
   bảng genealogy.Marriages và genealogy.ParentChild để tìm:
     - Tổ tiên chung gần nhất (Lowest Common Ancestor - LCA)
     - Số bậc thế hệ từ LCA tới Thành viên A (DepthA) và Thành viên B (DepthB)
     - Đường đi phả hệ chi tiết từ tổ tiên chung tới từng thành viên
     - Gợi ý danh xưng / quan hệ họ hàng Việt Nam chuẩn xác.
   ===================================================================== */
CREATE OR ALTER PROCEDURE [genealogy].[usp_FindRelationshipPath]
    @MemberAId UNIQUEIDENTIFIER,
    @MemberBId UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF @MemberAId IS NULL OR @MemberBId IS NULL
        THROW 50731, N'MemberAId và MemberBId không được để trống.', 1;

    DECLARE
        @FamilyA     UNIQUEIDENTIFIER,
        @FamilyB     UNIQUEIDENTIFIER,
        @NameA       NVARCHAR(200),
        @NameB       NVARCHAR(200),
        @BirthA      DATE,
        @BirthB      DATE,
        @BranchNameA NVARCHAR(200),
        @BranchNameB NVARCHAR(200);

    SELECT
        @FamilyA     = m.[FamilyId],
        @NameA       = m.[FullName],
        @BirthA      = m.[BirthDate],
        @BranchNameA = b.[Name]
    FROM [genealogy].[Members] AS m
    LEFT JOIN [core].[Branches] AS b ON b.[Id] = m.[BranchId]
    WHERE m.[Id] = @MemberAId;

    SELECT
        @FamilyB     = m.[FamilyId],
        @NameB       = m.[FullName],
        @BirthB      = m.[BirthDate],
        @BranchNameB = b.[Name]
    FROM [genealogy].[Members] AS m
    LEFT JOIN [core].[Branches] AS b ON b.[Id] = m.[BranchId]
    WHERE m.[Id] = @MemberBId;

    IF @NameA IS NULL OR @NameB IS NULL
        THROW 50732, N'Một hoặc cả hai thành viên không tồn tại trong gia phả.', 1;

    -- Đảm bảo bảng bao đóng genealogy.MemberClosure đã được đồng bộ đầy đủ
    -- cho dòng họ này (phòng trường hợp dữ liệu được chèn trực tiếp từ 01_seed.sql)
    IF EXISTS (
        SELECT 1
        FROM [genealogy].[Members] AS m
        WHERE m.[FamilyId] IN (@FamilyA, @FamilyB)
          AND NOT EXISTS (
              SELECT 1
              FROM [genealogy].[MemberClosure] AS mc
              WHERE mc.[AncestorId] = m.[Id] AND mc.[DescendantId] = m.[Id]
          )
    )
    OR EXISTS (
        SELECT 1
        FROM [genealogy].[ParentChild] AS pc
        INNER JOIN [genealogy].[Members] AS m ON m.[Id] = pc.[ParentId]
        WHERE m.[FamilyId] IN (@FamilyA, @FamilyB)
          AND NOT EXISTS (
              SELECT 1
              FROM [genealogy].[MemberClosure] AS mc
              WHERE mc.[AncestorId] = pc.[ParentId] AND mc.[DescendantId] = pc.[ChildId]
          )
    )
    BEGIN
        ;WITH ClosureTree AS
        (
            SELECT
                m.[Id] AS [AncestorId],
                m.[Id] AS [DescendantId],
                0      AS [Depth]
            FROM [genealogy].[Members] AS m
            WHERE m.[FamilyId] IN (@FamilyA, @FamilyB)

            UNION ALL

            SELECT
                ct.[AncestorId],
                pc.[ChildId] AS [DescendantId],
                ct.[Depth] + 1 AS [Depth]
            FROM ClosureTree AS ct
            INNER JOIN [genealogy].[ParentChild] AS pc
                ON pc.[ParentId] = ct.[DescendantId]
            WHERE ct.[Depth] < 30
        ),
        MinClosure AS
        (
            SELECT
                [AncestorId],
                [DescendantId],
                MIN([Depth]) AS [Depth]
            FROM ClosureTree
            GROUP BY [AncestorId], [DescendantId]
        )
        MERGE INTO [genealogy].[MemberClosure] AS target
        USING MinClosure AS source
        ON  target.[AncestorId]   = source.[AncestorId]
        AND target.[DescendantId] = source.[DescendantId]
        WHEN MATCHED AND source.[Depth] < target.[Depth] THEN
            UPDATE SET target.[Depth] = source.[Depth]
        WHEN NOT MATCHED THEN
            INSERT ([AncestorId], [DescendantId], [Depth])
            VALUES (source.[AncestorId], source.[DescendantId], source.[Depth]);
    END;

    -- Trường hợp 1: Hai ID là cùng một người
    IF @MemberAId = @MemberBId
    BEGIN
        SELECT
            @MemberAId                                          AS [MemberAId],
            @NameA                                              AS [MemberAName],
            @BirthA                                             AS [MemberABirthDate],
            @BranchNameA                                        AS [MemberABranchName],
            @MemberBId                                          AS [MemberBId],
            @NameB                                              AS [MemberBName],
            @BirthB                                             AS [MemberBBirthDate],
            @BranchNameB                                        AS [MemberBBranchName],
            CAST(N'self' AS NVARCHAR(30))                       AS [RelationshipCategory],
            @MemberAId                                          AS [CommonAncestorId],
            @NameA                                              AS [CommonAncestorName],
            0                                                   AS [DepthFromAncestorToA],
            0                                                   AS [DepthFromAncestorToB],
            0                                                   AS [TotalGenerationDistance],
            @NameA                                              AS [PathFromAncestorToA],
            @NameB                                              AS [PathFromAncestorToB],
            [genealogy].[fn_SuggestVietnameseKinship](0, 0)     AS [SuggestedKinship];
        RETURN;
    END;

    -- Trường hợp 2: Quan hệ Vợ - Chồng trực tiếp trong bảng genealogy.Marriages
    DECLARE @MarriedDate DATE = NULL;
    SELECT TOP (1) @MarriedDate = mr.[MarriedDate]
    FROM [genealogy].[Marriages] AS mr
    WHERE (mr.[Spouse1Id] = @MemberAId AND mr.[Spouse2Id] = @MemberBId)
       OR (mr.[Spouse1Id] = @MemberBId AND mr.[Spouse2Id] = @MemberAId);

    IF @MarriedDate IS NOT NULL OR EXISTS (
        SELECT 1 FROM [genealogy].[Marriages] AS mr
        WHERE (mr.[Spouse1Id] = @MemberAId AND mr.[Spouse2Id] = @MemberBId)
           OR (mr.[Spouse1Id] = @MemberBId AND mr.[Spouse2Id] = @MemberAId)
    )
    BEGIN
        SELECT
            @MemberAId                                          AS [MemberAId],
            @NameA                                              AS [MemberAName],
            @BirthA                                             AS [MemberABirthDate],
            @BranchNameA                                        AS [MemberABranchName],
            @MemberBId                                          AS [MemberBId],
            @NameB                                              AS [MemberBName],
            @BirthB                                             AS [MemberBBirthDate],
            @BranchNameB                                        AS [MemberBBranchName],
            CAST(N'marriage' AS NVARCHAR(30))                   AS [RelationshipCategory],
            CAST(NULL AS UNIQUEIDENTIFIER)                      AS [CommonAncestorId],
            CAST(NULL AS NVARCHAR(200))                         AS [CommonAncestorName],
            0                                                   AS [DepthFromAncestorToA],
            0                                                   AS [DepthFromAncestorToB],
            0                                                   AS [TotalGenerationDistance],
            CONCAT(@NameA, N' <==> ', @NameB)                   AS [PathFromAncestorToA],
            CONCAT(@NameB, N' <==> ', @NameA)                   AS [PathFromAncestorToB],
            CONCAT(
                N'Quan hệ Hôn nhân: Vợ — Chồng (', @NameA, N' và ', @NameB,
                CASE WHEN @MarriedDate IS NOT NULL
                     THEN CONCAT(N', kết hôn ngày ', CONVERT(NVARCHAR(10), @MarriedDate, 120))
                     ELSE N''
                END,
                N')'
            )                                                   AS [SuggestedKinship];
        RETURN;
    END;

    -- Trường hợp 3: Quan hệ huyết thống trực hệ hoặc bàng hệ qua bảng bao đóng MemberClosure
    DECLARE
        @CommonAncestorId   UNIQUEIDENTIFIER = NULL,
        @CommonAncestorName NVARCHAR(200)    = NULL,
        @DepthA             INT              = NULL,
        @DepthB             INT              = NULL;

    SELECT TOP (1)
        @CommonAncestorId   = ca.[AncestorId],
        @CommonAncestorName = anc.[FullName],
        @DepthA             = ca.[Depth],
        @DepthB             = cb.[Depth]
    FROM [genealogy].[MemberClosure] AS ca
    INNER JOIN [genealogy].[MemberClosure] AS cb
        ON cb.[AncestorId] = ca.[AncestorId]
    INNER JOIN [genealogy].[Members] AS anc
        ON anc.[Id] = ca.[AncestorId]
    WHERE ca.[DescendantId] = @MemberAId
      AND cb.[DescendantId] = @MemberBId
    ORDER BY
        (ca.[Depth] + cb.[Depth]) ASC,
        ca.[Depth] ASC,
        anc.[BirthDate] ASC;

    IF @CommonAncestorId IS NOT NULL
    BEGIN
        DECLARE @PathToA NVARCHAR(1000) = @CommonAncestorName;
        DECLARE @PathToB NVARCHAR(1000) = @CommonAncestorName;

        -- Dựng chuỗi đường đi từ Tổ tiên chung xuống A dựa trên MemberClosure
        SELECT @PathToA = STRING_AGG(m.[FullName], N' -> ') WITHIN GROUP (ORDER BY cUp.[Depth] ASC)
        FROM [genealogy].[MemberClosure] AS cUp
        INNER JOIN [genealogy].[MemberClosure] AS cDown
            ON cDown.[AncestorId] = cUp.[DescendantId]
        INNER JOIN [genealogy].[Members] AS m
            ON m.[Id] = cUp.[DescendantId]
        WHERE cUp.[AncestorId] = @CommonAncestorId
          AND cDown.[DescendantId] = @MemberAId
          AND (cUp.[Depth] + cDown.[Depth]) = @DepthA;

        -- Dựng chuỗi đường đi từ Tổ tiên chung xuống B dựa trên MemberClosure
        SELECT @PathToB = STRING_AGG(m.[FullName], N' -> ') WITHIN GROUP (ORDER BY cUp.[Depth] ASC)
        FROM [genealogy].[MemberClosure] AS cUp
        INNER JOIN [genealogy].[MemberClosure] AS cDown
            ON cDown.[AncestorId] = cUp.[DescendantId]
        INNER JOIN [genealogy].[Members] AS m
            ON m.[Id] = cUp.[DescendantId]
        WHERE cUp.[AncestorId] = @CommonAncestorId
          AND cDown.[DescendantId] = @MemberBId
          AND (cUp.[Depth] + cDown.[Depth]) = @DepthB;

        SELECT
            @MemberAId                                          AS [MemberAId],
            @NameA                                              AS [MemberAName],
            @BirthA                                             AS [MemberABirthDate],
            @BranchNameA                                        AS [MemberABranchName],
            @MemberBId                                          AS [MemberBId],
            @NameB                                              AS [MemberBName],
            @BirthB                                             AS [MemberBBirthDate],
            @BranchNameB                                        AS [MemberBBranchName],
            CASE
                WHEN @DepthA = 0 OR @DepthB = 0 THEN CAST(N'direct_lineage' AS NVARCHAR(30))
                ELSE CAST(N'collateral_bloodline' AS NVARCHAR(30))
            END                                                 AS [RelationshipCategory],
            @CommonAncestorId                                   AS [CommonAncestorId],
            @CommonAncestorName                                 AS [CommonAncestorName],
            @DepthA                                             AS [DepthFromAncestorToA],
            @DepthB                                             AS [DepthFromAncestorToB],
            (@DepthA + @DepthB)                                 AS [TotalGenerationDistance],
            ISNULL(@PathToA, @NameA)                            AS [PathFromAncestorToA],
            ISNULL(@PathToB, @NameB)                            AS [PathFromAncestorToB],
            [genealogy].[fn_SuggestVietnameseKinship](@DepthA, @DepthB) AS [SuggestedKinship];
        RETURN;
    END;

    -- Trường hợp 4: Quan hệ Thông gia / Dâu / Rể (một người là vợ/chồng của người có huyết thống với người kia)
    DECLARE
        @SpouseId           UNIQUEIDENTIFIER = NULL,
        @SpouseName         NVARCHAR(200)    = NULL,
        @SpouseSide         NVARCHAR(10)     = NULL,
        @AffinalAncestorId  UNIQUEIDENTIFIER = NULL,
        @AffinalAncestor    NVARCHAR(200)    = NULL,
        @AffinalDepthA      INT              = NULL,
        @AffinalDepthB      INT              = NULL;

    -- Kiểm tra nếu B là vợ/chồng của một người S có huyết thống với A
    SELECT TOP (1)
        @SpouseId          = s.[Id],
        @SpouseName        = s.[FullName],
        @SpouseSide        = N'B',
        @AffinalAncestorId = ca.[AncestorId],
        @AffinalAncestor   = anc.[FullName],
        @AffinalDepthA     = ca.[Depth],
        @AffinalDepthB     = cs.[Depth]
    FROM [genealogy].[Marriages] AS mr
    INNER JOIN [genealogy].[Members] AS s
        ON s.[Id] = CASE WHEN mr.[Spouse1Id] = @MemberBId THEN mr.[Spouse2Id] ELSE mr.[Spouse1Id] END
    INNER JOIN [genealogy].[MemberClosure] AS ca
        ON ca.[DescendantId] = @MemberAId
    INNER JOIN [genealogy].[MemberClosure] AS cs
        ON cs.[AncestorId] = ca.[AncestorId] AND cs.[DescendantId] = s.[Id]
    INNER JOIN [genealogy].[Members] AS anc
        ON anc.[Id] = ca.[AncestorId]
    WHERE mr.[Spouse1Id] = @MemberBId OR mr.[Spouse2Id] = @MemberBId
    ORDER BY (ca.[Depth] + cs.[Depth]) ASC;

    -- Nếu chưa thấy, kiểm tra nếu A là vợ/chồng của một người S có huyết thống với B
    IF @SpouseId IS NULL
    BEGIN
        SELECT TOP (1)
            @SpouseId          = s.[Id],
            @SpouseName        = s.[FullName],
            @SpouseSide        = N'A',
            @AffinalAncestorId = cb.[AncestorId],
            @AffinalAncestor   = anc.[FullName],
            @AffinalDepthA     = cs.[Depth],
            @AffinalDepthB     = cb.[Depth]
        FROM [genealogy].[Marriages] AS mr
        INNER JOIN [genealogy].[Members] AS s
            ON s.[Id] = CASE WHEN mr.[Spouse1Id] = @MemberAId THEN mr.[Spouse2Id] ELSE mr.[Spouse1Id] END
        INNER JOIN [genealogy].[MemberClosure] AS cb
            ON cb.[DescendantId] = @MemberBId
        INNER JOIN [genealogy].[MemberClosure] AS cs
            ON cs.[AncestorId] = cb.[AncestorId] AND cs.[DescendantId] = s.[Id]
        INNER JOIN [genealogy].[Members] AS anc
            ON anc.[Id] = cb.[AncestorId]
        WHERE mr.[Spouse1Id] = @MemberAId OR mr.[Spouse2Id] = @MemberAId
        ORDER BY (cs.[Depth] + cb.[Depth]) ASC;
    END;

    IF @SpouseId IS NOT NULL
    BEGIN
        SELECT
            @MemberAId                                          AS [MemberAId],
            @NameA                                              AS [MemberAName],
            @BirthA                                             AS [MemberABirthDate],
            @BranchNameA                                        AS [MemberABranchName],
            @MemberBId                                          AS [MemberBId],
            @NameB                                              AS [MemberBName],
            @BirthB                                             AS [MemberBBirthDate],
            @BranchNameB                                        AS [MemberBBranchName],
            CAST(N'affinal_in_law' AS NVARCHAR(30))             AS [RelationshipCategory],
            @AffinalAncestorId                                  AS [CommonAncestorId],
            @AffinalAncestor                                    AS [CommonAncestorName],
            @AffinalDepthA                                      AS [DepthFromAncestorToA],
            @AffinalDepthB                                      AS [DepthFromAncestorToB],
            (@AffinalDepthA + @AffinalDepthB)                   AS [TotalGenerationDistance],
            CASE WHEN @SpouseSide = N'A'
                 THEN CONCAT(@AffinalAncestor, N' -> ... -> ', @SpouseName, N' (Vợ/Chồng của ', @NameA, N')')
                 ELSE CONCAT(@AffinalAncestor, N' -> ... -> ', @NameA)
            END                                                 AS [PathFromAncestorToA],
            CASE WHEN @SpouseSide = N'B'
                 THEN CONCAT(@AffinalAncestor, N' -> ... -> ', @SpouseName, N' (Vợ/Chồng của ', @NameB, N')')
                 ELSE CONCAT(@AffinalAncestor, N' -> ... -> ', @NameB)
            END                                                 AS [PathFromAncestorToB],
            CONCAT(
                N'Quan hệ Họ hàng qua Hôn nhân (Dâu/Rể): Thông qua ', @SpouseName,
                N' — ', [genealogy].[fn_SuggestVietnameseKinship](@AffinalDepthA, @AffinalDepthB)
            )                                                   AS [SuggestedKinship];
        RETURN;
    END;

    -- Trường hợp 5: Chưa tìm thấy đường nối trong cây gia phả
    SELECT
        @MemberAId                                              AS [MemberAId],
        @NameA                                                  AS [MemberAName],
        @BirthA                                                 AS [MemberABirthDate],
        @BranchNameA                                            AS [MemberABranchName],
        @MemberBId                                              AS [MemberBId],
        @NameB                                                  AS [MemberBName],
        @BirthB                                                 AS [MemberBBirthDate],
        @BranchNameB                                            AS [MemberBBranchName],
        CAST(N'unconnected' AS NVARCHAR(30))                    AS [RelationshipCategory],
        CAST(NULL AS UNIQUEIDENTIFIER)                          AS [CommonAncestorId],
        CAST(NULL AS NVARCHAR(200))                             AS [CommonAncestorName],
        CAST(NULL AS INT)                                       AS [DepthFromAncestorToA],
        CAST(NULL AS INT)                                       AS [DepthFromAncestorToB],
        CAST(NULL AS INT)                                       AS [TotalGenerationDistance],
        @NameA                                                  AS [PathFromAncestorToA],
        @NameB                                                  AS [PathFromAncestorToB],
        CAST(N'Chưa tìm thấy tổ tiên chung hoặc liên kết hôn nhân trực tiếp giữa hai thành viên.' AS NVARCHAR(300)) AS [SuggestedKinship];
END;
GO

/* =====================================================================
   5. Stored Procedure: reports.usp_SaveAiChatMessage
   Ghi nhận lịch sử hỏi đáp của người dùng với Trợ lý ảo AI vào bảng
   reports.AiChatMessages kèm danh sách ID nguồn tư liệu trích dẫn.
   ===================================================================== */
CREATE OR ALTER PROCEDURE [reports].[usp_SaveAiChatMessage]
    @FamilyId            UNIQUEIDENTIFIER,
    @UserId              UNIQUEIDENTIFIER,
    @QueryType           NVARCHAR(30) = N'semantic_search',
    @Question            NVARCHAR(2000),
    @Answer              NVARCHAR(MAX),
    @ReferencedSourceIds NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF @QueryType NOT IN (N'semantic_search', N'kinship_explain', N'summarization', N'recommendation', N'general')
        THROW 50741, N'QueryType không hợp lệ.', 1;

    IF @ReferencedSourceIds IS NOT NULL AND ISJSON(@ReferencedSourceIds) <> 1
        THROW 50742, N'ReferencedSourceIds phải là chuỗi JSON hợp lệ hoặc NULL.', 1;

    DECLARE @Inserted TABLE ([Id] UNIQUEIDENTIFIER, [CreatedAt] DATETIME2(0));

    INSERT INTO [reports].[AiChatMessages]
        ([FamilyId], [UserId], [QueryType], [Question], [Answer], [ReferencedSourceIds])
    OUTPUT inserted.[Id], inserted.[CreatedAt] INTO @Inserted
    VALUES
        (@FamilyId, @UserId, @QueryType, @Question, @Answer, @ReferencedSourceIds);

    SELECT [Id] AS [MessageId], [CreatedAt] FROM @Inserted;
END;
GO
