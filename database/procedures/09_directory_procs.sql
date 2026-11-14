USE [$(DB_NAME)];
GO
CREATE OR ALTER PROCEDURE genealogy.usp_ManageHistory
    @ActorUserId UNIQUEIDENTIFIER,@MemberId UNIQUEIDENTIFIER,@Resource VARCHAR(20),@Action VARCHAR(10),
    @Id UNIQUEIDENTIFIER=NULL,@Institution NVARCHAR(200)=NULL,@Degree NVARCHAR(200)=NULL,
    @Company NVARCHAR(200)=NULL,@Position NVARCHAR(200)=NULL,@StartDate DATE=NULL,@EndDate DATE=NULL
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @Family UNIQUEIDENTIFIER,@Branch UNIQUEIDENTIFIER,@Owner UNIQUEIDENTIFIER,@Role NVARCHAR(20);
        SELECT @Family=FamilyId,@Branch=BranchId,@Owner=UserId FROM genealogy.Members WITH(XLOCK,HOLDLOCK) WHERE Id=@MemberId;
        IF @Family IS NULL THROW 51404,N'Không tìm thấy thành viên.',1;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@Family;
        SELECT @Role=Role FROM core.Users WHERE UserId=@ActorUserId;
        IF @Role<>'admin' AND ISNULL(@Owner,'00000000-0000-0000-0000-000000000000')<>@ActorUserId
            AND NOT(@Role='family_head' AND EXISTS(SELECT 1 FROM genealogy.Members WHERE UserId=@ActorUserId AND BranchId=@Branch AND FamilyId=@Family))
            THROW 51403,N'Chỉ được sửa hồ sơ của mình hoặc thành viên trong chi đang quản lý.',1;
        IF @Resource NOT IN ('educations','work') OR @Action NOT IN ('create','update','delete') THROW 51522,N'Thao tác không hợp lệ.',1;
        IF EXISTS(SELECT 1 FROM heritage.KnowledgeChunks WHERE SourceType='member' AND SourceId=@MemberId)
            THROW 51509,N'Hồ sơ đã được AI lập chỉ mục; cần đồng bộ chỉ mục trước khi sửa.',1;
        IF @Action<>'delete' AND (@EndDate<@StartDate OR (@Resource='educations' AND NULLIF(LTRIM(RTRIM(@Institution)),N'') IS NULL)
            OR (@Resource='work' AND (NULLIF(LTRIM(RTRIM(@Company)),N'') IS NULL OR NULLIF(LTRIM(RTRIM(@Position)),N'') IS NULL)))
            THROW 51522,N'Tên trường/công việc hoặc khoảng thời gian chưa hợp lệ.',1;
        IF @Resource='educations'
        BEGIN
            IF @Action<>'create' AND NOT EXISTS(SELECT 1 FROM genealogy.Educations WITH(UPDLOCK,HOLDLOCK) WHERE Id=@Id AND MemberId=@MemberId) THROW 51404,N'Không tìm thấy học vấn.',1;
            IF @Action='create'
            BEGIN
                SET @Id=NEWID();
                INSERT genealogy.Educations(Id,MemberId,Institution,Degree,StartDate,EndDate) VALUES(@Id,@MemberId,@Institution,@Degree,@StartDate,@EndDate);
            END
            ELSE IF @Action='update' UPDATE genealogy.Educations SET Institution=@Institution,Degree=@Degree,StartDate=@StartDate,EndDate=@EndDate WHERE Id=@Id;
            ELSE DELETE genealogy.Educations WHERE Id=@Id;
        END
        ELSE
        BEGIN
            IF @Action<>'create' AND NOT EXISTS(SELECT 1 FROM genealogy.WorkHistories WITH(UPDLOCK,HOLDLOCK) WHERE Id=@Id AND MemberId=@MemberId) THROW 51404,N'Không tìm thấy công việc.',1;
            IF @Action='create'
            BEGIN
                SET @Id=NEWID();
                INSERT genealogy.WorkHistories(Id,MemberId,Company,Position,StartDate,EndDate) VALUES(@Id,@MemberId,@Company,@Position,@StartDate,@EndDate);
            END
            ELSE IF @Action='update' UPDATE genealogy.WorkHistories SET Company=@Company,Position=@Position,StartDate=@StartDate,EndDate=@EndDate WHERE Id=@Id;
            ELSE DELETE genealogy.WorkHistories WHERE Id=@Id;
        END;
        INSERT reports.AuditLog(UserId,Action) VALUES(@ActorUserId,CONCAT('directory.',@Resource,'.',@Action,'; id=',@Id));
        COMMIT; SELECT @Id AS id;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO
