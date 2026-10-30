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

-- 3. EventParticipants
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

-- 4. Posts
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

-- 5. Comments
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

-- 6. Reactions
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
