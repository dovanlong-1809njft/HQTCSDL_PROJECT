--Thành viên và các quan hệ trong gia phả.
SET QUOTED_IDENTIFIER ON;
GO
USE [$(DB_NAME)];
GO

IF OBJECT_ID(N'genealogy.Members', N'U') IS NULL
BEGIN
    CREATE TABLE [genealogy].[Members]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT [DF_Members_Id] DEFAULT NEWSEQUENTIALID(),
        [FamilyId] UNIQUEIDENTIFIER NOT NULL,
        [BranchId] UNIQUEIDENTIFIER NULL,
        [UserId] UNIQUEIDENTIFIER NULL,
        [FullName] NVARCHAR(200) NOT NULL,
        [BirthDate] DATE NULL,
        [Location] NVARCHAR(300) NULL,
        [CreatedAt] DATETIME2(0) NOT NULL
            CONSTRAINT [DF_Members_CreatedAt] DEFAULT SYSUTCDATETIME(),
        CONSTRAINT [PK_Members] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_Members_Families] FOREIGN KEY ([FamilyId])
            REFERENCES [core].[Families] ([Id]),
        CONSTRAINT [FK_Members_Branches] FOREIGN KEY ([BranchId])
            REFERENCES [core].[Branches] ([Id]),
        CONSTRAINT [FK_Members_Users] FOREIGN KEY ([UserId])
            REFERENCES [core].[Users] ([UserId])
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'UX_Members_UserId' AND [object_id] = OBJECT_ID(N'genealogy.Members'))
    CREATE UNIQUE INDEX [UX_Members_UserId] ON [genealogy].[Members] ([UserId]) WHERE [UserId] IS NOT NULL;
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_Members_Family_Branch' AND [object_id] = OBJECT_ID(N'genealogy.Members'))
    CREATE INDEX [IX_Members_Family_Branch] ON [genealogy].[Members] ([FamilyId], [BranchId]);
GO

IF OBJECT_ID(N'genealogy.ParentChild', N'U') IS NULL
BEGIN
    CREATE TABLE [genealogy].[ParentChild]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT [DF_ParentChild_Id] DEFAULT NEWSEQUENTIALID(),
        [ParentId] UNIQUEIDENTIFIER NOT NULL,
        [ChildId] UNIQUEIDENTIFIER NOT NULL,
        [CreatedAt] DATETIME2(0) NOT NULL
            CONSTRAINT [DF_ParentChild_CreatedAt] DEFAULT SYSUTCDATETIME(),
        CONSTRAINT [PK_ParentChild] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_ParentChild_Parent] FOREIGN KEY ([ParentId])
            REFERENCES [genealogy].[Members] ([Id]),
        CONSTRAINT [FK_ParentChild_Child] FOREIGN KEY ([ChildId])
            REFERENCES [genealogy].[Members] ([Id]),
        CONSTRAINT [UQ_ParentChild_Parent_Child] UNIQUE ([ParentId], [ChildId]),
        CONSTRAINT [CK_ParentChild_NotSelf] CHECK ([ParentId] <> [ChildId])
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_ParentChild_ChildId' AND [object_id] = OBJECT_ID(N'genealogy.ParentChild'))
    CREATE INDEX [IX_ParentChild_ChildId] ON [genealogy].[ParentChild] ([ChildId]);
GO

IF OBJECT_ID(N'genealogy.Marriages', N'U') IS NULL
BEGIN
    CREATE TABLE [genealogy].[Marriages]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT [DF_Marriages_Id] DEFAULT NEWSEQUENTIALID(),
        [Spouse1Id] UNIQUEIDENTIFIER NOT NULL,
        [Spouse2Id] UNIQUEIDENTIFIER NOT NULL,
        [MarriedDate] DATE NULL,
        [CreatedAt] DATETIME2(0) NOT NULL
            CONSTRAINT [DF_Marriages_CreatedAt] DEFAULT SYSUTCDATETIME(),
        CONSTRAINT [PK_Marriages] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_Marriages_Spouse1] FOREIGN KEY ([Spouse1Id])
            REFERENCES [genealogy].[Members] ([Id]),
        CONSTRAINT [FK_Marriages_Spouse2] FOREIGN KEY ([Spouse2Id])
            REFERENCES [genealogy].[Members] ([Id]),
        CONSTRAINT [UQ_Marriages_Spouses] UNIQUE ([Spouse1Id], [Spouse2Id]),
        CONSTRAINT [CK_Marriages_SpousesOrdered]
            CHECK (CONVERT(CHAR(36), [Spouse1Id]) < CONVERT(CHAR(36), [Spouse2Id]))
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_Marriages_Spouse2Id' AND [object_id] = OBJECT_ID(N'genealogy.Marriages'))
    CREATE INDEX [IX_Marriages_Spouse2Id] ON [genealogy].[Marriages] ([Spouse2Id]);
GO

-- Bảng Hồ sơ học vấn
IF OBJECT_ID(N'genealogy.Educations', N'U') IS NULL
BEGIN
    CREATE TABLE [genealogy].[Educations]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [DF_Educations_Id] DEFAULT NEWSEQUENTIALID(),
        [MemberId] UNIQUEIDENTIFIER NOT NULL,
        [Institution] NVARCHAR(200) NOT NULL,
        [Degree] NVARCHAR(200) NULL,
        [StartDate] DATE NULL,
        [EndDate] DATE NULL,
        [CreatedAt] DATETIME2(0) NOT NULL CONSTRAINT [DF_Educations_CreatedAt] DEFAULT SYSUTCDATETIME(),
        
        CONSTRAINT [PK_Educations] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_Educations_Members] FOREIGN KEY ([MemberId]) 
            REFERENCES [genealogy].[Members] ([Id]) ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_Educations_MemberId' AND [object_id] = OBJECT_ID(N'genealogy.Educations'))
    CREATE INDEX [IX_Educations_MemberId] ON [genealogy].[Educations] ([MemberId]);
GO

-- Bảng Lịch sử công tác
IF OBJECT_ID(N'genealogy.WorkHistories', N'U') IS NULL
BEGIN
    CREATE TABLE [genealogy].[WorkHistories]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [DF_WorkHistories_Id] DEFAULT NEWSEQUENTIALID(),
        [MemberId] UNIQUEIDENTIFIER NOT NULL,
        [Company] NVARCHAR(200) NOT NULL,
        [Position] NVARCHAR(200) NOT NULL,
        [StartDate] DATE NULL,
        [EndDate] DATE NULL,
        [CreatedAt] DATETIME2(0) NOT NULL CONSTRAINT [DF_WorkHistories_CreatedAt] DEFAULT SYSUTCDATETIME(),
        
        CONSTRAINT [PK_WorkHistories] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_WorkHistories_Members] FOREIGN KEY ([MemberId]) 
            REFERENCES [genealogy].[Members] ([Id]) ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_WorkHistories_MemberId' AND [object_id] = OBJECT_ID(N'genealogy.WorkHistories'))
    CREATE INDEX [IX_WorkHistories_MemberId] ON [genealogy].[WorkHistories] ([MemberId]);
GO
