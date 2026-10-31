-- T-SQL: nhật ký thay đổi hệ thống.
USE [$(DB_NAME)];
GO

IF OBJECT_ID(N'reports.AuditLog', N'U') IS NULL
BEGIN
    CREATE TABLE [reports].[AuditLog]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT [DF_AuditLog_Id] DEFAULT NEWSEQUENTIALID(),
        [UserId] UNIQUEIDENTIFIER NULL,
        [Action] NVARCHAR(300) NOT NULL,
        [CreatedAt] DATETIME2(0) NOT NULL
            CONSTRAINT [DF_AuditLog_CreatedAt] DEFAULT SYSUTCDATETIME(),
        CONSTRAINT [PK_AuditLog] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_AuditLog_Users] FOREIGN KEY ([UserId])
            REFERENCES [core].[Users] ([UserId])
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_AuditLog_CreatedAt' AND [object_id] = OBJECT_ID(N'reports.AuditLog'))
    CREATE INDEX [IX_AuditLog_CreatedAt] ON [reports].[AuditLog] ([CreatedAt] DESC);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_AuditLog_User_CreatedAt' AND [object_id] = OBJECT_ID(N'reports.AuditLog'))
    CREATE INDEX [IX_AuditLog_User_CreatedAt] ON [reports].[AuditLog] ([UserId], [CreatedAt] DESC);
GO

-- View chi tiết audit log, giữ được cả log không gắn với tài khoản.
CREATE OR ALTER VIEW [reports].[vw_AuditLogDetails]
AS
    SELECT
        log.[Id],
        log.[UserId],
        users.[FullName] AS [UserFullName],
        users.[Email] AS [UserEmail],
        log.[Action],
        log.[CreatedAt]
    FROM [reports].[AuditLog] AS log
    LEFT JOIN [core].[Users] AS users ON users.[UserId] = log.[UserId];
GO

CREATE OR ALTER VIEW [reports].[vw_FamilyActivitySummary]
AS
    SELECT
        family.[Id] AS [FamilyId],
        family.[Name] AS [FamilyName],
        (SELECT COUNT_BIG(*) FROM [genealogy].[Members] AS member
         WHERE member.[FamilyId] = family.[Id]) AS [MemberCount],
        (SELECT COUNT_BIG(*) FROM [community].[Posts] AS post
         WHERE post.[FamilyId] = family.[Id]) AS [PostCount],
        (SELECT COUNT_BIG(*) FROM [community].[Events] AS event
         WHERE event.[FamilyId] = family.[Id]) AS [EventCount]
    FROM [core].[Families] AS family;
GO

CREATE OR ALTER PROCEDURE [reports].[usp_GetFamilyActivitySummary]
    @FamilyId UNIQUEIDENTIFIER = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT [FamilyId], [FamilyName], [MemberCount], [PostCount], [EventCount]
    FROM [reports].[vw_FamilyActivitySummary]
    WHERE @FamilyId IS NULL OR [FamilyId] = @FamilyId
    ORDER BY [FamilyName];
END;
GO
