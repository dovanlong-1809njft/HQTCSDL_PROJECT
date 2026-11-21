-- Additive migration. Legacy events are not automatically enrolled.
IF COL_LENGTH('community.Events','EndDate') IS NULL
    ALTER TABLE community.Events ADD EndDate DATETIME2(0) NULL;
IF COL_LENGTH('community.Events','CompletionEnabled') IS NULL
BEGIN
    ALTER TABLE community.Events ADD CompletionEnabled BIT NOT NULL CONSTRAINT DF_Events_CompletionEnabled DEFAULT(0) WITH VALUES;
    ALTER TABLE community.Events DROP CONSTRAINT DF_Events_CompletionEnabled;
    ALTER TABLE community.Events ADD CONSTRAINT DF_Events_CompletionEnabled DEFAULT(1) FOR CompletionEnabled;
END;
IF COL_LENGTH('community.Events','CompletionHandledAt') IS NULL
    ALTER TABLE community.Events ADD CompletionHandledAt DATETIME2(0) NULL;
GO
IF NOT EXISTS(SELECT 1 FROM sys.check_constraints WHERE name='CK_Events_EndDate' AND parent_object_id=OBJECT_ID('community.Events'))
    ALTER TABLE community.Events ADD CONSTRAINT CK_Events_EndDate CHECK(EndDate IS NULL OR EndDate>EventDate);
GO
IF COL_LENGTH('community.Notifications','NotificationType') IS NULL
    ALTER TABLE community.Notifications ADD NotificationType VARCHAR(20) NOT NULL CONSTRAINT DF_Notifications_Type DEFAULT('reminder') WITH VALUES;
IF COL_LENGTH('community.Notifications','SourceId') IS NULL
    ALTER TABLE community.Notifications ADD SourceId UNIQUEIDENTIFIER NULL;
IF EXISTS(SELECT 1 FROM sys.key_constraints WHERE parent_object_id=OBJECT_ID('community.Notifications') AND name='UQ_Notifications_Reminder_User')
    ALTER TABLE community.Notifications DROP CONSTRAINT UQ_Notifications_Reminder_User;
IF EXISTS(SELECT 1 FROM sys.columns WHERE object_id=OBJECT_ID('community.Notifications') AND name='ReminderId' AND is_nullable=0)
    ALTER TABLE community.Notifications ALTER COLUMN ReminderId UNIQUEIDENTIFIER NULL;
GO
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('community.Notifications') AND name='UX_Notifications_Reminder_User')
    CREATE UNIQUE INDEX UX_Notifications_Reminder_User ON community.Notifications(ReminderId,UserId) WHERE ReminderId IS NOT NULL;
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('community.Notifications') AND name='UX_Notifications_Completion_User')
    CREATE UNIQUE INDEX UX_Notifications_Completion_User ON community.Notifications(SourceId,UserId) WHERE NotificationType='event_ended';
IF NOT EXISTS(SELECT 1 FROM sys.check_constraints WHERE parent_object_id=OBJECT_ID('community.Notifications') AND name='CK_Notifications_Source')
    ALTER TABLE community.Notifications ADD CONSTRAINT CK_Notifications_Source CHECK(
        (NotificationType='reminder' AND ReminderId IS NOT NULL) OR
        (NotificationType='event_ended' AND ReminderId IS NULL AND SourceId IS NOT NULL));
-- EventId is the live FK; SourceId is a historical deduplication key retained after deletion.
IF NOT EXISTS(SELECT 1 FROM sys.foreign_keys WHERE name='FK_Notifications_Event')
    ALTER TABLE community.Notifications ADD CONSTRAINT FK_Notifications_Event FOREIGN KEY(EventId) REFERENCES community.Events(Id);
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('community.Events') AND name='IX_Events_Completion')
    CREATE INDEX IX_Events_Completion ON community.Events(CompletionEnabled,CompletionHandledAt,EndDate);
GO
