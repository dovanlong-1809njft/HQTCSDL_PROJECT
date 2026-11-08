/* =====================================================================
   tests/database/test_community_smoke.sql
   TV3 - Chay thu nhanh cac doi tuong cong dong. Moi thu nam trong giao
   tac va ROLLBACK cuoi file nen khong de lai du lieu.
   Dung SQLCMD Mode:  :setvar DB_NAME "FamilyConnect"
   ===================================================================== */
USE [$(DB_NAME)];
GO
SET NOCOUNT ON;
BEGIN TRAN;

DECLARE @U UNIQUEIDENTIFIER = NEWID(), @F UNIQUEIDENTIFIER = NEWID(),
        @P UNIQUEIDENTIFIER, @E UNIQUEIDENTIFIER = NEWID(),
        @M UNIQUEIDENTIFIER = NEWID();

INSERT core.Users (UserId, Email, PasswordHash, FullName)
VALUES (@U, N'tv3.test@example.invalid', N'TEST-ONLY', N'TV3 Test');
INSERT core.Families (Id, Name) VALUES (@F, N'Gia dinh test');

-- 1. Tao bai viet kem 2 anh -> vw_NewsfeedPosts phai co MediaUrls 2 anh
EXEC community.usp_CreatePostWithMedia @U, @F, N'Bai dau tien',
     N'[{"url":"a.jpg"},{"url":"b.jpg","type":"image"}]', @P OUTPUT;
SELECT N'1. Newsfeed' AS [Buoc], PostId, AuthorName, CommentCount, ReactionCount, MediaUrls
FROM community.vw_NewsfeedPosts WHERE PostId = @P;

-- 2. Cam xuc: Like roi doi sang Love -> chi con 1 dong
EXEC community.usp_UpsertReaction @P, @U, N'Like';
EXEC community.usp_UpsertReaction @P, @U, N'Love';
SELECT N'2. Reaction' AS [Buoc], [Type] FROM community.Reactions WHERE PostId = @P;

-- 3. RSVP: Maybe roi doi Going -> GoingCount = 1
INSERT community.Events (Id, FamilyId, Title, EventDate)
VALUES (@E, @F, N'Gio to', DATEFROMPARTS(2026, 11, 20));
EXEC community.usp_UpsertEventRsvp @E, @M, N'Maybe';
EXEC community.usp_UpsertEventRsvp @E, @M, N'Going';
SELECT N'3. Lich thang 11' AS [Buoc], Title, GoingCount
FROM community.fn_GetMonthlyEvents(@F, 2026, 11);

-- 4. Nhac nho: 1 den han, 1 chua den han -> chi lay duoc 1
INSERT community.EventReminders (EventId, ReminderTime)
VALUES (@E, DATEADD(MINUTE, -5, SYSUTCDATETIME())),
       (@E, DATEADD(DAY, 1, SYSUTCDATETIME()));
EXEC community.usp_ClaimDueReminders @BatchSize = 10;   -- ky vong 1 dong

-- 5. Trigger: 3 bao cao pending cung 1 bai -> 1 dong ESCALATE trong AuditLog
INSERT community.ReportedContents (TargetId, TargetType, ReportedBy, Reason)
VALUES (@P, N'post', @U, N'spam 1'), (@P, N'post', @U, N'spam 2'), (@P, N'post', @U, N'spam 3');
SELECT N'5. Escalation' AS [Buoc], [Action]
FROM reports.AuditLog WHERE [Action] LIKE N'ESCALATE:%' + CONVERT(NVARCHAR(36), @P) + N'%';

ROLLBACK TRAN;
GO
