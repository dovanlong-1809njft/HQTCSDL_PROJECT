-- T-SQL: tài khoản và dữ liệu nền tảng của ứng dụng.
USE [$(DB_NAME)];
GO

IF OBJECT_ID(N'core.Users', N'U') IS NULL AND OBJECT_ID(N'dbo.Users', N'U') IS NOT NULL
BEGIN
    ALTER SCHEMA [core] TRANSFER [dbo].[Users];
END;
GO

IF OBJECT_ID(N'core.Users', N'U') IS NULL
BEGIN
    CREATE TABLE [core].[Users]
    (
        [UserId] UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT [DF_Users_UserId] DEFAULT NEWSEQUENTIALID(),
        [Email] NVARCHAR(255) NOT NULL,
        [PasswordHash] NVARCHAR(255) NOT NULL,
        [FullName] NVARCHAR(200) NOT NULL,
        [Role] NVARCHAR(20) NOT NULL
            CONSTRAINT [DF_Users_Role] DEFAULT N'member',
        [IsActive] BIT NOT NULL
            CONSTRAINT [DF_Users_IsActive] DEFAULT (1),
        [CreatedAt] DATETIME2(0) NOT NULL
            CONSTRAINT [DF_Users_CreatedAt] DEFAULT SYSUTCDATETIME(),
        CONSTRAINT [PK_Users] PRIMARY KEY ([UserId]),
        CONSTRAINT [UQ_Users_Email] UNIQUE ([Email]),
        CONSTRAINT [CK_Users_Role]
            CHECK ([Role] IN (N'admin', N'family_head', N'member', N'guest'))
    );
END;
GO

IF OBJECT_ID(N'core.Families', N'U') IS NULL
BEGIN
    CREATE TABLE [core].[Families]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT [DF_Families_Id] DEFAULT NEWSEQUENTIALID(),
        [Name] NVARCHAR(200) NOT NULL,
        [CreatedAt] DATETIME2(0) NOT NULL
            CONSTRAINT [DF_Families_CreatedAt] DEFAULT SYSUTCDATETIME(),
        CONSTRAINT [PK_Families] PRIMARY KEY ([Id])
    );
END;
GO

IF OBJECT_ID(N'core.Branches', N'U') IS NULL
BEGIN
    CREATE TABLE [core].[Branches]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT [DF_Branches_Id] DEFAULT NEWSEQUENTIALID(),
        [FamilyId] UNIQUEIDENTIFIER NOT NULL,
        [Name] NVARCHAR(200) NOT NULL,
        [CreatedAt] DATETIME2(0) NOT NULL
            CONSTRAINT [DF_Branches_CreatedAt] DEFAULT SYSUTCDATETIME(),
        CONSTRAINT [PK_Branches] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_Branches_Families] FOREIGN KEY ([FamilyId])
            REFERENCES [core].[Families] ([Id]),
        CONSTRAINT [UQ_Branches_Family_Name] UNIQUE ([FamilyId], [Name])
    );
END;
GO

IF OBJECT_ID(N'core.MemberVerifications', N'U') IS NULL
BEGIN
    CREATE TABLE [core].[MemberVerifications]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT [DF_MemberVerifications_Id] DEFAULT NEWSEQUENTIALID(),
        [UserId] UNIQUEIDENTIFIER NOT NULL,
        [MemberId] UNIQUEIDENTIFIER NOT NULL,
        [Status] NVARCHAR(20) NOT NULL
            CONSTRAINT [DF_MemberVerifications_Status] DEFAULT N'pending',
        [CreatedAt] DATETIME2(0) NOT NULL
            CONSTRAINT [DF_MemberVerifications_CreatedAt] DEFAULT SYSUTCDATETIME(),
        CONSTRAINT [PK_MemberVerifications] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_MemberVerifications_Users] FOREIGN KEY ([UserId])
            REFERENCES [core].[Users] ([UserId]),
        CONSTRAINT [UQ_MemberVerifications_User_Member] UNIQUE ([UserId], [MemberId]),
        CONSTRAINT [CK_MemberVerifications_Status]
            CHECK ([Status] IN (N'pending', N'approved', N'rejected'))
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_Branches_FamilyId' AND [object_id] = OBJECT_ID(N'core.Branches'))
    CREATE INDEX [IX_Branches_FamilyId] ON [core].[Branches] ([FamilyId]);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_MemberVerifications_Status_CreatedAt' AND [object_id] = OBJECT_ID(N'core.MemberVerifications'))
    CREATE INDEX [IX_MemberVerifications_Status_CreatedAt] ON [core].[MemberVerifications] ([Status], [CreatedAt]);
GO
