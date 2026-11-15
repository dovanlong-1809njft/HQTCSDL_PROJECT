-- Additive and rerunnable; never seeds or changes existing comments/reactions.
IF OBJECT_ID(N'community.CommentReactions', N'U') IS NULL
BEGIN
    CREATE TABLE community.CommentReactions (
        Id UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_CommentReactions_Id DEFAULT NEWSEQUENTIALID(),
        CommentId UNIQUEIDENTIFIER NOT NULL,
        UserId UNIQUEIDENTIFIER NOT NULL,
        Type NVARCHAR(20) NOT NULL,
        CreatedAt DATETIME2(0) NOT NULL CONSTRAINT DF_CommentReactions_CreatedAt DEFAULT SYSUTCDATETIME(),
        UpdatedAt DATETIME2(0) NOT NULL CONSTRAINT DF_CommentReactions_UpdatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_CommentReactions PRIMARY KEY (Id),
        CONSTRAINT UQ_CommentReactions_Comment_User UNIQUE (CommentId, UserId),
        CONSTRAINT CK_CommentReactions_Type CHECK (Type IN ('Like','Love','Haha','Wow','Sad','Angry')),
        CONSTRAINT FK_CommentReactions_Comments FOREIGN KEY (CommentId) REFERENCES community.Comments(Id) ON DELETE CASCADE,
        CONSTRAINT FK_CommentReactions_Users FOREIGN KEY (UserId) REFERENCES core.Users(UserId)
    );
    CREATE INDEX IX_CommentReactions_Comment_Type ON community.CommentReactions(CommentId, Type);
END;
GO
