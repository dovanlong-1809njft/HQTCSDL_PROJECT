USE [$(DB_NAME)];
GO
CREATE OR ALTER PROCEDURE community.usp_ManagePost
    @ActorUserId UNIQUEIDENTIFIER,@PostId UNIQUEIDENTIFIER,@Action VARCHAR(10),
    @Content NVARCHAR(MAX)=NULL,@MediaJson NVARCHAR(MAX)=NULL,@IsAnnouncement BIT=0
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @Family UNIQUEIDENTIFIER,@Owner UNIQUEIDENTIFIER,@Role NVARCHAR(20);
        SELECT @Family=FamilyId,@Owner=UserId FROM community.Posts WITH(XLOCK,HOLDLOCK) WHERE Id=@PostId;
        IF @Family IS NULL THROW 51404,N'Bài viết không còn tồn tại.',1;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@Family;
        SELECT @Role=Role FROM core.Users WHERE UserId=@ActorUserId;
        IF @Owner<>@ActorUserId AND @Role<>'admin' THROW 51403,N'Chỉ tác giả hoặc quản trị viên được sửa/xóa bài.',1;
        IF EXISTS(SELECT 1 FROM heritage.KnowledgeChunks WHERE SourceType='post' AND SourceId=@PostId)
            THROW 51509,N'Bài đã được AI lập chỉ mục; cần đồng bộ chỉ mục trước khi thay đổi.',1;
        IF @Action NOT IN ('update','delete') THROW 51522,N'Thao tác không hợp lệ.',1;
        IF @Action='update'
        BEGIN
            IF NULLIF(LTRIM(RTRIM(@Content)),N'') IS NULL OR (@MediaJson IS NOT NULL AND ISJSON(@MediaJson)=0) THROW 51522,N'Nội dung chưa hợp lệ.',1;
            IF @IsAnnouncement=1 EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@Family,1;
            UPDATE community.Posts SET Content=@Content,IsAnnouncement=@IsAnnouncement WHERE Id=@PostId;
        END;
        DECLARE @Media TABLE(Url NVARCHAR(2048) COLLATE Latin1_General_100_BIN2);
        IF @Action='update'
            INSERT @Media SELECT url FROM OPENJSON(@MediaJson) WITH(url NVARCHAR(2048) '$.url');
        DECLARE @RemovedMedia TABLE(Id UNIQUEIDENTIFIER);
        DELETE m OUTPUT deleted.Id INTO @RemovedMedia
        FROM community.PostMedia m WHERE m.PostId=@PostId
            AND NOT EXISTS(SELECT 1 FROM @Media incoming WHERE incoming.Url=m.MediaUrl COLLATE Latin1_General_100_BIN2);
        UPDATE community.ReportedContents SET Status='resolved' WHERE Status='pending' AND (
            (TargetType='photo' AND TargetId IN(SELECT Id FROM @RemovedMedia)) OR
            (@Action='delete' AND ((TargetType='post' AND TargetId=@PostId) OR
            (TargetType='comment' AND TargetId IN(SELECT Id FROM community.Comments WHERE PostId=@PostId)))));
        IF @Action='delete' DELETE community.Posts WHERE Id=@PostId;
        ELSE
            INSERT community.PostMedia(PostId,MediaUrl,MediaType)
            SELECT DISTINCT @PostId,incoming.Url,'image' FROM @Media incoming
            WHERE NOT EXISTS(SELECT 1 FROM community.PostMedia m WHERE m.PostId=@PostId
                AND m.MediaUrl COLLATE Latin1_General_100_BIN2=incoming.Url);
        INSERT reports.AuditLog(UserId,Action) VALUES(@ActorUserId,CONCAT('post.',@Action,'; id=',@PostId));
        COMMIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER PROCEDURE community.usp_ManageComment
    @ActorUserId UNIQUEIDENTIFIER,@Id UNIQUEIDENTIFIER,@Action VARCHAR(10),@Content NVARCHAR(2000)=NULL
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @Family UNIQUEIDENTIFIER,@Owner UNIQUEIDENTIFIER;
        SELECT @Family=p.FamilyId,@Owner=c.UserId FROM community.Comments c WITH(UPDLOCK,HOLDLOCK)
            JOIN community.Posts p WITH(HOLDLOCK) ON p.Id=c.PostId WHERE c.Id=@Id;
        IF @Family IS NULL THROW 51404,N'Bình luận không còn tồn tại.',1;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@Family;
        IF @Owner<>@ActorUserId AND NOT EXISTS(SELECT 1 FROM core.Users WHERE UserId=@ActorUserId AND Role='admin') THROW 51403,N'Không được sửa/xóa bình luận của người khác.',1;
        IF @Action='update'
        BEGIN
            IF NULLIF(LTRIM(RTRIM(@Content)),N'') IS NULL THROW 51522,N'Bình luận không được trống.',1;
            UPDATE community.Comments SET Content=@Content WHERE Id=@Id;
        END
        ELSE IF @Action='delete'
        BEGIN
            UPDATE community.ReportedContents SET Status='resolved' WHERE TargetType='comment' AND TargetId=@Id AND Status='pending';
            DELETE community.Comments WHERE Id=@Id;
        END
        ELSE THROW 51522,N'Thao tác không hợp lệ.',1;
        INSERT reports.AuditLog(UserId,Action) VALUES(@ActorUserId,CONCAT('comment.',@Action,'; id=',@Id));
        COMMIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER PROCEDURE community.usp_ManageEvent
    @ActorUserId UNIQUEIDENTIFIER,@EventId UNIQUEIDENTIFIER,@Action VARCHAR(20),
    @Title NVARCHAR(200)=NULL,@EventDate DATETIME2(0)=NULL,@Location NVARCHAR(500)=NULL,
    @MemberId UNIQUEIDENTIFIER=NULL,@RsvpStatus NVARCHAR(20)=NULL,@GalleryId UNIQUEIDENTIFIER=NULL
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @Family UNIQUEIDENTIFIER,@Owner UNIQUEIDENTIFIER;
        SELECT @Family=FamilyId FROM community.Events WITH(UPDLOCK,HOLDLOCK) WHERE Id=@EventId;
        IF @Family IS NULL THROW 51404,N'Sự kiện không còn tồn tại.',1;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@Family;
        IF @Action='gallery-delete'
        BEGIN
            SELECT @Owner=UploadedBy FROM community.EventGalleries WITH(UPDLOCK,HOLDLOCK) WHERE Id=@GalleryId AND EventId=@EventId;
            IF @Owner IS NULL THROW 51404,N'Không tìm thấy ảnh.',1;
            IF @Owner<>@ActorUserId EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@Family,1;
            DELETE community.EventGalleries WHERE Id=@GalleryId;
        END
        ELSE
        BEGIN
            EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@Family,1;
            IF @Action='update'
            BEGIN
                IF NULLIF(LTRIM(RTRIM(@Title)),N'') IS NULL OR @EventDate IS NULL THROW 51522,N'Tên hoặc thời gian không hợp lệ.',1;
                IF EXISTS(SELECT 1 FROM community.EventReminders WHERE EventId=@EventId AND Status='pending' AND ReminderTime>@EventDate)
                    THROW 51509,N'Hãy hủy các nhắc lịch sau thời gian sự kiện mới trước khi đổi lịch.',1;
                UPDATE community.Events SET Title=@Title,EventDate=@EventDate,Location=@Location WHERE Id=@EventId;
            END
            ELSE IF @Action='delete'
            BEGIN
                UPDATE community.Notifications SET EventId=NULL WHERE EventId=@EventId;
                DELETE community.Events WHERE Id=@EventId;
            END
            ELSE IF @Action='participant'
            BEGIN
                IF NOT EXISTS(SELECT 1 FROM genealogy.Members WITH(HOLDLOCK) WHERE Id=@MemberId AND FamilyId=@Family) THROW 51522,N'Thành viên không thuộc gia đình.',1;
                IF @RsvpStatus NOT IN ('Pending','Going','Maybe','Declined') OR @RsvpStatus IS NULL THROW 51522,N'Trạng thái không hợp lệ.',1;
                EXEC community.usp_UpsertEventRsvp @EventId,@MemberId,@RsvpStatus;
            END
            ELSE THROW 51522,N'Thao tác không hợp lệ.',1;
        END;
        INSERT reports.AuditLog(UserId,Action) VALUES(@ActorUserId,CONCAT('event.',@Action,'; id=',@EventId,'; member=',@MemberId));
        COMMIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO
