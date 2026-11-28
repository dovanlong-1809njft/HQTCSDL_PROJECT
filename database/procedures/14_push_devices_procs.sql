/* =====================================================================
   database/procedures/14_push_devices_procs.sql
   TV3 - Thu tuc cho viec day thong bao ra dien thoai

     1. usp_UpsertDeviceToken     : app dang ky / gia han token FCM.
     2. usp_DeleteDeviceToken     : app go token khi dang xuat.
     3. usp_ClaimUnpushedNotifications : tien trinh nen lay cac thong bao
        chua day kem token thiet bi, va danh dau da day ngay trong cung
        mot cau lenh de khong gui trung.
     4. usp_ReleaseNotificationPush : tra lai cac thong bao gui that bai
        de lan quet sau day lai.
   ===================================================================== */
USE [$(DB_NAME)];
GO

/* ---------------------------------------------------------------------
   1. usp_UpsertDeviceToken
   Token FCM co the doi chu: cung mot may, nguoi dung A dang xuat roi
   nguoi dung B dang nhap thi token cu thuoc ve B. Vi vay khi token da
   ton tai thi gan lai cho nguoi dung moi thay vi bao loi trung khoa.
   MERGE ... WITH (HOLDLOCK) de hai lan dang ky dong thoi khong sinh ra
   hai dong cho cung mot token.
   --------------------------------------------------------------------- */
CREATE OR ALTER PROCEDURE [community].[usp_UpsertDeviceToken]
    @UserId   UNIQUEIDENTIFIER,
    @Token    NVARCHAR(400),
    @Platform NVARCHAR(20) = N'android'
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF @Token IS NULL OR LEN(LTRIM(RTRIM(@Token))) = 0
        THROW 50731, N'Token khong duoc de trong.', 1;
    IF NOT EXISTS (SELECT 1 FROM [core].[Users] WHERE [UserId] = @UserId AND [IsActive] = 1)
        THROW 50732, N'Nguoi dung khong ton tai hoac da bi khoa.', 1;
    IF @Platform NOT IN (N'android', N'ios', N'web')
        THROW 50733, N'Platform phai la android, ios hoac web.', 1;

    MERGE [community].[DeviceTokens] WITH (HOLDLOCK) AS tgt
    USING (SELECT @Token AS [Token]) AS src
        ON tgt.[Token] = src.[Token]
    WHEN MATCHED THEN
        UPDATE SET tgt.[UserId]     = @UserId,
                   tgt.[Platform]   = @Platform,
                   tgt.[LastSeenAt] = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
        INSERT ([UserId], [Token], [Platform])
        VALUES (@UserId, @Token, @Platform);
END;
GO

/* ---------------------------------------------------------------------
   2. usp_DeleteDeviceToken
   Go token khi dang xuat hoac khi FCM bao token khong con hop le.
   Truyen @UserId = NULL khi tien trinh nen tu don token het han.
   --------------------------------------------------------------------- */
CREATE OR ALTER PROCEDURE [community].[usp_DeleteDeviceToken]
    @Token  NVARCHAR(400),
    @UserId UNIQUEIDENTIFIER = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DELETE FROM [community].[DeviceTokens]
    WHERE [Token] = @Token
      AND (@UserId IS NULL OR [UserId] = @UserId);
END;
GO

/* ---------------------------------------------------------------------
   3. usp_ClaimUnpushedNotifications
   Tien trinh nen goi moi lan quet. Lay toi da @BatchSize thong bao chua
   day, danh dau PushedAt ngay trong cung cau lenh UPDATE ... OUTPUT roi
   tra ve kem token cua tung thiet bi cua nguoi nhan.
   UPDLOCK, READPAST, ROWLOCK: nhieu tien trinh nen chay song song khong
   lay trung mot thong bao va khong phai cho nhau.
   Moi dong tra ve la mot cap (thong bao, thiet bi): mot nguoi dang nhap
   ba may thi mot thong bao sinh ra ba dong.
   --------------------------------------------------------------------- */
CREATE OR ALTER PROCEDURE [community].[usp_ClaimUnpushedNotifications]
    @BatchSize INT = 50
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @Claimed TABLE
    (
        [Id]      UNIQUEIDENTIFIER PRIMARY KEY,
        [UserId]  UNIQUEIDENTIFIER NOT NULL,
        [EventId] UNIQUEIDENTIFIER NULL,
        [Title]   NVARCHAR(200) NOT NULL,
        [Body]    NVARCHAR(600) NOT NULL
    );

    ;WITH due AS
    (
        SELECT TOP (@BatchSize) *
        FROM [community].[Notifications] WITH (UPDLOCK, READPAST, ROWLOCK)
        WHERE [PushedAt] IS NULL
        ORDER BY [CreatedAt]
    )
    UPDATE due
    SET [PushedAt] = SYSUTCDATETIME()
    OUTPUT inserted.[Id], inserted.[UserId], inserted.[EventId],
           inserted.[Title], inserted.[Body]
    INTO @Claimed ([Id], [UserId], [EventId], [Title], [Body]);

    SELECT
        c.[Id]       AS [NotificationId],
        c.[UserId],
        c.[EventId],
        c.[Title],
        c.[Body],
        d.[Token],
        d.[Platform]
    FROM @Claimed AS c
    INNER JOIN [community].[DeviceTokens] AS d
        ON d.[UserId] = c.[UserId]
    ORDER BY c.[Id], d.[Token];
END;
GO

/* ---------------------------------------------------------------------
   4. usp_ReleaseNotificationPush
   Gui that bai vi loi mang hoac loi FCM: tra PushedAt ve NULL de lan
   quet sau day lai. @IdsJson co dang ["guid","guid"].
   --------------------------------------------------------------------- */
CREATE OR ALTER PROCEDURE [community].[usp_ReleaseNotificationPush]
    @IdsJson NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF @IdsJson IS NULL OR ISJSON(@IdsJson) = 0
        THROW 50734, N'IdsJson khong phai JSON hop le.', 1;

    UPDATE n
    SET n.[PushedAt] = NULL
    FROM [community].[Notifications] AS n
    INNER JOIN OPENJSON(@IdsJson) AS j
        ON n.[Id] = TRY_CONVERT(UNIQUEIDENTIFIER, j.[value]);
END;
GO
