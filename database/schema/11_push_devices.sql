/* =====================================================================
   database/schema/11_push_devices.sql
   TV3 - Day thong bao ra dien thoai (Firebase Cloud Messaging)

   Them hai thu:
     1. community.DeviceTokens: moi dong la mot thiet bi da dang ky nhan
        thong bao. Mot nguoi co the dang nhap tren nhieu may.
     2. Cot community.Notifications.PushedAt: moc thoi gian da day ra
        thiet bi, de tien trinh nen khong day trung mot thong bao.
   File chi them, khong sua doi tuong cua thanh vien khac.
   ===================================================================== */
USE [$(DB_NAME)];
GO

IF OBJECT_ID(N'community.DeviceTokens', N'U') IS NULL
BEGIN
    CREATE TABLE [community].[DeviceTokens]
    (
        [Id]       UNIQUEIDENTIFIER NOT NULL
                   CONSTRAINT [DF_DeviceTokens_Id] DEFAULT NEWSEQUENTIALID(),
        [UserId]   UNIQUEIDENTIFIER NOT NULL,
        [Token]    NVARCHAR(400)    NOT NULL,
        [Platform] NVARCHAR(20)     NOT NULL
                   CONSTRAINT [DF_DeviceTokens_Platform] DEFAULT N'android',
        [CreatedAt] DATETIME2(0)    NOT NULL
                   CONSTRAINT [DF_DeviceTokens_CreatedAt] DEFAULT SYSUTCDATETIME(),
        [LastSeenAt] DATETIME2(0)   NOT NULL
                   CONSTRAINT [DF_DeviceTokens_LastSeenAt] DEFAULT SYSUTCDATETIME(),

        CONSTRAINT [PK_DeviceTokens] PRIMARY KEY CLUSTERED ([Id]),
        -- Mot token FCM chi thuoc dung mot thiet bi, nen khong the trung.
        CONSTRAINT [UQ_DeviceTokens_Token] UNIQUE ([Token]),
        CONSTRAINT [CK_DeviceTokens_Platform]
            CHECK ([Platform] IN (N'android', N'ios', N'web')),
        CONSTRAINT [FK_DeviceTokens_Users] FOREIGN KEY ([UserId])
            REFERENCES [core].[Users] ([UserId]) ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE [name] = N'IX_DeviceTokens_UserId'
                 AND [object_id] = OBJECT_ID(N'community.DeviceTokens'))
    CREATE INDEX [IX_DeviceTokens_UserId] ON [community].[DeviceTokens] ([UserId]);
GO

IF COL_LENGTH('community.Notifications', 'PushedAt') IS NULL
    ALTER TABLE [community].[Notifications] ADD [PushedAt] DATETIME2(0) NULL;
GO

/* Chi muc loc: tien trinh nen chi quan tam cac thong bao chua day. */
IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE [name] = N'IX_Notifications_Unpushed'
                 AND [object_id] = OBJECT_ID(N'community.Notifications'))
    CREATE INDEX [IX_Notifications_Unpushed]
        ON [community].[Notifications] ([CreatedAt])
        WHERE [PushedAt] IS NULL;
GO
