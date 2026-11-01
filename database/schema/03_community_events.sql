-- 1. Schema
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'community')
    EXEC (N'CREATE SCHEMA community');
GO

-- 2. Events
IF OBJECT_ID(N'community.Events', N'U') IS NULL
BEGIN
    CREATE TABLE community.Events
    (
        Id          UNIQUEIDENTIFIER NOT NULL
                    CONSTRAINT DF_Events_Id DEFAULT NEWSEQUENTIALID(),
        FamilyId    UNIQUEIDENTIFIER NOT NULL,
        Title       NVARCHAR(200)    NOT NULL,
        EventDate   DATETIME2(0)     NOT NULL,
        Location    NVARCHAR(500)    NULL,
        CreatedAt   DATETIME2(0)     NOT NULL
                    CONSTRAINT DF_Events_CreatedAt DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_Events PRIMARY KEY CLUSTERED (Id),
        CONSTRAINT CK_Events_Title CHECK (LEN(LTRIM(RTRIM(Title))) > 0)
    );
END
GO

-- 3. EventReminders
IF OBJECT_ID(N'community.EventReminders', N'U') IS NULL
BEGIN
    CREATE TABLE [community].[EventReminders]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [DF_EventReminders_Id] DEFAULT NEWSEQUENTIALID(),
        [EventId] UNIQUEIDENTIFIER NOT NULL,
        [ReminderTime] DATETIME2(0) NOT NULL,
        [Status] NVARCHAR(20) NOT NULL CONSTRAINT [DF_EventReminders_Status] DEFAULT N'pending',
        [CreatedAt] DATETIME2(0) NOT NULL CONSTRAINT [DF_EventReminders_CreatedAt] DEFAULT SYSUTCDATETIME(),
        
        CONSTRAINT [PK_EventReminders] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_EventReminders_Events] FOREIGN KEY ([EventId]) 
            REFERENCES [community].[Events] ([Id]) ON DELETE CASCADE,
        CONSTRAINT [CK_EventReminders_Status] CHECK ([Status] IN (N'pending', N'sent', N'failed', N'cancelled'))
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_EventReminders_Time_Status' AND [object_id] = OBJECT_ID(N'community.EventReminders'))
    CREATE INDEX [IX_EventReminders_Time_Status] ON [community].[EventReminders] ([ReminderTime], [Status]);
GO

-- 4.EventGalleries
IF OBJECT_ID(N'community.EventGalleries', N'U') IS NULL
BEGIN
    CREATE TABLE [community].[EventGalleries]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [DF_EventGalleries_Id] DEFAULT NEWSEQUENTIALID(),
        [EventId] UNIQUEIDENTIFIER NOT NULL,
        [MediaUrl] NVARCHAR(2048) NOT NULL,
        [UploadedBy] UNIQUEIDENTIFIER NOT NULL,
        [CreatedAt] DATETIME2(0) NOT NULL CONSTRAINT [DF_EventGalleries_CreatedAt] DEFAULT SYSUTCDATETIME(),
        
        CONSTRAINT [PK_EventGalleries] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_EventGalleries_Events] FOREIGN KEY ([EventId]) 
            REFERENCES [community].[Events] ([Id]) ON DELETE CASCADE,
        CONSTRAINT [FK_EventGalleries_Users] FOREIGN KEY ([UploadedBy]) 
            REFERENCES [core].[Users] ([UserId])
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_EventGalleries_EventId' AND [object_id] = OBJECT_ID(N'community.EventGalleries'))
    CREATE INDEX [IX_EventGalleries_EventId] ON [community].[EventGalleries] ([EventId]);
GO

-- 5. EventParticipants
IF OBJECT_ID(N'community.EventParticipants', N'U') IS NULL
BEGIN
    CREATE TABLE community.EventParticipants
    (
        Id          UNIQUEIDENTIFIER NOT NULL
                    CONSTRAINT DF_EventParticipants_Id DEFAULT NEWSEQUENTIALID(),
        EventId     UNIQUEIDENTIFIER NOT NULL,
        MemberId    UNIQUEIDENTIFIER NOT NULL,
        RsvpStatus  NVARCHAR(20)     NOT NULL
                    CONSTRAINT DF_EventParticipants_RsvpStatus DEFAULT N'Pending',
        CreatedAt   DATETIME2(0)     NOT NULL
                    CONSTRAINT DF_EventParticipants_CreatedAt DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_EventParticipants PRIMARY KEY CLUSTERED (Id),
        CONSTRAINT UQ_EventParticipants_Event_Member UNIQUE (EventId, MemberId),
        CONSTRAINT CK_EventParticipants_RsvpStatus
            CHECK (RsvpStatus IN (N'Pending', N'Going', N'Maybe', N'Declined')),
        CONSTRAINT FK_EventParticipants_Events
            FOREIGN KEY (EventId) REFERENCES community.Events (Id) ON DELETE CASCADE
    );
END
GO

-- 6. Posts
IF OBJECT_ID(N'community.Posts', N'U') IS NULL
BEGIN
    CREATE TABLE community.Posts
    (
        Id          UNIQUEIDENTIFIER NOT NULL
                    CONSTRAINT DF_Posts_Id DEFAULT NEWSEQUENTIALID(),
        UserId      UNIQUEIDENTIFIER NOT NULL,
        FamilyId    UNIQUEIDENTIFIER NOT NULL,
        Content     NVARCHAR(MAX)    NOT NULL,
        CreatedAt   DATETIME2(0)     NOT NULL
                    CONSTRAINT DF_Posts_CreatedAt DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_Posts PRIMARY KEY CLUSTERED (Id),
        CONSTRAINT CK_Posts_Content CHECK (LEN(LTRIM(RTRIM(Content))) > 0)
    );
END
GO

-- 7. PostMedia
IF OBJECT_ID(N'community.PostMedia', N'U') IS NULL
BEGIN
    CREATE TABLE [community].[PostMedia]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [DF_PostMedia_Id] DEFAULT NEWSEQUENTIALID(),
        [PostId] UNIQUEIDENTIFIER NOT NULL,
        [MediaUrl] NVARCHAR(2048) NOT NULL,
        [MediaType] NVARCHAR(50) NOT NULL CONSTRAINT [DF_PostMedia_MediaType] DEFAULT N'image',
        [CreatedAt] DATETIME2(0) NOT NULL CONSTRAINT [DF_PostMedia_CreatedAt] DEFAULT SYSUTCDATETIME(),
        
        CONSTRAINT [PK_PostMedia] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_PostMedia_Posts] FOREIGN KEY ([PostId]) 
            REFERENCES [community].[Posts] ([Id]) ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_PostMedia_PostId' AND [object_id] = OBJECT_ID(N'community.PostMedia'))
    CREATE INDEX [IX_PostMedia_PostId] ON [community].[PostMedia] ([PostId]);
GO
-- 8. Comments
IF OBJECT_ID(N'community.Comments', N'U') IS NULL
BEGIN
    CREATE TABLE community.Comments
    (
        Id          UNIQUEIDENTIFIER NOT NULL
                    CONSTRAINT DF_Comments_Id DEFAULT NEWSEQUENTIALID(),
        PostId      UNIQUEIDENTIFIER NOT NULL,
        UserId      UNIQUEIDENTIFIER NOT NULL,
        Content     NVARCHAR(2000)   NOT NULL,
        CreatedAt   DATETIME2(0)     NOT NULL
                    CONSTRAINT DF_Comments_CreatedAt DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_Comments PRIMARY KEY CLUSTERED (Id),
        CONSTRAINT CK_Comments_Content CHECK (LEN(LTRIM(RTRIM(Content))) > 0),
        CONSTRAINT FK_Comments_Posts
            FOREIGN KEY (PostId) REFERENCES community.Posts (Id) ON DELETE CASCADE
    );
END
GO

-- 9. Reactions
IF OBJECT_ID(N'community.Reactions', N'U') IS NULL
BEGIN
    CREATE TABLE community.Reactions
    (
        Id          UNIQUEIDENTIFIER NOT NULL
                    CONSTRAINT DF_Reactions_Id DEFAULT NEWSEQUENTIALID(),
        PostId      UNIQUEIDENTIFIER NOT NULL,
        UserId      UNIQUEIDENTIFIER NOT NULL,
        [Type]      NVARCHAR(20)     NOT NULL,
        CreatedAt   DATETIME2(0)     NOT NULL
                    CONSTRAINT DF_Reactions_CreatedAt DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_Reactions PRIMARY KEY CLUSTERED (Id),
        -- Mỗi người dùng chỉ có một reaction trên mỗi bài viết
        CONSTRAINT UQ_Reactions_Post_User UNIQUE (PostId, UserId),
        CONSTRAINT CK_Reactions_Type
            CHECK ([Type] IN (N'Like', N'Love', N'Haha', N'Wow', N'Sad', N'Angry')),
        CONSTRAINT FK_Reactions_Posts
            FOREIGN KEY (PostId) REFERENCES community.Posts (Id) ON DELETE CASCADE
    );
END
GO

-- 10 ReportedContents
IF OBJECT_ID(N'community.ReportedContents', N'U') IS NULL
BEGIN
    CREATE TABLE [community].[ReportedContents]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [DF_ReportedContents_Id] DEFAULT NEWSEQUENTIALID(),
        [TargetId] UNIQUEIDENTIFIER NOT NULL,
        [TargetType] NVARCHAR(50) NOT NULL,
        [ReportedBy] UNIQUEIDENTIFIER NOT NULL,
        [Reason] NVARCHAR(500) NOT NULL,
        [Status] NVARCHAR(20) NOT NULL CONSTRAINT [DF_ReportedContents_Status] DEFAULT N'pending',
        [CreatedAt] DATETIME2(0) NOT NULL CONSTRAINT [DF_ReportedContents_CreatedAt] DEFAULT SYSUTCDATETIME(),
        
        CONSTRAINT [PK_ReportedContents] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_ReportedContents_Users] FOREIGN KEY ([ReportedBy]) 
            REFERENCES [core].[Users] ([UserId]),
        CONSTRAINT [CK_ReportedContents_TargetType] CHECK ([TargetType] IN (N'post', N'comment', N'photo')),
        CONSTRAINT [CK_ReportedContents_Status] CHECK ([Status] IN (N'pending', N'resolved', N'dismissed'))
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_ReportedContents_Target_Status' AND [object_id] = OBJECT_ID(N'community.ReportedContents'))
    CREATE INDEX [IX_ReportedContents_Target_Status] ON [community].[ReportedContents] ([TargetId], [TargetType], [Status]);
GO
