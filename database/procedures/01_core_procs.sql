-- TV1: duyet xac minh va xu ly bao cao trong transaction.
USE [$(DB_NAME)];
GO
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- @ReviewerUserId phai lay tu JWT da xac thuc, khong nhan tu request body.
-- admin: toan he thong; family_head: chi thanh vien cung family va branch.
-- approved: gan tai khoan vao thanh vien, tu choi cac yeu cau pending canh tranh.
-- rejected: chi tu choi yeu cau duoc chon, khong thay doi lien ket thanh vien.
CREATE OR ALTER PROCEDURE [core].[usp_ReviewMemberVerification]
    @VerificationId UNIQUEIDENTIFIER,
    @ReviewerUserId UNIQUEIDENTIFIER,
    @Decision NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF @Decision IS NULL OR @Decision NOT IN (N'approved', N'rejected')
        THROW 51001, N'Decision phai la approved hoac rejected.', 1;

    DECLARE @StartedTransaction BIT = CASE WHEN @@TRANCOUNT = 0 THEN 1 ELSE 0 END;
    BEGIN TRY
        IF @StartedTransaction = 1 BEGIN TRANSACTION;
        ELSE SAVE TRANSACTION ReviewVerification;

        -- Cac lan duyet dung chung khoa de tranh hai admin duyet lien ket canh tranh.
        -- Khoa duoc giai phong cung transaction; khong can quyen DML truc tiep cho backend.
        DECLARE @LockResult INT;
        EXEC @LockResult = sys.sp_getapplock
            @Resource = N'core.usp_ReviewMemberVerification',
            @LockMode = N'Exclusive', @LockOwner = N'Transaction', @LockTimeout = 10000;
        IF @LockResult < 0 THROW 51002, N'Khong lay duoc khoa duyet xac minh. Hay thu lai.', 1;

        DECLARE @ReviewerRole NVARCHAR(20);
        SELECT @ReviewerRole = [Role]
        FROM [core].[Users] WITH (HOLDLOCK)
        WHERE [UserId] = @ReviewerUserId AND [IsActive] = 1;
        IF @ReviewerRole IS NULL OR @ReviewerRole NOT IN (N'admin', N'family_head')
            THROW 51003, N'Tai khoan khong co quyen duyet xac minh.', 1;

        DECLARE @UserId UNIQUEIDENTIFIER, @MemberId UNIQUEIDENTIFIER, @Status NVARCHAR(20);
        SELECT @UserId = [UserId], @MemberId = [MemberId], @Status = [Status]
        FROM [core].[MemberVerifications] WITH (UPDLOCK, HOLDLOCK)
        WHERE [Id] = @VerificationId;
        IF @UserId IS NULL THROW 51004, N'Khong tim thay yeu cau xac minh.', 1;
        IF @Status <> N'pending' THROW 51005, N'Yeu cau xac minh da duoc xu ly.', 1;

        DECLARE @FamilyId UNIQUEIDENTIFIER, @BranchId UNIQUEIDENTIFIER, @LinkedUserId UNIQUEIDENTIFIER;
        SELECT @FamilyId = [FamilyId], @BranchId = [BranchId], @LinkedUserId = [UserId]
        FROM [genealogy].[Members] WITH (UPDLOCK, HOLDLOCK)
        WHERE [Id] = @MemberId;
        IF @FamilyId IS NULL THROW 51006, N'Khong tim thay thanh vien gia pha.', 1;

        IF @ReviewerRole = N'family_head'
        BEGIN
            IF @ReviewerUserId = @UserId
                THROW 51007, N'Truong chi khong duoc tu duyet yeu cau cua minh.', 1;
            IF @BranchId IS NULL OR NOT EXISTS
            (
                SELECT 1
                FROM [genealogy].[Members] AS reviewer WITH (HOLDLOCK)
                INNER JOIN [core].[Branches] AS branch WITH (HOLDLOCK)
                    ON branch.[Id] = reviewer.[BranchId] AND branch.[FamilyId] = reviewer.[FamilyId]
                WHERE reviewer.[UserId] = @ReviewerUserId
                  AND reviewer.[FamilyId] = @FamilyId AND reviewer.[BranchId] = @BranchId
            )
                THROW 51008, N'Yeu cau khong thuoc chi do tai khoan nay quan ly.', 1;
        END;

        DECLARE @AutoRejectedCount INT = 0;
        IF @Decision = N'approved'
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM [core].[Users] WITH (UPDLOCK, HOLDLOCK)
                           WHERE [UserId] = @UserId AND [IsActive] = 1)
                THROW 51009, N'Khong the xac minh tai khoan da bi khoa.', 1;
            IF @LinkedUserId IS NOT NULL AND @LinkedUserId <> @UserId
                THROW 51010, N'Thanh vien da lien ket voi tai khoan khac.', 1;
            IF EXISTS (SELECT 1 FROM [genealogy].[Members] WITH (UPDLOCK, HOLDLOCK)
                       WHERE [UserId] = @UserId AND [Id] <> @MemberId)
                THROW 51011, N'Tai khoan da lien ket voi thanh vien khac.', 1;

            UPDATE [genealogy].[Members] SET [UserId] = @UserId WHERE [Id] = @MemberId;
            UPDATE [core].[MemberVerifications]
            SET [Status] = N'rejected'
            WHERE [Status] = N'pending' AND [Id] <> @VerificationId
              AND ([UserId] = @UserId OR [MemberId] = @MemberId);
            SET @AutoRejectedCount = @@ROWCOUNT;
        END;

        UPDATE [core].[MemberVerifications] SET [Status] = @Decision WHERE [Id] = @VerificationId;
        INSERT INTO [reports].[AuditLog] ([UserId], [Action])
        VALUES (@ReviewerUserId, CONCAT(N'verification.', @Decision,
            N'; request=', CONVERT(NVARCHAR(36), @VerificationId),
            N'; user=', CONVERT(NVARCHAR(36), @UserId),
            N'; member=', CONVERT(NVARCHAR(36), @MemberId),
            N'; auto_rejected=', @AutoRejectedCount));

        IF @StartedTransaction = 1 COMMIT TRANSACTION;
        SELECT @VerificationId AS [VerificationId], @Decision AS [Status],
               @AutoRejectedCount AS [AutoRejectedCount];
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
        BEGIN
            IF @StartedTransaction = 1 OR XACT_STATE() = -1 ROLLBACK TRANSACTION;
            ELSE ROLLBACK TRANSACTION ReviewVerification;
        END;
        THROW;
    END CATCH;
END;
GO

-- Chi admin dang hoat dong duoc xu ly bao cao.
-- Quy uoc photo = community.PostMedia (MediaType image hoac image/*).
-- dismissed: giu noi dung; resolved: xoa noi dung vi schema chua co co an bai.
-- Khi xoa post, cac comment/media/reaction bi cascade; dong bao cao lien quan
-- va xoa KnowledgeChunks cua post de tranh AI tiep tuc doc noi dung da go.
CREATE OR ALTER PROCEDURE [community].[usp_ResolveReportedContent]
    @ReportId UNIQUEIDENTIFIER,
    @ReviewerUserId UNIQUEIDENTIFIER,
    @Decision NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    IF @Decision IS NULL OR @Decision NOT IN (N'resolved', N'dismissed')
        THROW 51030, N'Decision phai la resolved hoac dismissed.', 1;

    DECLARE @StartedTransaction BIT = CASE WHEN @@TRANCOUNT = 0 THEN 1 ELSE 0 END;
    BEGIN TRY
        IF @StartedTransaction = 1 BEGIN TRANSACTION;
        ELSE SAVE TRANSACTION ResolveReport;

        DECLARE @LockResult INT;
        EXEC @LockResult = sys.sp_getapplock
            @Resource = N'community.usp_ResolveReportedContent',
            @LockMode = N'Exclusive', @LockOwner = N'Transaction', @LockTimeout = 10000;
        IF @LockResult < 0 THROW 51031, N'Khong lay duoc khoa xu ly bao cao. Hay thu lai.', 1;

        IF NOT EXISTS (SELECT 1 FROM [core].[Users] WITH (HOLDLOCK)
                       WHERE [UserId] = @ReviewerUserId AND [Role] = N'admin' AND [IsActive] = 1)
            THROW 51032, N'Chi admin dang hoat dong duoc xu ly bao cao.', 1;

        DECLARE @TargetId UNIQUEIDENTIFIER, @TargetType NVARCHAR(50), @Status NVARCHAR(20);
        SELECT @TargetId = [TargetId], @TargetType = [TargetType], @Status = [Status]
        FROM [community].[ReportedContents] WITH (UPDLOCK, HOLDLOCK) WHERE [Id] = @ReportId;
        IF @TargetId IS NULL THROW 51033, N'Khong tim thay bao cao.', 1;
        IF @Status <> N'pending' THROW 51034, N'Bao cao da duoc xu ly.', 1;

        DECLARE @AffectedTargets TABLE ([TargetId] UNIQUEIDENTIFIER, [TargetType] NVARCHAR(50),
                                       PRIMARY KEY ([TargetId], [TargetType]));
        INSERT INTO @AffectedTargets VALUES (@TargetId, @TargetType);
        DECLARE @DeletedCount INT = 0, @ResolvedReportCount INT = 0;

        IF @Decision = N'resolved'
        BEGIN
            IF @TargetType = N'post'
            BEGIN
                -- Khoa post va con truoc khi thu thap danh sach cascade.
                IF NOT EXISTS (SELECT 1 FROM [community].[Posts] WITH (XLOCK, HOLDLOCK) WHERE [Id] = @TargetId)
                    THROW 51035, N'Bai viet bi bao cao khong con ton tai.', 1;
                INSERT INTO @AffectedTargets
                    SELECT [Id], N'comment' FROM [community].[Comments] WITH (UPDLOCK, HOLDLOCK) WHERE [PostId] = @TargetId
                    UNION ALL
                    SELECT [Id], N'photo' FROM [community].[PostMedia] WITH (UPDLOCK, HOLDLOCK) WHERE [PostId] = @TargetId;
                DELETE FROM [heritage].[KnowledgeChunks] WHERE [SourceType] = N'post' AND [SourceId] = @TargetId;
                DELETE FROM [community].[Posts] WHERE [Id] = @TargetId;
                SET @DeletedCount = @@ROWCOUNT;
            END
            ELSE IF @TargetType = N'comment'
            BEGIN
                DELETE FROM [community].[Comments] WHERE [Id] = @TargetId;
                SET @DeletedCount = @@ROWCOUNT;
            END
            ELSE IF @TargetType = N'photo'
            BEGIN
                DELETE FROM [community].[PostMedia]
                WHERE [Id] = @TargetId AND ([MediaType] = N'image' OR [MediaType] LIKE N'image/%');
                SET @DeletedCount = @@ROWCOUNT;
            END;
            IF @DeletedCount = 0
                THROW 51036, N'Khong tim thay noi dung phu hop. Photo chi ho tro anh PostMedia.', 1;

            -- Nhieu nguoi co the bao cao cung noi dung; dong tat ca bao cao pending bi anh huong.
            UPDATE report SET [Status] = N'resolved'
            FROM [community].[ReportedContents] AS report
            INNER JOIN @AffectedTargets AS target
                ON target.[TargetId] = report.[TargetId] AND target.[TargetType] = report.[TargetType]
            WHERE report.[Status] = N'pending';
            SET @ResolvedReportCount = @@ROWCOUNT;
        END
        ELSE
            UPDATE [community].[ReportedContents] SET [Status] = N'dismissed' WHERE [Id] = @ReportId;

        INSERT INTO [reports].[AuditLog] ([UserId], [Action])
        VALUES (@ReviewerUserId, CONCAT(N'report.', @Decision,
            N'; report=', CONVERT(NVARCHAR(36), @ReportId),
            N'; type=', @TargetType, N'; target=', CONVERT(NVARCHAR(36), @TargetId),
            N'; resolved_reports=', @ResolvedReportCount));

        IF @StartedTransaction = 1 COMMIT TRANSACTION;
        SELECT @ReportId AS [ReportId], @Decision AS [Status], @DeletedCount AS [DeletedTargetCount],
               @ResolvedReportCount AS [ResolvedReportCount];
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
        BEGIN
            IF @StartedTransaction = 1 OR XACT_STATE() = -1 ROLLBACK TRANSACTION;
            ELSE ROLLBACK TRANSACTION ResolveReport;
        END;
        THROW;
    END CATCH;
END;
GO
