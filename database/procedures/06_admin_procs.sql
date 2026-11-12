-- TV1 task 6: quan tri cau hinh va danh sach xac minh theo pham vi chi.
-- Nguoi thuc hien phai lay tu JWT da xac thuc o backend.
USE [$(DB_NAME)];
GO
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

CREATE OR ALTER PROCEDURE [core].[usp_CreateSystemConfig]
    @ActorUserId UNIQUEIDENTIFIER,
    @ConfigKey NVARCHAR(4000),
    @ConfigValue NVARCHAR(MAX),
    @Description NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF @ConfigKey IS NULL OR DATALENGTH(@ConfigKey) = 0 OR DATALENGTH(@ConfigKey) > 200
       OR @ConfigKey COLLATE Latin1_General_100_BIN2 LIKE N'%[^A-Za-z0-9_.-]%'
        THROW 51101, N'ConfigKey chi gom chu ASCII, so, dau cham, gach duoi va gach ngang; toi da 100 ky tu.', 1;
    IF @ConfigValue IS NULL OR DATALENGTH(@Description) > 1000
        THROW 51101, N'ConfigValue khong duoc NULL; Description toi da 500 don vi UTF-16.', 1;

    DECLARE @StartedTransaction BIT = CASE WHEN @@TRANCOUNT = 0 THEN 1 ELSE 0 END;
    BEGIN TRY
        IF @StartedTransaction = 1 BEGIN TRANSACTION;
        ELSE SAVE TRANSACTION CreateSystemConfig;

        IF NOT EXISTS (SELECT 1 FROM [core].[Users] WITH (HOLDLOCK)
                       WHERE [UserId] = @ActorUserId AND [Role] = N'admin' AND [IsActive] = 1)
            THROW 51102, N'Chi admin dang hoat dong duoc quan ly cau hinh.', 1;

        IF EXISTS (SELECT 1 FROM [core].[SystemConfigs] WITH (UPDLOCK, HOLDLOCK)
                       WHERE [ConfigKey] = CONVERT(VARCHAR(100), @ConfigKey))
            THROW 51103, N'Khoa cau hinh da ton tai.', 1;

        INSERT INTO [core].[SystemConfigs] ([ConfigKey], [ConfigValue], [Description])
        VALUES (CONVERT(VARCHAR(100), @ConfigKey), @ConfigValue, @Description);

        INSERT INTO [reports].[AuditLog] ([UserId], [Action])
        VALUES (@ActorUserId, CONCAT(N'system_config.created; key=', @ConfigKey));

        -- SELECT sau DML de lay UpdatedAt do AFTER UPDATE trigger thiet lap.
        DECLARE @Result TABLE ([ConfigKey] VARCHAR(100), [ConfigValue] NVARCHAR(MAX),
                               [Description] NVARCHAR(500), [UpdatedAt] DATETIME2(0));
        INSERT INTO @Result
        SELECT [ConfigKey], [ConfigValue], [Description], [UpdatedAt]
        FROM [core].[SystemConfigs] WHERE [ConfigKey] = CONVERT(VARCHAR(100), @ConfigKey);

        IF @StartedTransaction = 1 COMMIT TRANSACTION;
        SELECT [ConfigKey], [ConfigValue], [Description], [UpdatedAt] FROM @Result;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
        BEGIN
            IF @StartedTransaction = 1 OR XACT_STATE() = -1 ROLLBACK TRANSACTION;
            ELSE ROLLBACK TRANSACTION CreateSystemConfig;
        END;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE [core].[usp_UpdateSystemConfig]
    @ActorUserId UNIQUEIDENTIFIER,
    @ConfigKey NVARCHAR(4000),
    @ConfigValue NVARCHAR(MAX),
    @Description NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF @ConfigKey IS NULL OR DATALENGTH(@ConfigKey) = 0 OR DATALENGTH(@ConfigKey) > 200
       OR @ConfigKey COLLATE Latin1_General_100_BIN2 LIKE N'%[^A-Za-z0-9_.-]%'
        THROW 51101, N'ConfigKey chi gom chu ASCII, so, dau cham, gach duoi va gach ngang; toi da 100 ky tu.', 1;
    IF @ConfigValue IS NULL OR DATALENGTH(@Description) > 1000
        THROW 51101, N'ConfigValue khong duoc NULL; Description toi da 500 don vi UTF-16.', 1;

    DECLARE @StartedTransaction BIT = CASE WHEN @@TRANCOUNT = 0 THEN 1 ELSE 0 END;
    BEGIN TRY
        IF @StartedTransaction = 1 BEGIN TRANSACTION;
        ELSE SAVE TRANSACTION UpdateSystemConfig;

        IF NOT EXISTS (SELECT 1 FROM [core].[Users] WITH (HOLDLOCK)
                       WHERE [UserId] = @ActorUserId AND [Role] = N'admin' AND [IsActive] = 1)
            THROW 51102, N'Chi admin dang hoat dong duoc quan ly cau hinh.', 1;

        IF NOT EXISTS (SELECT 1 FROM [core].[SystemConfigs] WITH (UPDLOCK, HOLDLOCK)
                       WHERE [ConfigKey] = CONVERT(VARCHAR(100), @ConfigKey))
            THROW 51104, N'Khong tim thay cau hinh.', 1;

        UPDATE [core].[SystemConfigs]
        SET [ConfigValue] = @ConfigValue, [Description] = @Description
        WHERE [ConfigKey] = CONVERT(VARCHAR(100), @ConfigKey);

        INSERT INTO [reports].[AuditLog] ([UserId], [Action])
        VALUES (@ActorUserId, CONCAT(N'system_config.updated; key=', @ConfigKey));

        -- SELECT sau DML de lay UpdatedAt do AFTER UPDATE trigger thiet lap.
        DECLARE @Result TABLE ([ConfigKey] VARCHAR(100), [ConfigValue] NVARCHAR(MAX),
                               [Description] NVARCHAR(500), [UpdatedAt] DATETIME2(0));
        INSERT INTO @Result
        SELECT [ConfigKey], [ConfigValue], [Description], [UpdatedAt]
        FROM [core].[SystemConfigs] WHERE [ConfigKey] = CONVERT(VARCHAR(100), @ConfigKey);

        IF @StartedTransaction = 1 COMMIT TRANSACTION;
        SELECT [ConfigKey], [ConfigValue], [Description], [UpdatedAt] FROM @Result;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
        BEGIN
            IF @StartedTransaction = 1 OR XACT_STATE() = -1 ROLLBACK TRANSACTION;
            ELSE ROLLBACK TRANSACTION UpdateSystemConfig;
        END;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE [core].[usp_DeleteSystemConfig]
    @ActorUserId UNIQUEIDENTIFIER,
    @ConfigKey NVARCHAR(4000)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF @ConfigKey IS NULL OR DATALENGTH(@ConfigKey) = 0 OR DATALENGTH(@ConfigKey) > 200
       OR @ConfigKey COLLATE Latin1_General_100_BIN2 LIKE N'%[^A-Za-z0-9_.-]%'
        THROW 51101, N'ConfigKey chi gom chu ASCII, so, dau cham, gach duoi va gach ngang; toi da 100 ky tu.', 1;

    DECLARE @StartedTransaction BIT = CASE WHEN @@TRANCOUNT = 0 THEN 1 ELSE 0 END;
    BEGIN TRY
        IF @StartedTransaction = 1 BEGIN TRANSACTION;
        ELSE SAVE TRANSACTION DeleteSystemConfig;

        IF NOT EXISTS (SELECT 1 FROM [core].[Users] WITH (HOLDLOCK)
                       WHERE [UserId] = @ActorUserId AND [Role] = N'admin' AND [IsActive] = 1)
            THROW 51102, N'Chi admin dang hoat dong duoc quan ly cau hinh.', 1;

        IF NOT EXISTS (SELECT 1 FROM [core].[SystemConfigs] WITH (UPDLOCK, HOLDLOCK)
                       WHERE [ConfigKey] = CONVERT(VARCHAR(100), @ConfigKey))
            THROW 51104, N'Khong tim thay cau hinh.', 1;

        DELETE FROM [core].[SystemConfigs]
        WHERE [ConfigKey] = CONVERT(VARCHAR(100), @ConfigKey);

        INSERT INTO [reports].[AuditLog] ([UserId], [Action])
        VALUES (@ActorUserId, CONCAT(N'system_config.deleted; key=', @ConfigKey));

        IF @StartedTransaction = 1 COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
        BEGIN
            IF @StartedTransaction = 1 OR XACT_STATE() = -1 ROLLBACK TRANSACTION;
            ELSE ROLLBACK TRANSACTION DeleteSystemConfig;
        END;
        THROW;
    END CATCH;
END;
GO

-- Admin xem toan bo; family_head chi xem cung family/branch va khong tu duyet.
CREATE OR ALTER PROCEDURE [core].[usp_GetPendingVerifications]
    @ReviewerUserId UNIQUEIDENTIFIER,
    @Limit INT = 50,
    @Offset INT = 0
AS
BEGIN
    SET NOCOUNT ON;
    IF @Limit IS NULL OR @Limit < 1 OR @Limit > 200 OR @Offset IS NULL OR @Offset < 0
        THROW 51101, N'Limit phai tu 1 den 200; Offset khong am.', 1;

    DECLARE @ReviewerRole NVARCHAR(20);
    SELECT @ReviewerRole = [Role] FROM [core].[Users]
    WHERE [UserId] = @ReviewerUserId AND [IsActive] = 1;
    IF @ReviewerRole IS NULL OR @ReviewerRole NOT IN (N'admin', N'family_head')
        THROW 51102, N'Tai khoan khong co quyen xem yeu cau xac minh.', 1;

    SELECT pending.[VerificationId], pending.[UserId], pending.[UserFullName],
           pending.[UserEmail], pending.[UserIsActive], pending.[MemberId],
           pending.[MemberFullName], pending.[BirthDate], pending.[FamilyId],
           pending.[FamilyName], pending.[BranchId], pending.[BranchName],
           pending.[LinkedUserId], pending.[Status], pending.[RequestedAt]
    FROM [core].[vw_PendingVerifications] AS pending
    WHERE @ReviewerRole = N'admin'
       OR (pending.[UserId] <> @ReviewerUserId AND EXISTS
           (SELECT 1 FROM [genealogy].[Members] AS reviewer
            INNER JOIN [core].[Branches] AS branch
                ON branch.[Id] = reviewer.[BranchId] AND branch.[FamilyId] = reviewer.[FamilyId]
            WHERE reviewer.[UserId] = @ReviewerUserId
              AND reviewer.[FamilyId] = pending.[FamilyId]
              AND reviewer.[BranchId] = pending.[BranchId]))
    ORDER BY pending.[RequestedAt], pending.[VerificationId]
    OFFSET @Offset ROWS FETCH NEXT @Limit ROWS ONLY;
END;
GO
