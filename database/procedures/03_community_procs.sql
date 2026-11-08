/* =====================================================================
   database/procedures/03_community_procs.sql
   TV3 - Cac thu tuc cho bang tin, cam xuc, su kien va nhac nho
   ===================================================================== */
USE [$(DB_NAME)];
GO

/* ---------------------------------------------------------------------
   1. usp_CreatePostWithMedia
   Tao bai viet + cac anh trong MOT giao tac. @MediaJson co dang:
   [{"url":"https://.../a.jpg","type":"image"},{"url":"https://.../b.jpg"}]
   --------------------------------------------------------------------- */
CREATE OR ALTER PROCEDURE [community].[usp_CreatePostWithMedia]
    @UserId    UNIQUEIDENTIFIER,
    @FamilyId  UNIQUEIDENTIFIER,
    @Content   NVARCHAR(MAX),
    @MediaJson NVARCHAR(MAX) = NULL,
    @PostId    UNIQUEIDENTIFIER OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF NOT EXISTS (SELECT 1 FROM [core].[Users] WHERE [UserId] = @UserId)
        THROW 50701, N'Nguoi dung khong ton tai.', 1;
    IF NOT EXISTS (SELECT 1 FROM [core].[Families] WHERE [Id] = @FamilyId)
        THROW 50702, N'Gia dinh khong ton tai.', 1;
    IF @MediaJson IS NOT NULL AND ISJSON(@MediaJson) = 0
        THROW 50703, N'MediaJson khong phai JSON hop le.', 1;

    BEGIN TRY
        BEGIN TRAN;

        DECLARE @NewPost TABLE ([Id] UNIQUEIDENTIFIER);

        INSERT INTO [community].[Posts] ([UserId], [FamilyId], [Content])
        OUTPUT inserted.[Id] INTO @NewPost
        VALUES (@UserId, @FamilyId, @Content);

        SELECT @PostId = [Id] FROM @NewPost;

        IF @MediaJson IS NOT NULL
            INSERT INTO [community].[PostMedia] ([PostId], [MediaUrl], [MediaType])
            SELECT @PostId, j.[MediaUrl], ISNULL(j.[MediaType], N'image')
            FROM OPENJSON(@MediaJson)
                 WITH ([MediaUrl]  NVARCHAR(2048) '$.url',
                       [MediaType] NVARCHAR(50)   '$.type') AS j
            WHERE j.[MediaUrl] IS NOT NULL AND LEN(j.[MediaUrl]) > 0;

        COMMIT TRAN;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRAN;
        THROW;
    END CATCH;
END;
GO

/* ---------------------------------------------------------------------
   2. usp_UpsertReaction
   Moi nguoi chi co 1 cam xuc tren moi bai: chua co thi them, co roi thi
   doi loai. Truyen @Type = NULL de go cam xuc.
   --------------------------------------------------------------------- */
CREATE OR ALTER PROCEDURE [community].[usp_UpsertReaction]
    @PostId UNIQUEIDENTIFIER,
    @UserId UNIQUEIDENTIFIER,
    @Type   NVARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF NOT EXISTS (SELECT 1 FROM [community].[Posts] WHERE [Id] = @PostId)
        THROW 50711, N'Bai viet khong ton tai.', 1;

    IF @Type IS NULL
    BEGIN
        DELETE FROM [community].[Reactions]
        WHERE [PostId] = @PostId AND [UserId] = @UserId;
        RETURN;
    END;

    MERGE [community].[Reactions] WITH (HOLDLOCK) AS tgt
    USING (SELECT @PostId AS [PostId], @UserId AS [UserId]) AS src
        ON tgt.[PostId] = src.[PostId] AND tgt.[UserId] = src.[UserId]
    WHEN MATCHED THEN
        UPDATE SET tgt.[Type] = @Type
    WHEN NOT MATCHED THEN
        INSERT ([PostId], [UserId], [Type])
        VALUES (@PostId, @UserId, @Type);
END;
GO

/* ---------------------------------------------------------------------
   3. usp_UpsertEventRsvp
   Them hoac cap nhat cau tra loi tham du (Pending/Going/Maybe/Declined).
   --------------------------------------------------------------------- */
CREATE OR ALTER PROCEDURE [community].[usp_UpsertEventRsvp]
    @EventId    UNIQUEIDENTIFIER,
    @MemberId   UNIQUEIDENTIFIER,
    @RsvpStatus NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF NOT EXISTS (SELECT 1 FROM [community].[Events] WHERE [Id] = @EventId)
        THROW 50721, N'Su kien khong ton tai.', 1;

    MERGE [community].[EventParticipants] WITH (HOLDLOCK) AS tgt
    USING (SELECT @EventId AS [EventId], @MemberId AS [MemberId]) AS src
        ON tgt.[EventId] = src.[EventId] AND tgt.[MemberId] = src.[MemberId]
    WHEN MATCHED THEN
        UPDATE SET tgt.[RsvpStatus] = @RsvpStatus
    WHEN NOT MATCHED THEN
        INSERT ([EventId], [MemberId], [RsvpStatus])
        VALUES (@EventId, @MemberId, @RsvpStatus);
END;
GO

/* ---------------------------------------------------------------------
   4. usp_ClaimDueReminders
   Worker goi moi phut. Lay toi da @BatchSize nhac nho da den han,
   danh dau 'sent' va tra ve ngay trong cung cau lenh. UPDLOCK + READPAST
   giup nhieu worker chay song song ma khong lay trung va khong cho nhau.
   Bang chi co trang thai pending/sent/failed/cancelled nen "claim" =
   chuyen sang 'sent'; worker neu gui loi thi cap nhat lai thanh 'failed'.
   --------------------------------------------------------------------- */
CREATE OR ALTER PROCEDURE [community].[usp_ClaimDueReminders]
    @BatchSize INT = 50
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    ;WITH due AS
    (
        SELECT TOP (@BatchSize) *
        FROM [community].[EventReminders] WITH (UPDLOCK, READPAST, ROWLOCK)
        WHERE [Status] = N'pending'
          AND [ReminderTime] <= SYSUTCDATETIME()
        ORDER BY [ReminderTime]
    )
    UPDATE due
    SET [Status] = N'sent'
    OUTPUT inserted.[Id], inserted.[EventId], inserted.[ReminderTime], inserted.[Status];
END;
GO
