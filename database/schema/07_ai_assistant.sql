USE [$(DB_NAME)];
GO

SET XACT_ABORT ON;
GO

/* ---------------------------------------------------------------------
   1. Kiểm tra các schema và bảng nền tảng đã tồn tại
   --------------------------------------------------------------------- */
IF SCHEMA_ID(N'heritage') IS NULL OR SCHEMA_ID(N'reports') IS NULL
    THROW 50701, N'Thiếu schema heritage hoặc reports. Hãy chạy 00_schemas.sql trước.', 1;
GO

IF OBJECT_ID(N'core.Families', N'U') IS NULL OR OBJECT_ID(N'core.Users', N'U') IS NULL
    THROW 50702, N'Thiếu bảng core.Families hoặc core.Users. Hãy chạy 01_core.sql trước.', 1;
GO


/* ---------------------------------------------------------------------
   2. Bảng heritage.KnowledgeChunks
   Lưu các đoạn văn bản đã cắt nhỏ (Chunk) từ Bài viết (community.Posts),
   Di sản (heritage.Items) hoặc Hồ sơ thành viên (genealogy.Members),
   kèm bản tóm tắt (SummaryText) và dãy số Vector dạng JSON.
   --------------------------------------------------------------------- */
IF OBJECT_ID(N'heritage.KnowledgeChunks', N'U') IS NULL
BEGIN
    CREATE TABLE [heritage].[KnowledgeChunks]
    (
        [Id]            UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT [DF_KnowledgeChunks_Id] DEFAULT NEWSEQUENTIALID(),
        [FamilyId]      UNIQUEIDENTIFIER NOT NULL,
        [SourceType]    NVARCHAR(20)     NOT NULL, -- 'post', 'heritage', 'member'
        [SourceId]      UNIQUEIDENTIFIER NOT NULL, -- Id của bản ghi gốc
        [ChunkIndex]    INT              NOT NULL
            CONSTRAINT [DF_KnowledgeChunks_ChunkIndex] DEFAULT (0),
        [ChunkText]     NVARCHAR(2000)   NOT NULL,
        [SummaryText]   NVARCHAR(1000)   NULL,     -- Phục vụ AI content summarization
        [EmbeddingJson] NVARCHAR(MAX)    NULL,     -- Chuỗi JSON mảng số thực "[0.12, -0.34, ...]"
        [SyncStatus]    NVARCHAR(20)     NOT NULL
            CONSTRAINT [DF_KnowledgeChunks_SyncStatus] DEFAULT N'pending',
        [UpdatedAt]     DATETIME2(0)     NOT NULL
            CONSTRAINT [DF_KnowledgeChunks_UpdatedAt] DEFAULT SYSUTCDATETIME(),
        [CreatedAt]     DATETIME2(0)     NOT NULL
            CONSTRAINT [DF_KnowledgeChunks_CreatedAt] DEFAULT SYSUTCDATETIME(),

        CONSTRAINT [PK_KnowledgeChunks] PRIMARY KEY CLUSTERED ([Id]),
        CONSTRAINT [FK_KnowledgeChunks_Families]
            FOREIGN KEY ([FamilyId]) REFERENCES [core].[Families] ([Id]),
        CONSTRAINT [UQ_KnowledgeChunks_Source_ChunkIndex]
            UNIQUE ([SourceType], [SourceId], [ChunkIndex]),

        CONSTRAINT [CK_KnowledgeChunks_SourceType]
            CHECK ([SourceType] IN (N'post', N'heritage', N'member')),
        CONSTRAINT [CK_KnowledgeChunks_ChunkIndex]
            CHECK ([ChunkIndex] >= 0),
        CONSTRAINT [CK_KnowledgeChunks_ChunkText]
            CHECK (LEN(LTRIM(RTRIM([ChunkText]))) > 0),
        CONSTRAINT [CK_KnowledgeChunks_SyncStatus]
            CHECK ([SyncStatus] IN (N'pending', N'synced', N'failed')),
        CONSTRAINT [CK_KnowledgeChunks_EmbeddingIsJson]
            CHECK ([EmbeddingJson] IS NULL OR ISJSON([EmbeddingJson]) = 1),
        -- Đảm bảo bản ghi đã đánh dấu 'synced' bắt buộc phải có dữ liệu Vector
        CONSTRAINT [CK_KnowledgeChunks_SyncedMustHaveVector]
            CHECK (
                ([SyncStatus] = N'synced' AND [EmbeddingJson] IS NOT NULL)
                OR ([SyncStatus] IN (N'pending', N'failed'))
            )
    );
END;
GO

/* Bổ sung tương thích nếu bảng đã được tạo từ phiên bản trước */
IF COL_LENGTH(N'heritage.KnowledgeChunks', N'SummaryText') IS NULL
BEGIN
    ALTER TABLE [heritage].[KnowledgeChunks]
        ADD [SummaryText] NVARCHAR(1000) NULL;

    IF OBJECT_ID(N'heritage.CK_KnowledgeChunks_SourceType', N'C') IS NOT NULL
        ALTER TABLE [heritage].[KnowledgeChunks] DROP CONSTRAINT [CK_KnowledgeChunks_SourceType];

    ALTER TABLE [heritage].[KnowledgeChunks]
        ADD CONSTRAINT [CK_KnowledgeChunks_SourceType]
            CHECK ([SourceType] IN (N'post', N'heritage', N'member'));
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE [name] = N'IX_KnowledgeChunks_Family_SyncStatus'
      AND [object_id] = OBJECT_ID(N'heritage.KnowledgeChunks')
)
    CREATE INDEX [IX_KnowledgeChunks_Family_SyncStatus]
        ON [heritage].[KnowledgeChunks] ([FamilyId], [SyncStatus]);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE [name] = N'IX_KnowledgeChunks_Source'
      AND [object_id] = OBJECT_ID(N'heritage.KnowledgeChunks')
)
    CREATE INDEX [IX_KnowledgeChunks_Source]
        ON [heritage].[KnowledgeChunks] ([SourceType], [SourceId]);
GO


/* ---------------------------------------------------------------------
   3. Bảng reports.AiChatMessages
   Lưu lịch sử câu hỏi của thành viên và câu trả lời của Trợ lý ảo AI,
   kèm danh sách nguồn trích dẫn (ReferencedSourceIds dạng JSON).
   --------------------------------------------------------------------- */
IF OBJECT_ID(N'reports.AiChatMessages', N'U') IS NULL
BEGIN
    CREATE TABLE [reports].[AiChatMessages]
    (
        [Id]                  UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT [DF_AiChatMessages_Id] DEFAULT NEWSEQUENTIALID(),
        [FamilyId]            UNIQUEIDENTIFIER NOT NULL,
        [UserId]              UNIQUEIDENTIFIER NOT NULL,
        [QueryType]           NVARCHAR(30)     NOT NULL
            CONSTRAINT [DF_AiChatMessages_QueryType] DEFAULT N'semantic_search',
        [Question]            NVARCHAR(2000)   NOT NULL,
        [Answer]              NVARCHAR(MAX)    NOT NULL,
        [ReferencedSourceIds] NVARCHAR(MAX)    NULL,
        [CreatedAt]           DATETIME2(0)     NOT NULL
            CONSTRAINT [DF_AiChatMessages_CreatedAt] DEFAULT SYSUTCDATETIME(),

        CONSTRAINT [PK_AiChatMessages] PRIMARY KEY CLUSTERED ([Id]),
        CONSTRAINT [FK_AiChatMessages_Families]
            FOREIGN KEY ([FamilyId]) REFERENCES [core].[Families] ([Id]),
        CONSTRAINT [FK_AiChatMessages_Users]
            FOREIGN KEY ([UserId]) REFERENCES [core].[Users] ([UserId]),

        CONSTRAINT [CK_AiChatMessages_QueryType]
            CHECK ([QueryType] IN (N'semantic_search', N'kinship_explain', N'summarization', N'recommendation', N'general')),
        CONSTRAINT [CK_AiChatMessages_Question]
            CHECK (LEN(LTRIM(RTRIM([Question]))) > 0),
        CONSTRAINT [CK_AiChatMessages_Answer]
            CHECK (LEN(LTRIM(RTRIM([Answer]))) > 0),
        CONSTRAINT [CK_AiChatMessages_RefsIsJson]
            CHECK ([ReferencedSourceIds] IS NULL OR ISJSON([ReferencedSourceIds]) = 1)
    );
END
ELSE
BEGIN
    IF EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE [name] = N'CK_AiChatMessages_QueryType'
          AND [parent_object_id] = OBJECT_ID(N'reports.AiChatMessages')
          AND [definition] NOT LIKE N'%summarization%'
    )
    BEGIN
        ALTER TABLE [reports].[AiChatMessages] DROP CONSTRAINT [CK_AiChatMessages_QueryType];
        ALTER TABLE [reports].[AiChatMessages]
            ADD CONSTRAINT [CK_AiChatMessages_QueryType]
                CHECK ([QueryType] IN (N'semantic_search', N'kinship_explain', N'summarization', N'recommendation', N'general'));
    END;
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE [name] = N'IX_AiChatMessages_User_CreatedAt'
      AND [object_id] = OBJECT_ID(N'reports.AiChatMessages')
)
    CREATE INDEX [IX_AiChatMessages_User_CreatedAt]
        ON [reports].[AiChatMessages] ([UserId], [CreatedAt] DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE [name] = N'IX_AiChatMessages_Family_CreatedAt'
      AND [object_id] = OBJECT_ID(N'reports.AiChatMessages')
)
    CREATE INDEX [IX_AiChatMessages_Family_CreatedAt]
        ON [reports].[AiChatMessages] ([FamilyId], [CreatedAt] DESC);
GO

PRINT N'07_ai_assistant.sql: Hoàn tất tạo/cập nhật bảng heritage.KnowledgeChunks và reports.AiChatMessages.';
GO
