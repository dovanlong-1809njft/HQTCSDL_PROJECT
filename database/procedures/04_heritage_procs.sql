-- T-SQL Stored Procedures - Thanh vien 4 (heritage & family tree)
USE [$(DB_NAME)];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO
-- Shared only within TV4. Linked Members.UserId is the authoritative membership
-- established by TV1's approval procedure (seed/admin-linked members also work).
CREATE OR ALTER PROCEDURE heritage.usp_AssertFamilyAccess
    @ActorUserId UNIQUEIDENTIFIER, @FamilyId UNIQUEIDENTIFIER, @Manage BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Role NVARCHAR(20);
    SELECT @Role = Role FROM core.Users WITH (HOLDLOCK)
    WHERE UserId = @ActorUserId AND IsActive = 1;
    IF @Role IS NULL OR @Role NOT IN (N'admin', N'family_head', N'member')
        THROW 51403, N'Family access denied.', 1;
    IF @Role <> N'admin' AND NOT EXISTS (
        SELECT 1 FROM genealogy.Members WITH (HOLDLOCK)
        WHERE UserId = @ActorUserId AND FamilyId = @FamilyId)
        THROW 51403, N'Family access denied.', 1;
    IF @Manage = 1 AND @Role NOT IN (N'admin', N'family_head')
        THROW 51403, N'Family manager required.', 1;
    IF NOT EXISTS (SELECT 1 FROM core.Families WITH (HOLDLOCK) WHERE Id = @FamilyId)
        THROW 51404, N'Family not found.', 1;
END;
GO
CREATE OR ALTER PROCEDURE heritage.usp_ValidateHeritageItem
    @Type NVARCHAR(MAX), @Title NVARCHAR(MAX), @Description NVARCHAR(MAX),
    @Content NVARCHAR(MAX), @MediaUrl NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;
    IF @Type IS NULL OR @Type NOT IN (N'document', N'story', N'photo')
       OR NULLIF(LTRIM(RTRIM(@Title)), N'') IS NULL OR DATALENGTH(@Title) > 400
       OR DATALENGTH(@Description) > 1000 OR DATALENGTH(@MediaUrl) > 1000
       OR (@Type = N'story' AND NULLIF(LTRIM(RTRIM(@Content)), N'') IS NULL)
       OR (@Type = N'photo' AND NULLIF(LTRIM(RTRIM(@MediaUrl)), N'') IS NULL)
       OR (@Type = N'document' AND NULLIF(LTRIM(RTRIM(@Content)), N'') IS NULL
                                   AND NULLIF(LTRIM(RTRIM(@MediaUrl)), N'') IS NULL)
        THROW 51422, N'Invalid heritage payload.', 1;
    IF @MediaUrl IS NOT NULL AND NOT
       (@MediaUrl LIKE N'https://%_.%' OR (@MediaUrl LIKE N'/%' AND @MediaUrl NOT LIKE N'//%'))
        THROW 51422, N'Use HTTPS or a local media path.', 1;
END;
GO
CREATE OR ALTER PROCEDURE heritage.usp_CreateHeritageItem
    @ActorUserId UNIQUEIDENTIFIER, @FamilyId UNIQUEIDENTIFIER,
    @Type NVARCHAR(MAX), @Title NVARCHAR(MAX), @Description NVARCHAR(MAX) = NULL,
    @Content NVARCHAR(MAX) = NULL, @MediaUrl NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Started BIT = CASE WHEN @@TRANCOUNT = 0 THEN 1 ELSE 0 END;
    DECLARE @Id UNIQUEIDENTIFIER = NEWID();
    BEGIN TRY
        IF @Started = 1 BEGIN TRANSACTION; ELSE SAVE TRANSACTION TV4CreateItem;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId, @FamilyId;
        EXEC heritage.usp_ValidateHeritageItem @Type, @Title, @Description, @Content, @MediaUrl;
        INSERT INTO heritage.Items (Id, FamilyId, CreatedByUserId, Type, Title, Description, Content, MediaUrl)
        VALUES (@Id, @FamilyId, @ActorUserId, @Type, @Title, @Description, @Content, @MediaUrl);
        INSERT INTO reports.AuditLog (UserId, Action)
        VALUES (@ActorUserId, CONCAT(N'heritage.item.created; id=', CONVERT(NVARCHAR(36), @Id)));
        -- Materialize before releasing locks, return only after COMMIT.
        SELECT * INTO #TV4CreatedItem FROM heritage.vw_HeritageItems WHERE Id = @Id;
        IF @Started = 1 COMMIT TRANSACTION;
        SELECT * FROM #TV4CreatedItem;
    END TRY
    BEGIN CATCH
        IF @Started = 1 AND XACT_STATE() <> 0 ROLLBACK TRANSACTION;
        ELSE IF XACT_STATE() = 1 ROLLBACK TRANSACTION TV4CreateItem;
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER PROCEDURE heritage.usp_UpdateHeritageItem
    @ActorUserId UNIQUEIDENTIFIER, @FamilyId UNIQUEIDENTIFIER, @Id UNIQUEIDENTIFIER,
    @ExpectedVersion VARCHAR(64), @Type NVARCHAR(MAX), @Title NVARCHAR(MAX),
    @Description NVARCHAR(MAX) = NULL, @Content NVARCHAR(MAX) = NULL, @MediaUrl NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Started BIT = CASE WHEN @@TRANCOUNT = 0 THEN 1 ELSE 0 END;
    BEGIN TRY
        IF @Started = 1 BEGIN TRANSACTION; ELSE SAVE TRANSACTION TV4UpdateItem;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId, @FamilyId;
        DECLARE @Owner UNIQUEIDENTIFIER;
        SELECT @Owner = CreatedByUserId FROM heritage.Items WITH (UPDLOCK, HOLDLOCK)
        WHERE Id = @Id AND FamilyId = @FamilyId;
        IF @Owner IS NULL THROW 51404, N'Item not found.', 1;
        IF @Owner <> @ActorUserId AND NOT EXISTS
            (SELECT 1 FROM core.Users WHERE UserId = @ActorUserId AND Role IN (N'admin', N'family_head'))
            THROW 51403, N'Only author or family manager may edit.', 1;
        IF @ExpectedVersion IS NULL OR NOT EXISTS
            (SELECT 1 FROM heritage.vw_HeritageItems WHERE Id = @Id AND VersionToken = @ExpectedVersion)
            THROW 51409, N'Item changed. Reload before editing.', 1;
        EXEC heritage.usp_ValidateHeritageItem @Type, @Title, @Description, @Content, @MediaUrl;
        -- TV5 owns synchronization; refuse edits of indexed sources until its hook exists.
        IF OBJECT_ID(N'heritage.KnowledgeChunks', N'U') IS NOT NULL
        BEGIN
            IF EXISTS (SELECT 1 FROM heritage.KnowledgeChunks WITH (HOLDLOCK)
                       WHERE SourceType=N'heritage' AND SourceId=@Id)
                THROW 51410, N'AI knowledge references this item. Coordinate with TV5.', 1;
        END;
        UPDATE heritage.Items SET Type = @Type, Title = @Title, Description = @Description,
            Content = @Content, MediaUrl = @MediaUrl WHERE Id = @Id AND FamilyId = @FamilyId;
        INSERT INTO reports.AuditLog (UserId, Action)
        VALUES (@ActorUserId, CONCAT(N'heritage.item.updated; id=', CONVERT(NVARCHAR(36), @Id)));
        SELECT * INTO #TV4UpdatedItem FROM heritage.vw_HeritageItems WHERE Id = @Id;
        IF @Started = 1 COMMIT TRANSACTION;
        SELECT * FROM #TV4UpdatedItem;
    END TRY
    BEGIN CATCH
        IF @Started = 1 AND XACT_STATE() <> 0 ROLLBACK TRANSACTION;
        ELSE IF XACT_STATE() = 1 ROLLBACK TRANSACTION TV4UpdateItem;
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER PROCEDURE heritage.usp_DeleteHeritageItem
    @ActorUserId UNIQUEIDENTIFIER, @FamilyId UNIQUEIDENTIFIER, @Id UNIQUEIDENTIFIER,
    @ExpectedVersion VARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Started BIT = CASE WHEN @@TRANCOUNT = 0 THEN 1 ELSE 0 END;
    BEGIN TRY
        IF @Started = 1 BEGIN TRANSACTION; ELSE SAVE TRANSACTION TV4DeleteItem;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId, @FamilyId;
        DECLARE @Owner UNIQUEIDENTIFIER;
        SELECT @Owner = CreatedByUserId FROM heritage.Items WITH (UPDLOCK, HOLDLOCK)
        WHERE Id = @Id AND FamilyId = @FamilyId;
        IF @Owner IS NULL THROW 51404, N'Item not found.', 1;
        IF @Owner <> @ActorUserId AND NOT EXISTS
            (SELECT 1 FROM core.Users WHERE UserId = @ActorUserId AND Role IN (N'admin', N'family_head'))
            THROW 51403, N'Only author or family manager may delete.', 1;
        IF @ExpectedVersion IS NULL OR NOT EXISTS
            (SELECT 1 FROM heritage.vw_HeritageItems WHERE Id = @Id AND VersionToken = @ExpectedVersion)
            THROW 51409, N'Item changed. Reload before deleting.', 1;
        -- KnowledgeChunks belongs to TV5. Do not edit it; refuse stale-source deletion.
        IF OBJECT_ID(N'heritage.KnowledgeChunks', N'U') IS NOT NULL
        BEGIN
            IF EXISTS (SELECT 1 FROM heritage.KnowledgeChunks WITH (HOLDLOCK)
                       WHERE SourceType = N'heritage' AND SourceId = @Id)
                THROW 51410, N'AI knowledge references this item. Coordinate with TV5.', 1;
        END;
        DELETE FROM heritage.Items WHERE Id = @Id AND FamilyId = @FamilyId;
        INSERT INTO reports.AuditLog (UserId, Action)
        VALUES (@ActorUserId, CONCAT(N'heritage.item.deleted; id=', CONVERT(NVARCHAR(36), @Id)));
        IF @Started = 1 COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @Started = 1 AND XACT_STATE() <> 0 ROLLBACK TRANSACTION;
        ELSE IF XACT_STATE() = 1 ROLLBACK TRANSACTION TV4DeleteItem;
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER PROCEDURE heritage.usp_GrantMemberHonor
    @ActorUserId UNIQUEIDENTIFIER, @FamilyId UNIQUEIDENTIFIER, @MemberId UNIQUEIDENTIFIER,
    @Title NVARCHAR(MAX), @Description NVARCHAR(MAX) = NULL, @DateAwarded DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Started BIT = CASE WHEN @@TRANCOUNT = 0 THEN 1 ELSE 0 END;
    DECLARE @Previous SQL_VARIANT = SESSION_CONTEXT(N'actor_user_id'), @Id UNIQUEIDENTIFIER = NEWID();
    BEGIN TRY
        IF @Started = 1 BEGIN TRANSACTION; ELSE SAVE TRANSACTION TV4GrantHonor;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId, @FamilyId, 1;
        IF NOT EXISTS (SELECT 1 FROM genealogy.Members WITH (HOLDLOCK) WHERE Id = @MemberId AND FamilyId = @FamilyId)
            THROW 51404, N'Member not found in family.', 1;
        IF NULLIF(LTRIM(RTRIM(@Title)), N'') IS NULL OR DATALENGTH(@Title) > 400 OR DATALENGTH(@Description) > 2000
            THROW 51422, N'Invalid honor payload.', 1;
        EXEC sys.sp_set_session_context @key=N'actor_user_id', @value=@ActorUserId;
        INSERT INTO heritage.Honors (Id, MemberId, Title, Description, DateAwarded)
        VALUES (@Id, @MemberId, @Title, @Description, @DateAwarded);
        EXEC sys.sp_set_session_context @key=N'actor_user_id', @value=@Previous;
        SELECT * INTO #TV4CreatedHonor FROM heritage.vw_Honors WHERE Id = @Id;
        IF @Started = 1 COMMIT TRANSACTION;
        SELECT * FROM #TV4CreatedHonor;
    END TRY
    BEGIN CATCH
        IF @Started = 1 AND XACT_STATE() <> 0 ROLLBACK TRANSACTION;
        ELSE IF XACT_STATE() = 1 ROLLBACK TRANSACTION TV4GrantHonor;
        EXEC sys.sp_set_session_context @key=N'actor_user_id', @value=@Previous;
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER PROCEDURE heritage.usp_UpdateMemberHonor
    @ActorUserId UNIQUEIDENTIFIER, @FamilyId UNIQUEIDENTIFIER, @Id UNIQUEIDENTIFIER,
    @ExpectedVersion VARCHAR(64), @Title NVARCHAR(MAX),
    @Description NVARCHAR(MAX) = NULL, @DateAwarded DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Started BIT = CASE WHEN @@TRANCOUNT = 0 THEN 1 ELSE 0 END;
    DECLARE @Previous SQL_VARIANT = SESSION_CONTEXT(N'actor_user_id');
    BEGIN TRY
        IF @Started = 1 BEGIN TRANSACTION; ELSE SAVE TRANSACTION TV4UpdateHonor;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId, @FamilyId, 1;
        IF NOT EXISTS (SELECT 1 FROM heritage.Honors h WITH (UPDLOCK, HOLDLOCK)
                       JOIN genealogy.Members m WITH (HOLDLOCK) ON m.Id=h.MemberId
                       WHERE h.Id=@Id AND m.FamilyId=@FamilyId)
            THROW 51404, N'Honor not found.', 1;
        IF @ExpectedVersion IS NULL OR NOT EXISTS
            (SELECT 1 FROM heritage.vw_Honors WHERE Id=@Id AND VersionToken=@ExpectedVersion)
            THROW 51409, N'Honor changed. Reload before editing.', 1;
        IF NULLIF(LTRIM(RTRIM(@Title)), N'') IS NULL OR DATALENGTH(@Title)>400 OR DATALENGTH(@Description)>2000
            THROW 51422, N'Invalid honor payload.', 1;
        EXEC sys.sp_set_session_context @key=N'actor_user_id', @value=@ActorUserId;
        UPDATE heritage.Honors SET Title=@Title, Description=@Description, DateAwarded=@DateAwarded WHERE Id=@Id;
        EXEC sys.sp_set_session_context @key=N'actor_user_id', @value=@Previous;
        SELECT * INTO #TV4UpdatedHonor FROM heritage.vw_Honors WHERE Id=@Id;
        IF @Started=1 COMMIT TRANSACTION;
        SELECT * FROM #TV4UpdatedHonor;
    END TRY
    BEGIN CATCH
        IF @Started=1 AND XACT_STATE()<>0 ROLLBACK TRANSACTION;
        ELSE IF XACT_STATE()=1 ROLLBACK TRANSACTION TV4UpdateHonor;
        EXEC sys.sp_set_session_context @key=N'actor_user_id', @value=@Previous;
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER PROCEDURE heritage.usp_DeleteMemberHonor
    @ActorUserId UNIQUEIDENTIFIER, @FamilyId UNIQUEIDENTIFIER, @Id UNIQUEIDENTIFIER,
    @ExpectedVersion VARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Started BIT = CASE WHEN @@TRANCOUNT=0 THEN 1 ELSE 0 END;
    DECLARE @Previous SQL_VARIANT = SESSION_CONTEXT(N'actor_user_id');
    BEGIN TRY
        IF @Started=1 BEGIN TRANSACTION; ELSE SAVE TRANSACTION TV4DeleteHonor;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId, @FamilyId, 1;
        IF NOT EXISTS (SELECT 1 FROM heritage.Honors h WITH (UPDLOCK,HOLDLOCK)
                       JOIN genealogy.Members m WITH (HOLDLOCK) ON m.Id=h.MemberId
                       WHERE h.Id=@Id AND m.FamilyId=@FamilyId)
            THROW 51404, N'Honor not found.', 1;
        IF @ExpectedVersion IS NULL OR NOT EXISTS
            (SELECT 1 FROM heritage.vw_Honors WHERE Id=@Id AND VersionToken=@ExpectedVersion)
            THROW 51409, N'Honor changed. Reload before deleting.', 1;
        EXEC sys.sp_set_session_context @key=N'actor_user_id', @value=@ActorUserId;
        DELETE FROM heritage.Honors WHERE Id=@Id;
        EXEC sys.sp_set_session_context @key=N'actor_user_id', @value=@Previous;
        IF @Started=1 COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @Started=1 AND XACT_STATE()<>0 ROLLBACK TRANSACTION;
        ELSE IF XACT_STATE()=1 ROLLBACK TRANSACTION TV4DeleteHonor;
        EXEC sys.sp_set_session_context @key=N'actor_user_id', @value=@Previous;
        THROW;
    END CATCH;
END;
GO
-- Only reads TV2 tables. Never creates/changes relationships or closure rows.
CREATE OR ALTER PROCEDURE heritage.usp_GetFamilyTreeJson
    @ActorUserId UNIQUEIDENTIFIER, @FamilyId UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Started BIT = CASE WHEN @@TRANCOUNT=0 THEN 1 ELSE 0 END;
    BEGIN TRY
      IF @Started=1 BEGIN TRANSACTION; ELSE SAVE TRANSACTION TV4ReadTree;
      EXEC heritage.usp_AssertFamilyAccess @ActorUserId, @FamilyId;
      -- Hold the selected members while materializing both edge sets.
      SELECT Id, FullName, BirthDate INTO #TV4TreeMembers
      FROM genealogy.Members WITH (HOLDLOCK) WHERE FamilyId=@FamilyId;
      DECLARE @TreeJson NVARCHAR(MAX) = (
        SELECT @FamilyId AS family_id,
            JSON_QUERY((SELECT Id AS id, FullName AS label, BirthDate AS birth_date
                        FROM #TV4TreeMembers ORDER BY BirthDate, Id FOR JSON PATH, INCLUDE_NULL_VALUES)) AS nodes,
            JSON_QUERY((SELECT edges.id, edges.source, edges.target, edges.kind FROM (
                SELECT CONCAT(N'parent-', CONVERT(NVARCHAR(36), pc.Id)) AS id,
                       pc.ParentId AS source, pc.ChildId AS target, N'parent_child' AS kind
                FROM genealogy.ParentChild pc WITH (HOLDLOCK)
                JOIN #TV4TreeMembers p ON p.Id=pc.ParentId JOIN #TV4TreeMembers c ON c.Id=pc.ChildId
                UNION ALL
                SELECT CONCAT(N'marriage-', CONVERT(NVARCHAR(36), r.Id)), r.Spouse1Id, r.Spouse2Id, N'marriage'
                FROM genealogy.Marriages r WITH (HOLDLOCK)
                JOIN #TV4TreeMembers a ON a.Id=r.Spouse1Id JOIN #TV4TreeMembers b ON b.Id=r.Spouse2Id
            ) edges ORDER BY edges.kind, edges.id FOR JSON PATH)) AS edges
        FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
      );
      IF @Started=1 COMMIT TRANSACTION;
      SELECT @TreeJson AS TreeJson;
    END TRY
    BEGIN CATCH
      IF @Started=1 AND XACT_STATE()<>0 ROLLBACK TRANSACTION;
      ELSE IF XACT_STATE()=1 ROLLBACK TRANSACTION TV4ReadTree;
      THROW;
    END CATCH;
END;
GO
