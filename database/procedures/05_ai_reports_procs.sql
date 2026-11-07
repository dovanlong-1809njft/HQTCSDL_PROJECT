

USE [$(DB_NAME)];
GO

/* ---------------------------------------------------------------------
   Stored Procedure: heritage.usp_UpsertKnowledgeChunk
   Thêm mới hoặc cập nhật (MERGE) một đoạn văn bản (Chunk) kèm mảng
   Vector nhúng (EmbeddingJson) và bản tóm tắt (SummaryText) vào bảng
   heritage.KnowledgeChunks trong một giao tác an toàn.
   --------------------------------------------------------------------- */
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
