/*
    KIEM THU TASK 3 - (T-SQL / SSMS)
    Moi lan chay, doi @Mode ben duoi thanh mot trong cac gia tri:
      SETUP   : tao FamilyConnect_Task3Test (database rong, dung rieng cho test).
      TEST    : kiem thu View, SP, Trigger, phan quyen, audit va rollback.
      TAB_A   : phien duyet thu nhat; giu transaction 10 giay.
      TAB_B   : phien duyet thu hai; chay o tab khac trong luc TAB_A dang cho.
      CLEANUP : xoa database thu sau khi kiem tra xong.

    Thu tu:
      1. Chay SETUP.
      2. Nap cac file .sql trong database/schema/ theo thu tu ten va 3 file SQL task 3
         (views/01_core_views.sql, procedures/01_core_procs.sql,
          triggers/01_core_triggers.sql), dung DB_NAME=FamilyConnect_Task3Test.
         Khong nap seed hoac shared/06_permissions.sql. Xem README.md.
      3. Doi sang TEST va Execute toan bo file.
      4. Mo cung file trong hai tab SSMS; TAB_A truoc, TAB_B trong 10 giay cho.
      5. Doi sang CLEANUP va Execute toan bo file.
    Khong boc ca file trong transaction. Database FamilyConnect khong bi thay doi.
*/
USE [master];
GO
SET NOCOUNT ON;

DECLARE @Mode VARCHAR(12) = 'SETUP'; -- SETUP | TEST | TAB_A | TAB_B | CLEANUP
SET @Mode = UPPER(LTRIM(RTRIM(@Mode)));

DROP TABLE IF EXISTS #Task3Run;
CREATE TABLE #Task3Run ([Mode] VARCHAR(12) NOT NULL);
INSERT INTO #Task3Run VALUES (@Mode);

BEGIN TRY
    IF @Mode IS NULL OR @Mode NOT IN ('SETUP', 'TEST', 'TAB_A', 'TAB_B', 'CLEANUP')
        THROW 51910, N'Mode phai la SETUP, TEST, TAB_A, TAB_B hoac CLEANUP.', 1;

    IF @Mode = 'SETUP'
    BEGIN
        IF DB_ID(N'FamilyConnect_Task3Test') IS NOT NULL
            THROW 51910, N'Database thu da ton tai. Chon CLEANUP truoc khi SETUP lai.', 1;
        CREATE DATABASE [FamilyConnect_Task3Test];
        EXEC [FamilyConnect_Task3Test].sys.sp_addextendedproperty
            @name = N'FamilyConnect.Task3Test', @value = N'1';
        ALTER DATABASE [FamilyConnect_Task3Test] SET RECURSIVE_TRIGGERS ON;
        PRINT N'SETUP: da tao database thu. Nap schema va 3 file SQL task 3, sau do chon TEST.';
    END
    ELSE
    BEGIN
        IF DB_ID(N'FamilyConnect_Task3Test') IS NULL
            THROW 51910, N'Chua co database thu. Chon SETUP va nap cac file SQL truoc.', 1;

        DECLARE @IsTestDatabase BIT = 0;
        EXEC [FamilyConnect_Task3Test].sys.sp_executesql
            N'SELECT @Marked = 1 FROM sys.extended_properties
              WHERE class = 0 AND name = N''FamilyConnect.Task3Test'' AND CONVERT(NVARCHAR(10), value) = N''1'';',
            N'@Marked BIT OUTPUT', @Marked = @IsTestDatabase OUTPUT;
        IF @IsTestDatabase <> 1
            THROW 51910, N'Database khong thuoc bo test task 3. Dung thuc thi.', 1;
    END;
END TRY
BEGIN CATCH
    -- Chan cac batch sau neu dieu kien dau vao sai; reset NOEXEC o cuoi file.
    SET NOEXEC ON;
    THROW;
END CATCH;
GO

USE [FamilyConnect_Task3Test];
GO
CREATE OR ALTER PROCEDURE #ExpectError @Statement NVARCHAR(MAX), @ExpectedNumber INT
AS
BEGIN
    DECLARE @ActualNumber INT;
    BEGIN TRY
        EXEC sys.sp_executesql @Statement;
    END TRY
    BEGIN CATCH
        SET @ActualNumber = ERROR_NUMBER();
    END CATCH;
    IF @ActualNumber IS NULL OR @ActualNumber <> @ExpectedNumber
    BEGIN
        DECLARE @Message NVARCHAR(2048) = CONCAT(N'Expected error ', @ExpectedNumber, N'; got ', COALESCE(CONVERT(VARCHAR(20), @ActualNumber), 'success'));
        THROW 51900, @Message, 1;
    END;
END;
GO

DECLARE @Mode VARCHAR(12) = (SELECT [Mode] FROM #Task3Run);

BEGIN TRY
    IF @Mode = 'TEST'
    BEGIN
        IF OBJECT_ID(N'core.Users', N'U') IS NULL
           OR OBJECT_ID(N'heritage.KnowledgeChunks', N'U') IS NULL
           OR OBJECT_ID(N'core.vw_PendingVerifications', N'V') IS NULL
           OR OBJECT_ID(N'core.usp_ReviewMemberVerification', N'P') IS NULL
           OR OBJECT_ID(N'community.usp_ResolveReportedContent', N'P') IS NULL
           OR OBJECT_ID(N'core.trg_Users_AuditRoleAndStatus', N'TR') IS NULL
           OR OBJECT_ID(N'core.trg_SystemConfigs_UpdatedAt', N'TR') IS NULL
            THROW 51910, N'Thieu schema hoac doi tuong task 3. Nap cac file SQL theo README truoc.', 1;
        IF EXISTS (SELECT 1 FROM core.Users) OR EXISTS (SELECT 1 FROM core.Families)
            THROW 51910, N'Database thu phai rong. Chay CLEANUP, SETUP va nap lai SQL; khong nap seed.', 1;

        INSERT core.Users (UserId, Email, PasswordHash, FullName, Role, IsActive)
        VALUES
        ('00000000-0000-0000-0000-000000000001', 'admin@test.invalid', 'test', N'Admin', 'admin', 1),
        ('00000000-0000-0000-0000-000000000002', 'head@test.invalid', 'test', N'Head', 'family_head', 1),
        ('00000000-0000-0000-0000-000000000003', 'applicant@test.invalid', 'test', N'Applicant', 'member', 1),
        ('00000000-0000-0000-0000-000000000004', 'competitor@test.invalid', 'test', N'Competitor', 'member', 1),
        ('00000000-0000-0000-0000-000000000005', 'member@test.invalid', 'test', N'Member', 'member', 1),
        ('00000000-0000-0000-0000-000000000006', 'inactive-admin@test.invalid', 'test', N'Inactive admin', 'admin', 0),
        ('00000000-0000-0000-0000-000000000007', 'inactive@test.invalid', 'test', N'Inactive applicant', 'member', 0),
        ('00000000-0000-0000-0000-000000000008', 'race1@test.invalid', 'test', N'Race 1', 'member', 1),
        ('00000000-0000-0000-0000-000000000009', 'race2@test.invalid', 'test', N'Race 2', 'member', 1);
        INSERT core.Families (Id, Name) VALUES ('20000000-0000-0000-0000-000000000001', N'Test family');
        INSERT core.Branches (Id, FamilyId, Name) VALUES
        ('30000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', N'Branch A'),
        ('30000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000001', N'Branch B');
        INSERT genealogy.Members (Id, FamilyId, BranchId, UserId, FullName) VALUES
        ('10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000001', NULL, N'Target'),
        ('10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', N'Head'),
        ('10000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000001', NULL, N'Alternative'),
        ('10000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000002', NULL, N'Other branch'),
        ('10000000-0000-0000-0000-000000000005', '20000000-0000-0000-0000-000000000001', NULL, NULL, N'No branch'),
        ('10000000-0000-0000-0000-000000000006', '20000000-0000-0000-0000-000000000001', NULL, '00000000-0000-0000-0000-000000000005', N'Already linked'),
        ('10000000-0000-0000-0000-000000000020', '20000000-0000-0000-0000-000000000001', NULL, NULL, N'Race target');
        INSERT core.MemberVerifications (Id, UserId, MemberId) VALUES
        ('40000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000001'),
        ('40000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000001'),
        ('40000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000003'),
        ('40000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000004'),
        ('40000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000007', '10000000-0000-0000-0000-000000000005');

        IF (SELECT COUNT(*) FROM core.vw_PendingVerifications) <> 5 OR
           NOT EXISTS (SELECT 1 FROM core.vw_PendingVerifications WHERE BranchId IS NULL AND UserEmail = 'inactive@test.invalid')
            THROW 51900, N'Pending view must include joined information and members without a branch.', 1;

        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000001'', ''00000000-0000-0000-0000-000000000001'', N''pending'';', 51001;
        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000001'', ''00000000-0000-0000-0000-000000000005'', N''approved'';', 51003;
        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000001'', ''00000000-0000-0000-0000-000000000006'', N''approved'';', 51003;
        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000099'', ''00000000-0000-0000-0000-000000000001'', N''approved'';', 51004;
        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000004'', ''00000000-0000-0000-0000-000000000002'', N''approved'';', 51008;
        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000005'', ''00000000-0000-0000-0000-000000000002'', N''approved'';', 51008;
        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000005'', ''00000000-0000-0000-0000-000000000001'', N''approved'';', 51009;

        -- Match production backend grants: SELECT/EXECUTE, no direct member/request mutation.
        CREATE USER task3_backend WITHOUT LOGIN;
        GRANT SELECT, EXECUTE ON SCHEMA::core TO task3_backend;
        GRANT SELECT, EXECUTE ON SCHEMA::community TO task3_backend;
        GRANT SELECT ON SCHEMA::genealogy TO task3_backend;
        EXECUTE AS USER = 'task3_backend';
        IF HAS_PERMS_BY_NAME('genealogy.Members', 'OBJECT', 'UPDATE') <> 0
            THROW 51900, N'Backend fixture unexpectedly has direct UPDATE rights.', 1;
        EXEC core.usp_ReviewMemberVerification '40000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', N'approved';
        REVERT;
        IF NOT EXISTS (SELECT 1 FROM genealogy.Members WHERE Id = '10000000-0000-0000-0000-000000000001' AND UserId = '00000000-0000-0000-0000-000000000003')
           OR (SELECT COUNT(*) FROM core.MemberVerifications WHERE Id IN ('40000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000003') AND Status = 'rejected') <> 2
           OR (SELECT COUNT(*) FROM core.vw_PendingVerifications) <> 2
            THROW 51900, N'Approval must link user, reject both kinds of competing request and leave the pending view.', 1;
        IF NOT EXISTS (SELECT 1 FROM reports.AuditLog WHERE UserId = '00000000-0000-0000-0000-000000000002' AND Action LIKE 'verification.approved%; auto_rejected=2')
            THROW 51900, N'Approval audit must identify the reviewer and competing request count.', 1;
        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000001'', ''00000000-0000-0000-0000-000000000001'', N''approved'';', 51005;
        EXEC core.usp_ReviewMemberVerification '40000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001', N'rejected';
        IF EXISTS (SELECT 1 FROM genealogy.Members WHERE Id = '10000000-0000-0000-0000-000000000004' AND UserId IS NOT NULL)
            THROW 51900, N'Rejection must not link a member.', 1;

        -- Reject attempts to claim an occupied member or link an account twice.
        INSERT core.MemberVerifications (Id, UserId, MemberId) VALUES
        ('40000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000006'),
        ('40000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000005', '10000000-0000-0000-0000-000000000003'),
        ('40000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000003');
        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000006'', ''00000000-0000-0000-0000-000000000001'', N''approved'';', 51010;
        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000007'', ''00000000-0000-0000-0000-000000000001'', N''approved'';', 51011;
        -- Inject an audit failure to prove linkage and request changes roll back together.
        EXEC sys.sp_executesql N'CREATE TRIGGER reports.task3_FailAudit ON reports.AuditLog AFTER INSERT AS
        BEGIN
            THROW 51901, N''Injected audit failure.'', 1;
        END;';
        EXEC #ExpectError N'EXEC core.usp_ReviewMemberVerification ''40000000-0000-0000-0000-000000000008'', ''00000000-0000-0000-0000-000000000001'', N''approved'';', 51901;
        IF NOT EXISTS (SELECT 1 FROM core.MemberVerifications WHERE Id = '40000000-0000-0000-0000-000000000008' AND Status = 'pending')
           OR EXISTS (SELECT 1 FROM genealogy.Members WHERE Id = '10000000-0000-0000-0000-000000000003' AND UserId IS NOT NULL)
            THROW 51900, N'Audit failure must roll back verification and linkage.', 1;
        DROP TRIGGER reports.task3_FailAudit;

        -- Trigger: set-based audit, no audit on unrelated/no-op changes, correct actor.
        DECLARE @BeforeAudit INT = (SELECT COUNT(*) FROM reports.AuditLog);
        UPDATE core.Users SET FullName = FullName;
        UPDATE core.Users SET Role = Role;
        IF (SELECT COUNT(*) FROM reports.AuditLog) <> @BeforeAudit
            THROW 51900, N'Unrelated/no-op user updates must not generate audit rows.', 1;
        EXEC sys.sp_set_session_context @key = N'actor_user_id', @value = N'00000000-0000-0000-0000-000000000001';
        UPDATE core.Users SET Role = N'guest' WHERE UserId IN ('00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000009');
        IF (SELECT COUNT(*) FROM reports.AuditLog WHERE Action LIKE 'users.role_status_changed%' AND UserId = '00000000-0000-0000-0000-000000000001') <> 2
            THROW 51900, N'Bulk user updates must audit each changed row under the actor.', 1;
        EXEC sys.sp_set_session_context @key = N'actor_user_id', @value = NULL;
        UPDATE core.Users SET IsActive = 0 WHERE UserId = '00000000-0000-0000-0000-000000000009';
        IF NOT EXISTS (SELECT 1 FROM reports.AuditLog WHERE UserId IS NULL AND Action LIKE 'users.role_status_changed; target=00000000-0000-0000-0000-000000000009%active=1->0%')
            THROW 51900, N'Direct SQL user update must not misattribute the target as the actor.', 1;
        EXEC sys.sp_set_session_context @key = N'actor_user_id', @value = N'not-a-uuid';
        EXEC #ExpectError N'UPDATE core.Users SET IsActive = 0 WHERE UserId = ''00000000-0000-0000-0000-000000000008'';', 51021;
        IF NOT EXISTS (SELECT 1 FROM core.Users WHERE UserId = '00000000-0000-0000-0000-000000000008' AND IsActive = 1)
            THROW 51900, N'Invalid actor must roll back user update.', 1;
        EXEC sys.sp_set_session_context @key = N'actor_user_id', @value = NULL;
        UPDATE core.Users SET Role = 'member', IsActive = 1 WHERE UserId IN ('00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000009');

        INSERT core.SystemConfigs (ConfigKey, ConfigValue, UpdatedAt) VALUES ('test.a', 'old', '20000101'), ('test.b', 'old', '20000101');
        UPDATE core.SystemConfigs SET ConfigValue = 'new', UpdatedAt = '20000101';
        IF (SELECT COUNT(*) FROM core.SystemConfigs WHERE ConfigValue = 'new' AND UpdatedAt >= DATEADD(SECOND, -5, SYSUTCDATETIME())) <> 2
            THROW 51900, N'Config timestamp trigger must handle multiple rows and recursive triggers.', 1;

        -- Moderation fixtures: post with children and AI chunks, plus a retained post.
        INSERT community.Posts (Id, UserId, FamilyId, Content) VALUES
        ('50000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000001', N'Reported post'),
        ('50000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000001', N'Retained post');
        INSERT community.Comments (Id, PostId, UserId, Content) VALUES
        ('60000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', N'Cascade comment'),
        ('60000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003', N'Reported comment');
        INSERT community.PostMedia (Id, PostId, MediaUrl) VALUES
        ('70000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', N'https://test.invalid/cascade.jpg'),
        ('70000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000002', N'https://test.invalid/reported.jpg');
        INSERT community.Reactions (PostId, UserId, Type) VALUES ('50000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 'Like');
        INSERT heritage.KnowledgeChunks (FamilyId, SourceType, SourceId, ChunkText) VALUES ('20000000-0000-0000-0000-000000000001', 'post', '50000000-0000-0000-0000-000000000001', N'Stale content');
        INSERT community.ReportedContents (Id, TargetId, TargetType, ReportedBy, Reason) VALUES
        ('80000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'post', '00000000-0000-0000-0000-000000000003', N'test'),
        ('80000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000001', 'post', '00000000-0000-0000-0000-000000000004', N'test'),
        ('80000000-0000-0000-0000-000000000003', '60000000-0000-0000-0000-000000000001', 'comment', '00000000-0000-0000-0000-000000000003', N'test'),
        ('80000000-0000-0000-0000-000000000004', '70000000-0000-0000-0000-000000000001', 'photo', '00000000-0000-0000-0000-000000000003', N'test'),
        ('80000000-0000-0000-0000-000000000005', '50000000-0000-0000-0000-000000000002', 'post', '00000000-0000-0000-0000-000000000003', N'test'),
        ('80000000-0000-0000-0000-000000000006', '60000000-0000-0000-0000-000000000002', 'comment', '00000000-0000-0000-0000-000000000003', N'test'),
        ('80000000-0000-0000-0000-000000000007', '70000000-0000-0000-0000-000000000002', 'photo', '00000000-0000-0000-0000-000000000003', N'test'),
        ('80000000-0000-0000-0000-000000000008', '50000000-0000-0000-0000-000000000099', 'post', '00000000-0000-0000-0000-000000000003', N'missing');
        EXEC #ExpectError N'EXEC community.usp_ResolveReportedContent ''80000000-0000-0000-0000-000000000001'', ''00000000-0000-0000-0000-000000000001'', N''pending'';', 51030;
        EXEC #ExpectError N'EXEC community.usp_ResolveReportedContent ''80000000-0000-0000-0000-000000000001'', ''00000000-0000-0000-0000-000000000002'', N''resolved'';', 51032;
        EXEC #ExpectError N'EXEC community.usp_ResolveReportedContent ''80000000-0000-0000-0000-000000000001'', ''00000000-0000-0000-0000-000000000006'', N''resolved'';', 51032;
        EXEC #ExpectError N'EXEC community.usp_ResolveReportedContent ''80000000-0000-0000-0000-000000000099'', ''00000000-0000-0000-0000-000000000001'', N''resolved'';', 51033;
        EXEC #ExpectError N'EXEC community.usp_ResolveReportedContent ''80000000-0000-0000-0000-000000000008'', ''00000000-0000-0000-0000-000000000001'', N''resolved'';', 51035;
        EXEC community.usp_ResolveReportedContent '80000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000001', N'dismissed';
        IF NOT EXISTS (SELECT 1 FROM community.Posts WHERE Id = '50000000-0000-0000-0000-000000000002')
           OR NOT EXISTS (SELECT 1 FROM community.ReportedContents WHERE Id = '80000000-0000-0000-0000-000000000005' AND Status = 'dismissed')
            THROW 51900, N'Dismissal must retain content.', 1;
        EXEC sys.sp_executesql N'CREATE TRIGGER reports.task3_FailAudit ON reports.AuditLog AFTER INSERT AS
        BEGIN
            THROW 51901, N''Injected audit failure.'', 1;
        END;';
        EXEC #ExpectError N'EXEC community.usp_ResolveReportedContent ''80000000-0000-0000-0000-000000000001'', ''00000000-0000-0000-0000-000000000001'', N''resolved'';', 51901;
        IF NOT EXISTS (SELECT 1 FROM community.Posts WHERE Id = '50000000-0000-0000-0000-000000000001')
           OR NOT EXISTS (SELECT 1 FROM community.Comments WHERE Id = '60000000-0000-0000-0000-000000000001')
           OR NOT EXISTS (SELECT 1 FROM heritage.KnowledgeChunks WHERE SourceId = '50000000-0000-0000-0000-000000000001')
           OR (SELECT COUNT(*) FROM community.ReportedContents WHERE Status = 'pending' AND Id IN
               ('80000000-0000-0000-0000-000000000001', '80000000-0000-0000-0000-000000000002', '80000000-0000-0000-0000-000000000003', '80000000-0000-0000-0000-000000000004')) <> 4
            THROW 51900, N'Audit failure must restore post, cascade children, chunks and report statuses.', 1;
        DROP TRIGGER reports.task3_FailAudit;
        EXECUTE AS USER = 'task3_backend';
        EXEC community.usp_ResolveReportedContent '80000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', N'resolved';
        REVERT;
        IF EXISTS (SELECT 1 FROM community.Posts WHERE Id = '50000000-0000-0000-0000-000000000001')
           OR EXISTS (SELECT 1 FROM community.Comments WHERE PostId = '50000000-0000-0000-0000-000000000001')
           OR EXISTS (SELECT 1 FROM community.PostMedia WHERE PostId = '50000000-0000-0000-0000-000000000001')
           OR EXISTS (SELECT 1 FROM community.Reactions WHERE PostId = '50000000-0000-0000-0000-000000000001')
           OR EXISTS (SELECT 1 FROM heritage.KnowledgeChunks WHERE SourceId = '50000000-0000-0000-0000-000000000001')
           OR (SELECT COUNT(*) FROM community.ReportedContents WHERE Status = 'resolved') <> 4
            THROW 51900, N'Resolving post must cascade, clear AI chunks and resolve related pending reports.', 1;
        EXEC #ExpectError N'EXEC community.usp_ResolveReportedContent ''80000000-0000-0000-0000-000000000001'', ''00000000-0000-0000-0000-000000000001'', N''resolved'';', 51034;
        EXEC community.usp_ResolveReportedContent '80000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000001', N'resolved';
        EXEC community.usp_ResolveReportedContent '80000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000001', N'resolved';
        IF EXISTS (SELECT 1 FROM community.Comments WHERE Id = '60000000-0000-0000-0000-000000000002')
           OR EXISTS (SELECT 1 FROM community.PostMedia WHERE Id = '70000000-0000-0000-0000-000000000002')
           OR NOT EXISTS (SELECT 1 FROM community.Posts WHERE Id = '50000000-0000-0000-0000-000000000002')
            THROW 51900, N'Comment/photo moderation must retain their parent post.', 1;
        IF (SELECT COUNT(*) FROM reports.AuditLog WHERE UserId = '00000000-0000-0000-0000-000000000001' AND Action LIKE 'report.%') <> 4
            THROW 51900, N'Each completed moderation decision must have one audit row.', 1;

        -- Du lieu cho kiem thu dong thoi: mo cung file nay trong hai tab, chon TAB_A va TAB_B.
        INSERT core.MemberVerifications (Id, UserId, MemberId) VALUES
        ('40000000-0000-0000-0000-000000000020', '00000000-0000-0000-0000-000000000008', '10000000-0000-0000-0000-000000000020'),
        ('40000000-0000-0000-0000-000000000021', '00000000-0000-0000-0000-000000000009', '10000000-0000-0000-0000-000000000020');


        PRINT N'PASS: View, phan quyen, duyet/tu choi, kiem duyet, Trigger va rollback.';
        PRINT N'De kiem thu dong thoi: mo cung file nay o hai tab SSMS, chon TAB_A va TAB_B.';
    END;

    IF @Mode = 'TAB_A'
    BEGIN
        BEGIN TRY
            BEGIN TRANSACTION;
            EXEC core.usp_ReviewMemberVerification
                '40000000-0000-0000-0000-000000000020',
                '00000000-0000-0000-0000-000000000001', N'approved';
            -- Giu khoa de tab B phai cho transaction nay ket thuc.
            WAITFOR DELAY '00:00:10';
            COMMIT TRANSACTION;
            PRINT N'Tab A: duyet thanh cong.';
        END TRY
        BEGIN CATCH
            IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
            IF ERROR_NUMBER() <> 51005 THROW;
            PRINT N'Tab A: yeu cau da duoc xu ly do phien kia duyet truoc.';
        END CATCH;
    END;

    IF @Mode = 'TAB_B'
    BEGIN
        BEGIN TRY
            EXEC core.usp_ReviewMemberVerification
                '40000000-0000-0000-0000-000000000021',
                '00000000-0000-0000-0000-000000000001', N'approved';
            PRINT N'Tab B: duyet thanh cong (tab B chay truoc tab A).';
        END TRY
        BEGIN CATCH
            IF ERROR_NUMBER() <> 51005 THROW;
            PRINT N'Tab B: tu choi dung ky vong vi tab A da duyet truoc.';
        END CATCH;

        IF (SELECT COUNT(*) FROM core.MemberVerifications
            WHERE Id IN ('40000000-0000-0000-0000-000000000020', '40000000-0000-0000-0000-000000000021')
              AND Status = N'approved') <> 1
           OR (SELECT COUNT(*) FROM core.MemberVerifications
               WHERE Id IN ('40000000-0000-0000-0000-000000000020', '40000000-0000-0000-0000-000000000021')
                 AND Status = N'rejected') <> 1
           OR NOT EXISTS (SELECT 1 FROM core.MemberVerifications v JOIN genealogy.Members m ON m.Id = v.MemberId
               WHERE v.Id IN ('40000000-0000-0000-0000-000000000020', '40000000-0000-0000-0000-000000000021')
                 AND v.Status = N'approved' AND m.UserId = v.UserId)
            THROW 51900, N'FAIL: can dung mot approved, mot rejected va lien ket thanh vien dung.', 1;

        SELECT v.Id AS VerificationId, v.UserId, v.Status, m.UserId AS LinkedUserId
        FROM core.MemberVerifications v JOIN genealogy.Members m ON m.Id = v.MemberId
        WHERE v.Id IN ('40000000-0000-0000-0000-000000000020', '40000000-0000-0000-0000-000000000021');
        PRINT N'PASS: hai phien cung duyet mot ho so, chi mot yeu cau duoc chap nhan.';
    END;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    IF USER_NAME() = N'task3_backend' REVERT;
    EXEC sys.sp_set_session_context @key = N'actor_user_id', @value = NULL;
    PRINT N'FAIL: xem thong bao loi. Chon CLEANUP va SETUP truoc khi kiem thu lai.';
    THROW;
END CATCH;
GO

USE [master];
GO
IF (SELECT [Mode] FROM #Task3Run) = 'CLEANUP'
BEGIN
    ALTER DATABASE [FamilyConnect_Task3Test] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE [FamilyConnect_Task3Test];
    PRINT N'CLEANUP: da xoa database thu FamilyConnect_Task3Test.';
END;
DROP TABLE IF EXISTS #Task3Run;
GO
SET NOEXEC OFF;
GO
