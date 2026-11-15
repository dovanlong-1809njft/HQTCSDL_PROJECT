USE [$(DB_NAME)];
GO
CREATE OR ALTER PROCEDURE community.usp_DeliverDueReminders @BatchSize INT=50
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    IF @BatchSize<1 OR @BatchSize>500 THROW 51522,N'Batch không hợp lệ.',1;
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @Due TABLE(Id UNIQUEIDENTIFIER,EventId UNIQUEIDENTIFIER,ReminderTime DATETIME2(0),UserId UNIQUEIDENTIFIER);
        INSERT @Due SELECT TOP(@BatchSize) Id,EventId,ReminderTime,UserId FROM community.EventReminders WITH(UPDLOCK,READPAST,ROWLOCK)
            WHERE Status='pending' AND ReminderTime<=SYSUTCDATETIME() ORDER BY ReminderTime,Id;
        DECLARE @Created TABLE(Id UNIQUEIDENTIFIER);
        INSERT community.Notifications(UserId,FamilyId,EventId,ReminderId,Title,Body)
        OUTPUT inserted.Id INTO @Created
        SELECT u.UserId,e.FamilyId,e.Id,r.Id,e.Title,CONCAT(N'Sự kiện: ',e.Title,N' · ',CONVERT(NVARCHAR(19),e.EventDate,126),N' UTC')
        FROM @Due r JOIN community.Events e ON e.Id=r.EventId JOIN core.Users u ON u.IsActive=1 AND u.Role IN ('admin','family_head','member')
        WHERE (r.UserId IS NULL OR r.UserId=u.UserId)
            AND (EXISTS(SELECT 1 FROM genealogy.Members m WHERE m.UserId=u.UserId AND m.FamilyId=e.FamilyId) OR (r.UserId=u.UserId AND u.Role='admin'))
            AND NOT EXISTS(SELECT 1 FROM community.Notifications n WHERE n.ReminderId=r.Id AND n.UserId=u.UserId);
        UPDATE r SET Status='sent' FROM community.EventReminders r JOIN @Due due ON due.Id=r.Id;
        DECLARE @Count INT=(SELECT COUNT(*) FROM @Created);
        IF EXISTS(SELECT 1 FROM @Due)
            INSERT reports.AuditLog(UserId,Action) VALUES(NULL,CONCAT('reminder.dispatched; reminders=',(SELECT COUNT(*) FROM @Due),'; inbox=',@Count));
        COMMIT;
        SELECT @Count AS delivered;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER PROCEDURE community.usp_CancelReminder @ActorUserId UNIQUEIDENTIFIER,@EventId UNIQUEIDENTIFIER,@Id UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @Family UNIQUEIDENTIFIER,@Owner UNIQUEIDENTIFIER;
        SELECT @Family=e.FamilyId,@Owner=r.UserId FROM community.EventReminders r WITH(UPDLOCK,HOLDLOCK)
            JOIN community.Events e ON e.Id=r.EventId WHERE r.Id=@Id AND r.EventId=@EventId;
        IF @Family IS NULL THROW 51404,N'Không tìm thấy nhắc lịch.',1;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@Family;
        IF @Owner IS NULL OR @Owner<>@ActorUserId EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@Family,1;
        UPDATE community.EventReminders SET Status='cancelled' WHERE Id=@Id;
        INSERT reports.AuditLog(UserId,Action) VALUES(@ActorUserId,CONCAT('reminder.cancelled; id=',@Id));
        COMMIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO
