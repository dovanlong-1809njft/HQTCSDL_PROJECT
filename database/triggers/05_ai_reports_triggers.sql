-- T-SQL Triggers - Thành viên 5 (AI Vector Sync & Reports)
USE [$(DB_NAME)];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

/* =====================================================================
   1. Trigger: community.trg_Posts_SyncKnowledgeChunks
   Khi bài viết cộng đồng (community.Posts) bị xóa hoặc chỉnh sửa nội dung:
     - DELETE: Tự động xóa các đoạn Vector tương ứng trong heritage.KnowledgeChunks
     - UPDATE Content: Đánh dấu SyncStatus = 'pending' để Pipeline AI cắt đoạn
       và tính lại Vector mới.
   ===================================================================== */
CREATE OR ALTER TRIGGER [community].[trg_Posts_SyncKnowledgeChunks]
ON [community].[Posts]
AFTER UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID(N'heritage.KnowledgeChunks', N'U') IS NULL
        RETURN;

    -- 1. Trường hợp xóa bài viết: dọn sạch các chunk của bài viết đã xóa
    IF EXISTS (SELECT 1 FROM deleted) AND NOT EXISTS (SELECT 1 FROM inserted)
    BEGIN
        DELETE kc
        FROM [heritage].[KnowledgeChunks] AS kc
        INNER JOIN deleted AS d
            ON kc.[SourceType] = N'post'
           AND kc.[SourceId] = d.[Id];
        RETURN;
    END;

    -- 2. Trường hợp cập nhật nội dung bài viết: đánh dấu 'pending' để đồng bộ lại
    IF UPDATE([Content])
    BEGIN
        UPDATE kc
        SET kc.[SyncStatus] = N'pending',
            kc.[UpdatedAt]  = SYSUTCDATETIME()
        FROM [heritage].[KnowledgeChunks] AS kc
        INNER JOIN inserted AS i
            ON kc.[SourceType] = N'post'
           AND kc.[SourceId] = i.[Id]
        INNER JOIN deleted AS d
            ON d.[Id] = i.[Id]
        WHERE ISNULL(i.[Content], N'') <> ISNULL(d.[Content], N'');
    END;
END;
GO

/* =====================================================================
   2. Trigger: heritage.trg_Items_SyncKnowledgeChunks
   Khi tư liệu di sản (heritage.Items) bị xóa hoặc cập nhật Title/Description/Content:
     - DELETE: Tự động xóa các đoạn Vector tương ứng trong heritage.KnowledgeChunks
     - UPDATE: Đánh dấu SyncStatus = 'pending' để Pipeline AI đồng bộ lại.
   ===================================================================== */
CREATE OR ALTER TRIGGER [heritage].[trg_Items_SyncKnowledgeChunks]
ON [heritage].[Items]
AFTER UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID(N'heritage.KnowledgeChunks', N'U') IS NULL
        RETURN;

    -- 1. Trường hợp xóa tư liệu di sản: dọn sạch các chunk của tư liệu đã xóa
    IF EXISTS (SELECT 1 FROM deleted) AND NOT EXISTS (SELECT 1 FROM inserted)
    BEGIN
        DELETE kc
        FROM [heritage].[KnowledgeChunks] AS kc
        INNER JOIN deleted AS d
            ON kc.[SourceType] = N'heritage'
           AND kc.[SourceId] = d.[Id];
        RETURN;
    END;

    -- 2. Trường hợp cập nhật nội dung tư liệu: đánh dấu 'pending' để đồng bộ lại
    IF UPDATE([Title]) OR UPDATE([Description]) OR UPDATE([Content])
    BEGIN
        UPDATE kc
        SET kc.[SyncStatus] = N'pending',
            kc.[UpdatedAt]  = SYSUTCDATETIME()
        FROM [heritage].[KnowledgeChunks] AS kc
        INNER JOIN inserted AS i
            ON kc.[SourceType] = N'heritage'
           AND kc.[SourceId] = i.[Id]
        INNER JOIN deleted AS d
            ON d.[Id] = i.[Id]
        WHERE ISNULL(i.[Title], N'') <> ISNULL(d.[Title], N'')
           OR ISNULL(i.[Description], N'') <> ISNULL(d.[Description], N'')
           OR ISNULL(i.[Content], N'') <> ISNULL(d.[Content], N'');
    END;
END;
GO
