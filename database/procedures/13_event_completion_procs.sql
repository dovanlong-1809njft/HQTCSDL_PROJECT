CREATE OR ALTER PROCEDURE community.usp_UpdateEventSchedule
    @ActorUserId UNIQUEIDENTIFIER,@EventId UNIQUEIDENTIFIER,@Title NVARCHAR(200),
    @EventDate DATETIME2(0),@Location NVARCHAR(500),@EndDate DATETIME2(0)=NULL
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        IF NOT EXISTS(SELECT 1 FROM community.Events WITH(UPDLOCK,HOLDLOCK) WHERE Id=@EventId)
            THROW 51404,N'[TV4_SQL:51404] Không tìm thấy sự kiện.',1;
        IF @EndDate IS NOT NULL AND @EndDate<=@EventDate
            THROW 51522,N'[TV4_SQL:51522] Kết thúc phải sau bắt đầu.',1;
        -- Existing procedure keeps authorization, reminder validation and audit unchanged.
        EXEC community.usp_ManageEvent @ActorUserId=@ActorUserId,@EventId=@EventId,@Action='update',
            @Title=@Title,@EventDate=@EventDate,@Location=@Location;
        UPDATE community.Events SET EndDate=@EndDate,
            CompletionEnabled=CASE WHEN @EndDate>SYSUTCDATETIME() THEN 1 ELSE CompletionEnabled END
            WHERE Id=@EventId;
        COMMIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER PROCEDURE community.usp_DeliverEndedEvents @BatchSize INT=50
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    IF @BatchSize<1 OR @BatchSize>500 THROW 51522,N'Batch không hợp lệ.',1;
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @Now DATETIME2(0)=SYSUTCDATETIME();
        DECLARE @Due TABLE(Id UNIQUEIDENTIFIER PRIMARY KEY,FamilyId UNIQUEIDENTIFIER,Title NVARCHAR(200));
        INSERT @Due SELECT TOP(@BatchSize) Id,FamilyId,Title FROM community.Events WITH(UPDLOCK,READPAST,ROWLOCK)
            WHERE CompletionEnabled=1 AND CompletionHandledAt IS NULL AND EndDate IS NOT NULL AND EndDate<=@Now
            ORDER BY EndDate,Id;
        INSERT community.Notifications(UserId,FamilyId,EventId,ReminderId,NotificationType,SourceId,Title,Body)
        SELECT u.UserId,e.FamilyId,e.Id,NULL,'event_ended',e.Id,N'Sự kiện đã kết thúc',
            CONCAT(e.Title,N' đã kết thúc. Bạn có thể xem lại thông tin và hình ảnh của sự kiện.')
        FROM @Due e JOIN core.Users u ON u.IsActive=1 AND u.Role IN ('admin','family_head','member')
        WHERE EXISTS(SELECT 1 FROM genealogy.Members m WHERE m.FamilyId=e.FamilyId AND m.UserId=u.UserId)
          AND NOT EXISTS(SELECT 1 FROM community.Notifications n WHERE n.NotificationType='event_ended' AND n.SourceId=e.Id AND n.UserId=u.UserId);
        DECLARE @Delivered INT=@@ROWCOUNT;
        UPDATE e SET CompletionHandledAt=@Now FROM community.Events e JOIN @Due d ON d.Id=e.Id;
        COMMIT;
        SELECT @Delivered AS delivered;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO
IF DATABASE_PRINCIPAL_ID('role_backend') IS NOT NULL
BEGIN
    GRANT EXECUTE ON OBJECT::community.usp_UpdateEventSchedule TO role_backend;
    GRANT EXECUTE ON OBJECT::community.usp_DeliverEndedEvents TO role_backend;
END;
GO
