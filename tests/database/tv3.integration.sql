/* =====================================================================
   tests/database/tv3.integration.sql
   KIEM THU TICH HOP TV3 - Cong dong & Su kien (T-SQL / SSMS)

   Doi gia tri @Mode o dau file roi Execute toan bo file:
     TEST    : kiem thu view, function, procedure, trigger va phan quyen.
               Tu tao du lieu, tu don sach o cuoi; khong de lai gi.
     SETUP   : tao du lieu co dinh (da COMMIT) cho hai kich ban dong thoi.
     TAB_A   : phien thu nhat; giu transaction 10 giay.
     TAB_B   : phien thu hai; chay o tab khac trong luc TAB_A dang cho.
     CLEANUP : xoa du lieu do SETUP/TAB_A/TAB_B de lai.

   Thu tu chay:
     1. @Mode = 'TEST'   -> doc cot KetQua, tat ca phai la PASS.
     2. @Mode = 'SETUP'.
     3. Mo cung file o hai tab SSMS: tab 1 chon TAB_A va chay truoc,
        tab 2 chon TAB_B va chay ngay trong 10 giay TAB_A dang cho.
     4. @Mode = 'CLEANUP'.

   Yeu cau: file chay tren database FamilyConnect da nap day du
   schema/, views/, procedures/, triggers/. Dung SQLCMD Mode
   (Query -> SQLCMD Mode) hoac sqlcmd -v DB_NAME=FamilyConnect.
   Moi dong du lieu test deu mang dau hieu 'TV3-ITEST' nen CLEANUP
   xoa dung pham vi cua minh, khong anh huong du lieu that.
   ===================================================================== */
USE [$(DB_NAME)];
GO

SET NOCOUNT ON;

/* ------------------------------------------------------------------ */
DECLARE @Mode VARCHAR(10) = 'TEST';   -- TEST | SETUP | TAB_A | TAB_B | CLEANUP
/* ------------------------------------------------------------------ */

SET @Mode = UPPER(LTRIM(RTRIM(@Mode)));
IF @Mode NOT IN ('TEST', 'SETUP', 'TAB_A', 'TAB_B', 'CLEANUP')
BEGIN
    RAISERROR(N'Mode phai la TEST, SETUP, TAB_A, TAB_B hoac CLEANUP.', 16, 1);
    RETURN;
END;

DECLARE @MarkPost   NVARCHAR(20)  = N'TV3-ITEST';
DECLARE @MarkFamily NVARCHAR(50)  = N'TV3-ITEST Gia dinh';
DECLARE @MailAdmin  NVARCHAR(255) = N'tv3.itest.admin@example.invalid';
DECLARE @MailMember NVARCHAR(255) = N'tv3.itest.member@example.invalid';

DECLARE @Admin  UNIQUEIDENTIFIER, @Member UNIQUEIDENTIFIER,
        @Family UNIQUEIDENTIFIER, @Post   UNIQUEIDENTIFIER,
        @Event  UNIQUEIDENTIFIER, @MemberRow UNIQUEIDENTIFIER;
DECLARE @Err INT, @Rows INT, @Text NVARCHAR(400);

DECLARE @R TABLE
(
    [Stt]     INT IDENTITY(1, 1),
    [Buoc]    NVARCHAR(80),
    [KetQua]  CHAR(4),
    [ChiTiet] NVARCHAR(400)
);

/* =====================================================================
   PHAN 1 - @Mode = 'TEST'
   ===================================================================== */
IF @Mode = 'TEST'
BEGIN
    IF EXISTS (SELECT 1 FROM [core].[Families] WHERE [Name] = @MarkFamily)
    BEGIN
        PRINT N'TEST: du lieu SETUP cua kich ban dong thoi dang ton tai.';
        PRINT N'TEST: chay @Mode = CLEANUP truoc roi chay lai TEST.';
        RETURN;
    END;

    /* ---- Du lieu dung cho kiem thu -------------------------------- */
    SET @Admin  = NEWID();
    SET @Member = NEWID();
    SET @Family = NEWID();
    SET @Event  = NEWID();

    INSERT [core].[Families] ([Id], [Name]) VALUES (@Family, @MarkFamily);
    INSERT [core].[Users] ([UserId], [Email], [PasswordHash], [FullName], [Role], [IsActive])
    VALUES (@Admin,  @MailAdmin,  N'TEST-ONLY', N'TV3-ITEST Admin',  N'admin',  1),
           (@Member, @MailMember, N'TEST-ONLY', N'TV3-ITEST Member', N'member', 1);

    /* ---- 1. usp_CreatePostWithMedia + vw_NewsfeedPosts ------------ */
    EXEC [community].[usp_CreatePostWithMedia]
         @Admin, @Family, N'TV3-ITEST bai dau tien',
         N'[{"url":"a.jpg"},{"url":"b.jpg","type":"image"}]', @Post OUTPUT;

    SELECT @Text = [MediaUrls] FROM [community].[vw_NewsfeedPosts] WHERE [PostId] = @Post;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'1a. View ghep danh sach anh dung thu tu',
        CASE WHEN @Text = N'a.jpg,b.jpg' THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'MediaUrls = ', ISNULL(@Text, N'(NULL)'), N'; ky vong a.jpg,b.jpg'));

    SELECT @Text = CONCAT([AuthorName], N' / ', [CommentCount], N' / ', [ReactionCount])
    FROM [community].[vw_NewsfeedPosts] WHERE [PostId] = @Post;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'1b. View lay dung tac gia, dem binh luan va cam xuc',
        CASE WHEN @Text = N'TV3-ITEST Admin / 0 / 0' THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Tac gia/CommentCount/ReactionCount = ', @Text));

    /* ---- 2. Tinh nguyen to cua giao tac tao bai viet -------------- */
    SET @Err = 0;
    BEGIN TRY
        DECLARE @Tmp UNIQUEIDENTIFIER;
        EXEC [community].[usp_CreatePostWithMedia]
             @Admin, @Family, N'TV3-ITEST json sai', N'[{url:"a.jpg"}', @Tmp OUTPUT;
    END TRY
    BEGIN CATCH SET @Err = ERROR_NUMBER(); END CATCH;

    SELECT @Rows = COUNT(*) FROM [community].[Posts]
    WHERE [FamilyId] = @Family AND [Content] = N'TV3-ITEST json sai';
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'2. JSON sai bi chan, khong tao bai viet nua vo',
        CASE WHEN @Err = 50703 AND @Rows = 0 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Loi = ', @Err, N' (ky vong 50703); so bai con lai = ', @Rows, N' (ky vong 0)'));

    /* ---- 3. usp_UpsertReaction ----------------------------------- */
    EXEC [community].[usp_UpsertReaction] @Post, @Admin, N'Like';
    EXEC [community].[usp_UpsertReaction] @Post, @Admin, N'Love';

    SELECT @Rows = COUNT(*), @Text = MAX([Type])
    FROM [community].[Reactions] WHERE [PostId] = @Post AND [UserId] = @Admin;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'3a. Doi cam xuc chi cap nhat, khong tao dong moi',
        CASE WHEN @Rows = 1 AND @Text = N'Love' THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So dong = ', @Rows, N', loai = ', ISNULL(@Text, N'(NULL)'), N'; ky vong 1 / Love'));

    EXEC [community].[usp_UpsertReaction] @Post, @Admin, NULL;
    SELECT @Rows = COUNT(*) FROM [community].[Reactions] WHERE [PostId] = @Post;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'3b. Truyen Type = NULL thi go cam xuc',
        CASE WHEN @Rows = 0 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So dong con lai = ', @Rows, N'; ky vong 0'));

    SET @Err = 0;
    BEGIN TRY
        DECLARE @NoPost UNIQUEIDENTIFIER = NEWID();
        EXEC [community].[usp_UpsertReaction] @NoPost, @Admin, N'Like';
    END TRY
    BEGIN CATCH SET @Err = ERROR_NUMBER(); END CATCH;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'3c. Cam xuc cho bai khong ton tai bi tu choi',
        CASE WHEN @Err = 50711 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Loi = ', @Err, N'; ky vong 50711'));

    /* ---- 4. usp_UpsertEventRsvp + fn_GetMonthlyEvents ------------- */
    SET @MemberRow = NEWID();
    INSERT [community].[Events] ([Id], [FamilyId], [Title], [EventDate])
    VALUES (@Event, @Family, N'TV3-ITEST Gio to', DATETIME2FROMPARTS(2026, 11, 20, 9, 0, 0, 0, 0));

    EXEC [community].[usp_UpsertEventRsvp] @Event, @MemberRow, N'Maybe';
    EXEC [community].[usp_UpsertEventRsvp] @Event, @MemberRow, N'Going';

    SELECT @Rows = COUNT(*) FROM [community].[EventParticipants]
    WHERE [EventId] = @Event AND [MemberId] = @MemberRow;
    SELECT @Text = CONVERT(NVARCHAR(20), [GoingCount])
    FROM [community].[fn_GetMonthlyEvents](@Family, 2026, 11) WHERE [EventId] = @Event;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'4a. Doi RSVP chi cap nhat; GoingCount dem dung',
        CASE WHEN @Rows = 1 AND @Text = N'1' THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So dong RSVP = ', @Rows, N', GoingCount = ', ISNULL(@Text, N'(khong co)'),
               N'; ky vong 1 / 1'));

    SELECT @Rows = COUNT(*) FROM [community].[fn_GetMonthlyEvents](@Family, 2026, 12);
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'4b. Lich thang chi lay su kien trong thang do',
        CASE WHEN @Rows = 0 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So su kien thang 12 = ', @Rows, N'; ky vong 0'));

    /* Bien thang: 23:59 ngay cuoi thang phai nam trong thang. */
    DECLARE @Edge UNIQUEIDENTIFIER = NEWID();
    INSERT [community].[Events] ([Id], [FamilyId], [Title], [EventDate])
    VALUES (@Edge, @Family, N'TV3-ITEST cuoi thang',
            DATETIME2FROMPARTS(2026, 11, 30, 23, 59, 0, 0, 0));
    SELECT @Rows = COUNT(*) FROM [community].[fn_GetMonthlyEvents](@Family, 2026, 11)
    WHERE [EventId] = @Edge;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'4c. Su kien 23:59 ngay cuoi thang khong bi bo sot',
        CASE WHEN @Rows = 1 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Tim thay = ', @Rows, N'; ky vong 1'));

    SET @Err = 0;
    BEGIN TRY
        DECLARE @NoEvent UNIQUEIDENTIFIER = NEWID();
        EXEC [community].[usp_UpsertEventRsvp] @NoEvent, @MemberRow, N'Going';
    END TRY
    BEGIN CATCH SET @Err = ERROR_NUMBER(); END CATCH;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'4d. RSVP cho su kien khong ton tai bi tu choi',
        CASE WHEN @Err = 50721 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Loi = ', @Err, N'; ky vong 50721'));

    /* ---- 5. usp_ClaimDueReminders -------------------------------- */
    /* usp_ClaimDueReminders quet toan bang EventReminders, nen phan nay
       nam trong mot giao tac rieng va ROLLBACK: khong lam thay doi trang
       thai nhac nho that cua cac gia dinh khac. Ba nhac nho cua test dat
       moc thoi gian nam 1900 de luon duoc xep truoc trong ORDER BY. */
    BEGIN TRAN ClaimTest;

    INSERT [community].[EventReminders] ([EventId], [ReminderTime])
    VALUES (@Event, DATETIME2FROMPARTS(1900, 1, 1, 0, 0, 0, 0, 0)),
           (@Event, DATETIME2FROMPARTS(1900, 1, 2, 0, 0, 0, 0, 0)),
           (@Event, DATEADD(DAY, 1, SYSUTCDATETIME()));

    DECLARE @Claim1 TABLE ([Id] UNIQUEIDENTIFIER, [EventId] UNIQUEIDENTIFIER,
                           [ReminderTime] DATETIME2(0), [Status] NVARCHAR(20));
    INSERT @Claim1 EXEC [community].[usp_ClaimDueReminders] @BatchSize = 2;

    SELECT @Rows = COUNT(*) FROM @Claim1 WHERE [EventId] = @Event;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'5a. Chi lay nhac nho da den han',
        CASE WHEN @Rows = 2 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So nhac nho lay duoc = ', @Rows, N'; ky vong 2 (bo qua cai ngay mai)'));

    SELECT @Rows = COUNT(*) FROM @Claim1 WHERE [EventId] = @Event AND [Status] <> N'sent';
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'5b. Nhac nho lay ra duoc danh dau sent ngay trong cau lenh',
        CASE WHEN @Rows = 0 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So dong khac sent = ', @Rows, N'; ky vong 0'));

    DECLARE @Claim2 TABLE ([Id] UNIQUEIDENTIFIER, [EventId] UNIQUEIDENTIFIER,
                           [ReminderTime] DATETIME2(0), [Status] NVARCHAR(20));
    INSERT @Claim2 EXEC [community].[usp_ClaimDueReminders] @BatchSize = 2;
    SELECT @Rows = COUNT(*) FROM @Claim2 WHERE [EventId] = @Event;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'5c. Goi lan hai khong lay lai -> khong gui trung',
        CASE WHEN @Rows = 0 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So nhac nho lay lai = ', @Rows, N'; ky vong 0'));

    ROLLBACK TRAN ClaimTest;   -- bo moi thay doi trang thai nhac nho

    /* ---- 6. trg_ReportedContents_Escalation ---------------------- */
    DECLARE @Key NVARCHAR(60) = CONVERT(NVARCHAR(36), @Post);

    INSERT [community].[ReportedContents] ([TargetId], [TargetType], [ReportedBy], [Reason])
    VALUES (@Post, N'post', @Admin, N'TV3-ITEST spam 1'),
           (@Post, N'post', @Admin, N'TV3-ITEST spam 2');
    SELECT @Rows = COUNT(*) FROM [reports].[AuditLog]
    WHERE [Action] LIKE N'ESCALATE:%' + @Key + N'%';
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'6a. Duoi nguong 3 bao cao thi chua leo thang',
        CASE WHEN @Rows = 0 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So dong ESCALATE = ', @Rows, N'; ky vong 0'));

    INSERT [community].[ReportedContents] ([TargetId], [TargetType], [ReportedBy], [Reason])
    VALUES (@Post, N'post', @Admin, N'TV3-ITEST spam 3');
    SELECT @Rows = COUNT(*) FROM [reports].[AuditLog]
    WHERE [Action] LIKE N'ESCALATE:%' + @Key + N'%';
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'6b. Dung bao cao thu 3 thi ghi mot dong ESCALATE',
        CASE WHEN @Rows = 1 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So dong ESCALATE = ', @Rows, N'; ky vong 1'));

    INSERT [community].[ReportedContents] ([TargetId], [TargetType], [ReportedBy], [Reason])
    VALUES (@Post, N'post', @Admin, N'TV3-ITEST spam 4');
    SELECT @Rows = COUNT(*) FROM [reports].[AuditLog]
    WHERE [Action] LIKE N'ESCALATE:%' + @Key + N'%';
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'6c. Bao cao thu 4 khong ghi lap lai',
        CASE WHEN @Rows = 1 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So dong ESCALATE = ', @Rows, N'; ky vong van la 1'));

    /* Nhieu bao cao vao cung mot lenh INSERT: trigger chi ghi mot lan. */
    DECLARE @Post2 UNIQUEIDENTIFIER;
    EXEC [community].[usp_CreatePostWithMedia]
         @Admin, @Family, N'TV3-ITEST bai thu hai', NULL, @Post2 OUTPUT;
    DECLARE @Key2 NVARCHAR(60) = CONVERT(NVARCHAR(36), @Post2);
    INSERT [community].[ReportedContents] ([TargetId], [TargetType], [ReportedBy], [Reason])
    VALUES (@Post2, N'post', @Admin, N'TV3-ITEST loat 1'),
           (@Post2, N'post', @Admin, N'TV3-ITEST loat 2'),
           (@Post2, N'post', @Admin, N'TV3-ITEST loat 3'),
           (@Post2, N'post', @Admin, N'TV3-ITEST loat 4');
    SELECT @Rows = COUNT(*) FROM [reports].[AuditLog]
    WHERE [Action] LIKE N'ESCALATE:%' + @Key2 + N'%';
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'6d. Ba bao cao trong cung mot INSERT chi leo thang mot lan',
        CASE WHEN @Rows = 1 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So dong ESCALATE = ', @Rows, N'; ky vong 1'));

    /* ---- 7. Phan quyen theo gia dinh ----------------------------- */
    SET @Err = 0;
    BEGIN TRY
        DECLARE @Denied UNIQUEIDENTIFIER;
        EXEC [community].[usp_CreatePostWithMedia]
             @Member, @Family, N'TV3-ITEST khong co quyen', NULL, @Denied OUTPUT;
    END TRY
    BEGIN CATCH SET @Err = ERROR_NUMBER(); END CATCH;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'7a. Nguoi ngoai gia dinh khong dang bai duoc',
        CASE WHEN @Err = 51403 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Loi = ', @Err, N'; ky vong 51403'));

    INSERT [genealogy].[Members] ([FamilyId], [UserId], [FullName])
    VALUES (@Family, @Member, N'TV3-ITEST Member');

    SET @Err = 0;
    BEGIN TRY
        DECLARE @Allowed UNIQUEIDENTIFIER;
        EXEC [community].[usp_CreatePostWithMedia]
             @Member, @Family, N'TV3-ITEST da co quyen', NULL, @Allowed OUTPUT;
    END TRY
    BEGIN CATCH SET @Err = ERROR_NUMBER(); END CATCH;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'7b. Co ho so gia pha trong gia dinh thi dang bai duoc',
        CASE WHEN @Err = 0 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Loi = ', @Err, N'; ky vong 0'));

    SET @Err = 0;
    BEGIN TRY
        DECLARE @NoUser UNIQUEIDENTIFIER = NEWID(), @Any UNIQUEIDENTIFIER;
        EXEC [community].[usp_CreatePostWithMedia]
             @NoUser, @Family, N'TV3-ITEST nguoi la', NULL, @Any OUTPUT;
    END TRY
    BEGIN CATCH SET @Err = ERROR_NUMBER(); END CATCH;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'7c. Nguoi dung khong ton tai bi chan tu dau',
        CASE WHEN @Err = 50701 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Loi = ', @Err, N'; ky vong 50701'));

    /* ---- Don sach du lieu kiem thu ------------------------------- */
    DELETE a FROM [reports].[AuditLog] AS a
    WHERE a.[Action] LIKE N'ESCALATE:%'
      AND EXISTS (SELECT 1 FROM [community].[Posts] AS p
                  WHERE p.[FamilyId] = @Family
                    AND a.[Action] LIKE N'%' + CONVERT(NVARCHAR(36), p.[Id]) + N'%');
    DELETE FROM [reports].[AuditLog] WHERE [UserId] IN (@Admin, @Member);
    DELETE FROM [community].[ReportedContents] WHERE [ReportedBy] IN (@Admin, @Member);
    DELETE FROM [community].[Posts]  WHERE [FamilyId] = @Family;   -- cascade media/comment/reaction
    DELETE FROM [community].[Events] WHERE [FamilyId] = @Family;   -- cascade rsvp/reminder/gallery
    DELETE FROM [genealogy].[Members] WHERE [FamilyId] = @Family;
    DELETE FROM [core].[Users]    WHERE [UserId] IN (@Admin, @Member);
    DELETE FROM [core].[Families] WHERE [Id] = @Family;

    /* ---- Ket qua ------------------------------------------------- */
    SELECT [Stt], [Buoc], [KetQua], [ChiTiet] FROM @R ORDER BY [Stt];

    SELECT @Rows = COUNT(*) FROM @R WHERE [KetQua] = 'FAIL';
    IF @Rows = 0
        PRINT N'TEST: tat ca kiem thu PASS. Du lieu kiem thu da duoc don sach.';
    ELSE
        PRINT CONCAT(N'TEST: co ', @Rows, N' buoc FAIL. Xem cot ChiTiet.');
END;

/* =====================================================================
   PHAN 2 - @Mode = 'SETUP'
   Tao du lieu da COMMIT cho hai kich ban dong thoi.
   ===================================================================== */
IF @Mode = 'SETUP'
BEGIN
    IF EXISTS (SELECT 1 FROM [core].[Families] WHERE [Name] = @MarkFamily)
    BEGIN
        PRINT N'SETUP: du lieu TV3-ITEST da ton tai. Chay CLEANUP truoc.';
        RETURN;
    END;

    SET @Admin  = NEWID();
    SET @Family = NEWID();
    SET @Event  = NEWID();

    INSERT [core].[Families] ([Id], [Name]) VALUES (@Family, @MarkFamily);
    INSERT [core].[Users] ([UserId], [Email], [PasswordHash], [FullName], [Role], [IsActive])
    VALUES (@Admin, @MailAdmin, N'TEST-ONLY', N'TV3-ITEST Admin', N'admin', 1);

    EXEC [community].[usp_CreatePostWithMedia]
         @Admin, @Family, N'TV3-ITEST bai cho kich ban dong thoi', NULL, @Post OUTPUT;

    INSERT [community].[Events] ([Id], [FamilyId], [Title], [EventDate])
    VALUES (@Event, @Family, N'TV3-ITEST su kien dong thoi',
            DATEADD(DAY, 7, SYSUTCDATETIME()));

    /* Moc thoi gian nam 1900 de hai nhac nho nay luon duoc
       usp_ClaimDueReminders xep truoc moi nhac nho khac trong bang. */
    INSERT [community].[EventReminders] ([EventId], [ReminderTime])
    VALUES (@Event, DATETIME2FROMPARTS(1900, 1, 1, 0, 0, 0, 0, 0)),
           (@Event, DATETIME2FROMPARTS(1900, 1, 2, 0, 0, 0, 0, 0));

    PRINT N'SETUP: da tao 1 gia dinh, 1 nguoi dung, 1 bai viet, 1 su kien va 2 nhac nho den han.';
    PRINT N'SETUP: mo cung file o hai tab, chay TAB_A truoc roi TAB_B trong 10 giay.';
END;

/* =====================================================================
   PHAN 3 - @Mode = 'TAB_A'
   Giu transaction 10 giay: dang giu UPDLOCK tren nhac nho thu nhat va
   khoa khoang khoa cua cam xuc (MERGE ... WITH (HOLDLOCK)).
   ===================================================================== */
IF @Mode = 'TAB_A'
BEGIN
    SELECT @Family = [Id] FROM [core].[Families] WHERE [Name] = @MarkFamily;
    SELECT @Admin  = [UserId] FROM [core].[Users] WHERE [Email] = @MailAdmin;
    SELECT @Post   = [Id] FROM [community].[Posts] WHERE [FamilyId] = @Family;

    IF @Post IS NULL
    BEGIN
        PRINT N'TAB_A: chua co du lieu. Chay @Mode = SETUP truoc.';
        RETURN;
    END;

    BEGIN TRAN;

        DECLARE @ClaimA TABLE ([Id] UNIQUEIDENTIFIER, [EventId] UNIQUEIDENTIFIER,
                               [ReminderTime] DATETIME2(0), [Status] NVARCHAR(20));
        INSERT @ClaimA EXEC [community].[usp_ClaimDueReminders] @BatchSize = 1;
        SELECT N'TAB_A lay nhac nho' AS [Buoc], [Id], [ReminderTime], [Status] FROM @ClaimA;

        IF NOT EXISTS (SELECT 1 FROM @ClaimA)
            PRINT N'TAB_A: khong lay duoc nhac nho nao (co the da chay TAB_A truoc do). '
                + N'Nen chay CLEANUP roi SETUP lai de ket qua TAB_B dung.';

        EXEC [community].[usp_UpsertReaction] @Post, @Admin, N'Like';

        PRINT N'TAB_A: dang giu transaction 10 giay. Chay TAB_B ngay bay gio.';
        WAITFOR DELAY '00:00:10';

    COMMIT TRAN;

    PRINT N'TAB_A: da COMMIT. Doc ket qua o tab TAB_B.';
END;

/* =====================================================================
   PHAN 4 - @Mode = 'TAB_B'
   Chay trong luc TAB_A dang cho. Ky vong:
     - Lay nhac nho KHONG bi cho (READPAST bo qua dong TAB_A dang giu)
       va KHONG lay lai dong do -> khong gui trung thong bao.
     - Doi cam xuc PHAI cho TAB_A commit (HOLDLOCK), sau do chi con
       dung mot dong cam xuc -> khong sinh ban trung, khong mat ghi.
   ===================================================================== */
IF @Mode = 'TAB_B'
BEGIN
    SELECT @Family = [Id] FROM [core].[Families] WHERE [Name] = @MarkFamily;
    SELECT @Admin  = [UserId] FROM [core].[Users] WHERE [Email] = @MailAdmin;
    SELECT @Post   = [Id] FROM [community].[Posts] WHERE [FamilyId] = @Family;
    SELECT @Event  = [Id] FROM [community].[Events] WHERE [FamilyId] = @Family;

    IF @Post IS NULL
    BEGIN
        PRINT N'TAB_B: chua co du lieu. Chay @Mode = SETUP truoc.';
        RETURN;
    END;

    /* --- 1. Nhac nho: khong cho, khong trung --- */
    DECLARE @T0 DATETIME2(3) = SYSUTCDATETIME();
    DECLARE @ClaimB TABLE ([Id] UNIQUEIDENTIFIER, [EventId] UNIQUEIDENTIFIER,
                           [ReminderTime] DATETIME2(0), [Status] NVARCHAR(20));
    INSERT @ClaimB EXEC [community].[usp_ClaimDueReminders] @BatchSize = 1;
    DECLARE @MsClaim INT = DATEDIFF(MILLISECOND, @T0, SYSUTCDATETIME());

    SELECT @Rows = COUNT(*) FROM @ClaimB WHERE [EventId] = @Event;
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'B1. Lay nhac nho khong bi TAB_A chan',
        CASE WHEN @MsClaim < 3000 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Cho ', @MsClaim, N' ms; ky vong duoi 3000 ms (READPAST)'));
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'B2. Khong lay lai nhac nho TAB_A dang giu',
        CASE WHEN @Rows = 1 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Lay duoc ', @Rows, N' nhac nho cua su kien test; ',
               N'ky vong 1 - dong TAB_A dang giu bi bo qua, lay dong con lai'));

    /* --- 2. Cam xuc: phai cho, ket qua chi mot dong --- */
    SET @T0 = SYSUTCDATETIME();
    EXEC [community].[usp_UpsertReaction] @Post, @Admin, N'Love';
    DECLARE @MsReact INT = DATEDIFF(MILLISECOND, @T0, SYSUTCDATETIME());

    SELECT @Rows = COUNT(*), @Text = MAX([Type])
    FROM [community].[Reactions] WHERE [PostId] = @Post AND [UserId] = @Admin;

    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'B3. Doi cam xuc phai cho TAB_A commit',
        CASE WHEN @MsReact >= 1000 THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'Cho ', @MsReact, N' ms; ky vong tu 1000 ms tro len (HOLDLOCK). ',
               N'Neu nho hon thi TAB_A da commit xong truoc, chay lai hai tab.'));
    INSERT @R ([Buoc], [KetQua], [ChiTiet]) VALUES (N'B4. Hai phien ghi xong chi con dung mot cam xuc',
        CASE WHEN @Rows = 1 AND @Text = N'Love' THEN 'PASS' ELSE 'FAIL' END,
        CONCAT(N'So dong = ', @Rows, N', loai = ', ISNULL(@Text, N'(NULL)'),
               N'; ky vong 1 / Love'));

    SELECT [Stt], [Buoc], [KetQua], [ChiTiet] FROM @R ORDER BY [Stt];
    SELECT N'Trang thai nhac nho' AS [Bang], [Status], COUNT(*) AS [SoDong]
    FROM [community].[EventReminders] AS r
    WHERE EXISTS (SELECT 1 FROM [community].[Events] AS e
                  WHERE e.[Id] = r.[EventId] AND e.[FamilyId] = @Family)
    GROUP BY [Status];

    PRINT N'TAB_B: xong. Sau khi doc ket qua, chay @Mode = CLEANUP.';
END;

/* =====================================================================
   PHAN 5 - @Mode = 'CLEANUP'
   ===================================================================== */
IF @Mode = 'CLEANUP'
BEGIN
    SELECT @Family = [Id] FROM [core].[Families] WHERE [Name] = @MarkFamily;

    IF @Family IS NULL
    BEGIN
        PRINT N'CLEANUP: khong con du lieu TV3-ITEST nao.';
        RETURN;
    END;

    DELETE a FROM [reports].[AuditLog] AS a
    WHERE a.[Action] LIKE N'ESCALATE:%'
      AND EXISTS (SELECT 1 FROM [community].[Posts] AS p
                  WHERE p.[FamilyId] = @Family
                    AND a.[Action] LIKE N'%' + CONVERT(NVARCHAR(36), p.[Id]) + N'%');
    DELETE a FROM [reports].[AuditLog] AS a
    WHERE EXISTS (SELECT 1 FROM [core].[Users] AS u
                  WHERE u.[UserId] = a.[UserId]
                    AND u.[Email] IN (@MailAdmin, @MailMember));
    DELETE r FROM [community].[ReportedContents] AS r
    WHERE EXISTS (SELECT 1 FROM [core].[Users] AS u
                  WHERE u.[UserId] = r.[ReportedBy]
                    AND u.[Email] IN (@MailAdmin, @MailMember));

    DELETE FROM [community].[Posts]   WHERE [FamilyId] = @Family;
    DELETE FROM [community].[Events]  WHERE [FamilyId] = @Family;
    DELETE FROM [genealogy].[Members] WHERE [FamilyId] = @Family;
    DELETE FROM [core].[Users]        WHERE [Email] IN (@MailAdmin, @MailMember);
    DELETE FROM [core].[Families]     WHERE [Id] = @Family;

    PRINT N'CLEANUP: da xoa toan bo du lieu TV3-ITEST.';
END;
GO
