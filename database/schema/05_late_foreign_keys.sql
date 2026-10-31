USE [$(DB_NAME)];
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE [name] = N'FK_MemberVerifications_Members')
BEGIN
    ALTER TABLE [core].[MemberVerifications]
        ADD CONSTRAINT [FK_MemberVerifications_Members]
        FOREIGN KEY ([MemberId]) REFERENCES [genealogy].[Members] ([Id]);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_MemberVerifications_MemberId' AND [object_id] = OBJECT_ID(N'core.MemberVerifications'))
    CREATE INDEX [IX_MemberVerifications_MemberId] ON [core].[MemberVerifications] ([MemberId]);
GO
