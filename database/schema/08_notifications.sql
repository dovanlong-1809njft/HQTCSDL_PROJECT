USE [$(DB_NAME)];
GO
IF COL_LENGTH('community.Posts','IsAnnouncement') IS NULL
    ALTER TABLE community.Posts ADD IsAnnouncement BIT NOT NULL CONSTRAINT DF_Posts_IsAnnouncement DEFAULT(0) WITH VALUES;
IF COL_LENGTH('community.EventReminders','UserId') IS NULL
    ALTER TABLE community.EventReminders ADD UserId UNIQUEIDENTIFIER NULL CONSTRAINT FK_EventReminders_User REFERENCES core.Users(UserId);
GO
IF OBJECT_ID('community.CK_EventReminders_Status','C') IS NOT NULL
    ALTER TABLE community.EventReminders DROP CONSTRAINT CK_EventReminders_Status;
ALTER TABLE community.EventReminders ADD CONSTRAINT CK_EventReminders_Status CHECK(Status IN ('pending','sent','failed','cancelled'));
GO
IF OBJECT_ID('community.Notifications','U') IS NULL
CREATE TABLE community.Notifications (
    Id UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_Notifications_Id DEFAULT NEWSEQUENTIALID() PRIMARY KEY,
    UserId UNIQUEIDENTIFIER NOT NULL REFERENCES core.Users(UserId),
    FamilyId UNIQUEIDENTIFIER NOT NULL REFERENCES core.Families(Id),
    EventId UNIQUEIDENTIFIER NULL,
    ReminderId UNIQUEIDENTIFIER NOT NULL,
    Title NVARCHAR(200) NOT NULL,
    Body NVARCHAR(600) NOT NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    ReadAt DATETIME2(0) NULL,
    CONSTRAINT UQ_Notifications_Reminder_User UNIQUE(ReminderId,UserId)
);
GO
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE name='IX_Notifications_User' AND object_id=OBJECT_ID('community.Notifications'))
    CREATE INDEX IX_Notifications_User ON community.Notifications(UserId,CreatedAt DESC);
GO
