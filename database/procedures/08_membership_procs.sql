USE [$(DB_NAME)];
GO
SET QUOTED_IDENTIFIER ON;
GO

-- All record changes share the same access check and transaction as the write.
CREATE OR ALTER PROCEDURE genealogy.usp_ManageRecord
    @ActorUserId UNIQUEIDENTIFIER, @FamilyId UNIQUEIDENTIFIER,
    @Resource VARCHAR(20), @Action VARCHAR(10), @Id UNIQUEIDENTIFIER = NULL,
    @Name NVARCHAR(200) = NULL, @BranchId UNIQUEIDENTIFIER = NULL,
    @BirthDate DATE = NULL, @Location NVARCHAR(300) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        IF @Resource NOT IN ('families','branches','members') OR @Action NOT IN ('create','update','delete')
            THROW 51522, N'Thao tác không hợp lệ.', 1;
        IF @Action <> 'delete' AND NULLIF(LTRIM(RTRIM(@Name)),N'') IS NULL
            THROW 51522, N'Tên không được để trống.', 1;
        IF @Resource='families' AND @Action IN ('create','delete')
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM core.Users WITH (HOLDLOCK) WHERE UserId=@ActorUserId AND Role='admin' AND IsActive=1)
                THROW 51403, N'Chỉ quản trị viên được tạo hoặc xóa gia đình.', 1;
        END;
        IF NOT (@Resource='families' AND @Action='create')
            EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@FamilyId,1;
        DECLARE @Role NVARCHAR(20),@ManagedBranch UNIQUEIDENTIFIER;
        SELECT @Role=Role FROM core.Users WHERE UserId=@ActorUserId;
        IF @Role='family_head'
        BEGIN
            SELECT @ManagedBranch=BranchId FROM genealogy.Members WITH (HOLDLOCK) WHERE UserId=@ActorUserId AND FamilyId=@FamilyId;
            IF @Resource='families' OR @ManagedBranch IS NULL
                THROW 51403,N'Chỉ quản trị viên được thay đổi gia đình; trưởng chi cần liên kết một chi.',1;
            IF @Resource='branches' AND (@Action<>'update' OR @Id<>@ManagedBranch)
                THROW 51403,N'Trưởng chi chỉ được đổi tên chi đang quản lý.',1;
            IF @Resource='members'
            BEGIN
                IF @Action<>'create' AND NOT EXISTS (SELECT 1 FROM genealogy.Members WITH (HOLDLOCK) WHERE Id=@Id AND BranchId=@ManagedBranch)
                    THROW 51403,N'Thành viên không thuộc chi đang quản lý.',1;
                IF @Action<>'delete' AND (@BranchId IS NULL OR @BranchId<>@ManagedBranch)
                    THROW 51403,N'Chỉ quản trị viên được chuyển chi của thành viên.',1;
            END;
        END;
        IF @Resource='members'
        BEGIN
            DECLARE @GraphLock INT;
            EXEC @GraphLock=sp_getapplock @Resource=N'genealogy.MemberClosure',@LockMode=N'Exclusive',@LockOwner=N'Transaction',@LockTimeout=10000;
            IF @GraphLock<0 THROW 50100,N'Không thể khóa gia phả; vui lòng thử lại.',1;
        END;

        IF @Resource='families'
        BEGIN
            IF @Action='create'
            BEGIN
                SET @Id=NEWID();
                INSERT core.Families(Id,Name) VALUES (@Id,LTRIM(RTRIM(@Name)));
            END
            ELSE IF @Action='update'
                UPDATE core.Families SET Name=LTRIM(RTRIM(@Name)) WHERE Id=@FamilyId;
            ELSE
            BEGIN
                IF EXISTS (SELECT 1 FROM core.Branches WITH (UPDLOCK,HOLDLOCK) WHERE FamilyId=@FamilyId)
                    OR EXISTS (SELECT 1 FROM genealogy.Members WITH (UPDLOCK,HOLDLOCK) WHERE FamilyId=@FamilyId)
                    OR EXISTS (SELECT 1 FROM community.Posts WITH (UPDLOCK,HOLDLOCK) WHERE FamilyId=@FamilyId)
                    OR EXISTS (SELECT 1 FROM community.Events WITH (UPDLOCK,HOLDLOCK) WHERE FamilyId=@FamilyId)
                    OR EXISTS (SELECT 1 FROM heritage.Items WITH (UPDLOCK,HOLDLOCK) WHERE FamilyId=@FamilyId)
                    OR EXISTS (SELECT 1 FROM heritage.KnowledgeChunks WITH (UPDLOCK,HOLDLOCK) WHERE FamilyId=@FamilyId)
                    OR EXISTS (SELECT 1 FROM reports.AiChatMessages WITH (UPDLOCK,HOLDLOCK) WHERE FamilyId=@FamilyId)
                    THROW 51509,N'Gia đình còn dữ liệu liên quan; không thể xóa.',1;
                DELETE core.Families WHERE Id=@FamilyId;
            END;
        END
        ELSE IF @Resource='branches'
        BEGIN
            IF @Action<>'create' AND NOT EXISTS (SELECT 1 FROM core.Branches WITH (UPDLOCK,HOLDLOCK) WHERE Id=@Id AND FamilyId=@FamilyId)
                THROW 51404,N'Không tìm thấy chi nhánh.',1;
            IF @Action='create'
            BEGIN
                SET @Id=NEWID();
                INSERT core.Branches(Id,FamilyId,Name) VALUES(@Id,@FamilyId,LTRIM(RTRIM(@Name)));
            END
            ELSE IF @Action='update' UPDATE core.Branches SET Name=LTRIM(RTRIM(@Name)) WHERE Id=@Id;
            ELSE
            BEGIN
                IF EXISTS (SELECT 1 FROM genealogy.Members WITH (UPDLOCK,HOLDLOCK) WHERE BranchId=@Id)
                    THROW 51509,N'Chi nhánh còn thành viên; hãy chuyển họ trước khi xóa.',1;
                DELETE core.Branches WHERE Id=@Id;
            END;
        END
        ELSE
        BEGIN
            IF @Action<>'create' AND NOT EXISTS (SELECT 1 FROM genealogy.Members WITH (XLOCK,HOLDLOCK) WHERE Id=@Id AND FamilyId=@FamilyId)
                THROW 51404,N'Không tìm thấy thành viên.',1;
            IF @BranchId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM core.Branches WITH (HOLDLOCK) WHERE Id=@BranchId AND FamilyId=@FamilyId)
                THROW 51522,N'Chi nhánh không thuộc gia đình đã chọn.',1;
            IF @BirthDate>CONVERT(DATE,SYSUTCDATETIME()) THROW 51522,N'Ngày sinh không được ở tương lai.',1;
            IF @Action='create'
            BEGIN
                SET @Id=NEWID();
                INSERT genealogy.Members(Id,FamilyId,BranchId,FullName,BirthDate,Location)
                    VALUES(@Id,@FamilyId,@BranchId,LTRIM(RTRIM(@Name)),@BirthDate,@Location);
                INSERT genealogy.MemberClosure(AncestorId,DescendantId,Depth) VALUES(@Id,@Id,0);
            END
            ELSE IF @Action='update'
            BEGIN
                IF EXISTS (SELECT 1 FROM heritage.KnowledgeChunks WHERE SourceType='member' AND SourceId=@Id)
                    THROW 51509,N'Hồ sơ đã được AI lập chỉ mục; cần cập nhật chỉ mục trước khi sửa.',1;
                UPDATE genealogy.Members SET FullName=LTRIM(RTRIM(@Name)),BranchId=@BranchId,BirthDate=@BirthDate,Location=@Location WHERE Id=@Id;
            END
            ELSE
            BEGIN
                IF EXISTS (SELECT 1 FROM genealogy.Members WHERE Id=@Id AND UserId IS NOT NULL)
                    OR EXISTS (SELECT 1 FROM genealogy.ParentChild WHERE ParentId=@Id OR ChildId=@Id)
                    OR EXISTS (SELECT 1 FROM genealogy.Marriages WHERE Spouse1Id=@Id OR Spouse2Id=@Id)
                    OR EXISTS (SELECT 1 FROM core.MemberVerifications WHERE MemberId=@Id)
                    OR EXISTS (SELECT 1 FROM genealogy.Educations WHERE MemberId=@Id)
                    OR EXISTS (SELECT 1 FROM genealogy.WorkHistories WHERE MemberId=@Id)
                    OR EXISTS (SELECT 1 FROM heritage.Honors WHERE MemberId=@Id)
                    OR EXISTS (SELECT 1 FROM community.EventParticipants WITH (UPDLOCK,HOLDLOCK) WHERE MemberId=@Id)
                    OR EXISTS (SELECT 1 FROM heritage.KnowledgeChunks WITH (UPDLOCK,HOLDLOCK) WHERE SourceType='member' AND SourceId=@Id)
                    THROW 51509,N'Thành viên còn tài khoản, quan hệ hoặc lịch sử liên quan; không thể xóa.',1;
                DELETE genealogy.MemberClosure WHERE AncestorId=@Id OR DescendantId=@Id;
                DELETE genealogy.Members WHERE Id=@Id;
            END;
        END;
        INSERT reports.AuditLog(UserId,Action) VALUES(@ActorUserId,CONCAT('genealogy.',@Resource,'.',@Action,'; id=',COALESCE(@Id,@FamilyId)));
        COMMIT;
        SELECT COALESCE(@Id,@FamilyId) AS id;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE genealogy.usp_UpdateOwnProfile
    @ActorUserId UNIQUEIDENTIFIER, @Name NVARCHAR(200), @BirthDate DATE=NULL, @Location NVARCHAR(300)=NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        IF NULLIF(LTRIM(RTRIM(@Name)),N'') IS NULL OR @BirthDate>CONVERT(DATE,SYSUTCDATETIME())
            THROW 51522,N'Tên hoặc ngày sinh không hợp lệ.',1;
        IF NOT EXISTS (SELECT 1 FROM core.Users WITH (UPDLOCK,HOLDLOCK) WHERE UserId=@ActorUserId AND IsActive=1)
            THROW 51403,N'Tài khoản không hoạt động.',1;
        DECLARE @MemberId UNIQUEIDENTIFIER;
        SELECT @MemberId=Id FROM genealogy.Members WITH (XLOCK,HOLDLOCK) WHERE UserId=@ActorUserId;
        IF @MemberId IS NOT NULL AND EXISTS (SELECT 1 FROM heritage.KnowledgeChunks WHERE SourceType='member' AND SourceId=@MemberId)
            THROW 51509,N'Hồ sơ đã được AI lập chỉ mục; cần cập nhật chỉ mục trước khi sửa.',1;
        UPDATE core.Users SET FullName=LTRIM(RTRIM(@Name)) WHERE UserId=@ActorUserId;
        UPDATE genealogy.Members SET FullName=LTRIM(RTRIM(@Name)),BirthDate=@BirthDate,Location=@Location WHERE Id=@MemberId;
        INSERT reports.AuditLog(UserId,Action) VALUES(@ActorUserId,N'profile.updated');
        COMMIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE core.usp_RequestMemberVerification
    @ActorUserId UNIQUEIDENTIFIER, @MemberId UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        IF NOT EXISTS (SELECT 1 FROM core.Users WITH (UPDLOCK,HOLDLOCK) WHERE UserId=@ActorUserId AND IsActive=1 AND Role IN ('member','family_head','admin'))
            THROW 51403,N'Không có quyền gửi yêu cầu xác minh.',1;
        IF EXISTS (SELECT 1 FROM genealogy.Members WITH (UPDLOCK,HOLDLOCK) WHERE UserId=@ActorUserId)
            THROW 51509,N'Tài khoản đã liên kết hồ sơ gia phả.',1;
        IF NOT EXISTS (SELECT 1 FROM genealogy.Members WITH (UPDLOCK,HOLDLOCK) WHERE Id=@MemberId AND UserId IS NULL)
            THROW 51509,N'Hồ sơ không còn khả dụng để xác minh.',1;
        IF EXISTS (SELECT 1 FROM core.MemberVerifications WITH (UPDLOCK,HOLDLOCK) WHERE UserId=@ActorUserId AND Status='pending')
            THROW 51509,N'Bạn đang có yêu cầu chờ duyệt.',1;
        IF EXISTS (SELECT 1 FROM core.MemberVerifications WHERE UserId=@ActorUserId AND MemberId=@MemberId)
            UPDATE core.MemberVerifications SET Status='pending',CreatedAt=SYSUTCDATETIME() WHERE UserId=@ActorUserId AND MemberId=@MemberId;
        ELSE INSERT core.MemberVerifications(UserId,MemberId) VALUES(@ActorUserId,@MemberId);
        INSERT reports.AuditLog(UserId,Action) VALUES(@ActorUserId,CONCAT('verification.requested; member=',@MemberId));
        COMMIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE genealogy.usp_ManageRelationship
    @ActorUserId UNIQUEIDENTIFIER, @FamilyId UNIQUEIDENTIFIER,
    @Kind VARCHAR(20), @Action VARCHAR(10), @FirstId UNIQUEIDENTIFIER=NULL,
    @SecondId UNIQUEIDENTIFIER=NULL, @Id UNIQUEIDENTIFIER=NULL, @MarriedDate DATE=NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@FamilyId,1;
        DECLARE @LockResult INT;
        EXEC @LockResult=sp_getapplock @Resource=N'genealogy.MemberClosure',@LockMode=N'Exclusive',@LockOwner=N'Transaction',@LockTimeout=10000;
        IF @LockResult<0 THROW 50100,N'Không thể khóa gia phả; vui lòng thử lại.',1;
        IF @Kind NOT IN ('parent-child','marriages') OR @Action NOT IN ('create','delete') THROW 51522,N'Thao tác không hợp lệ.',1;
        IF @Action='delete' AND @Kind='parent-child'
            SELECT @FirstId=ParentId,@SecondId=ChildId FROM genealogy.ParentChild WHERE Id=@Id;
        IF @Action='delete' AND @Kind='marriages'
            SELECT @FirstId=Spouse1Id,@SecondId=Spouse2Id FROM genealogy.Marriages WHERE Id=@Id;
        IF EXISTS (SELECT 1 FROM core.Users WHERE UserId=@ActorUserId AND Role='family_head')
        BEGIN
            DECLARE @ManagedBranch UNIQUEIDENTIFIER;
            SELECT @ManagedBranch=BranchId FROM genealogy.Members WITH (HOLDLOCK) WHERE UserId=@ActorUserId AND FamilyId=@FamilyId;
            IF @ManagedBranch IS NULL OR NOT EXISTS (SELECT 1 FROM genealogy.Members WHERE BranchId=@ManagedBranch
                AND (Id=@SecondId OR (@Kind='marriages' AND Id=@FirstId)))
                THROW 51403,N'Quan hệ không thuộc chi đang quản lý.',1;
        END;
        IF @Action='create'
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM genealogy.Members WITH (HOLDLOCK) WHERE Id=@FirstId AND FamilyId=@FamilyId)
                OR NOT EXISTS (SELECT 1 FROM genealogy.Members WITH (HOLDLOCK) WHERE Id=@SecondId AND FamilyId=@FamilyId)
                THROW 51522,N'Cả hai thành viên phải thuộc gia đình đã chọn.',1;
            IF @Kind='parent-child'
            BEGIN
                EXEC genealogy.usp_AddChildNode @FirstId,@SecondId,@Id OUTPUT;
                -- A new edge must not make an existing marriage consanguineous.
                IF EXISTS (SELECT 1 FROM genealogy.Marriages m
                    JOIN genealogy.Members owner ON owner.Id=m.Spouse1Id AND owner.FamilyId=@FamilyId
                    JOIN genealogy.MemberClosure a ON a.DescendantId=m.Spouse1Id
                    JOIN genealogy.MemberClosure b ON b.DescendantId=m.Spouse2Id AND b.AncestorId=a.AncestorId
                    WHERE (a.Depth<=2 AND b.Depth<=2) OR a.Depth=0 OR b.Depth=0)
                    THROW 50204,N'Quan hệ mới làm hôn nhân hiện có vi phạm quy tắc huyết thống.',1;
            END
            ELSE EXEC genealogy.usp_AddMarriage @FirstId,@SecondId,@MarriedDate,3,@Id OUTPUT;
        END
        ELSE IF @Kind='parent-child'
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM genealogy.ParentChild p JOIN genealogy.Members m ON m.Id=p.ParentId JOIN genealogy.Members c ON c.Id=p.ChildId WHERE p.Id=@Id AND m.FamilyId=@FamilyId AND c.FamilyId=@FamilyId)
                THROW 51404,N'Không tìm thấy quan hệ.',1;
            DELETE genealogy.ParentChild WHERE Id=@Id;
            -- Recompute minimum depths: another parent may still supply a path.
            DELETE c FROM genealogy.MemberClosure c JOIN genealogy.Members m ON m.Id=c.AncestorId WHERE m.FamilyId=@FamilyId;
            ;WITH Paths AS (
                SELECT Id AS AncestorId,Id AS DescendantId,0 AS Depth FROM genealogy.Members WHERE FamilyId=@FamilyId
                UNION ALL
                SELECT p.AncestorId,e.ChildId,p.Depth+1 FROM Paths p JOIN genealogy.ParentChild e ON e.ParentId=p.DescendantId
            )
            INSERT genealogy.MemberClosure(AncestorId,DescendantId,Depth)
            SELECT AncestorId,DescendantId,MIN(Depth) FROM Paths GROUP BY AncestorId,DescendantId OPTION(MAXRECURSION 32767);
        END
        ELSE
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM genealogy.Marriages p JOIN genealogy.Members m ON m.Id=p.Spouse1Id JOIN genealogy.Members c ON c.Id=p.Spouse2Id WHERE p.Id=@Id AND m.FamilyId=@FamilyId AND c.FamilyId=@FamilyId)
                THROW 51404,N'Không tìm thấy quan hệ.',1;
            DELETE genealogy.Marriages WHERE Id=@Id;
        END;
        INSERT reports.AuditLog(UserId,Action) VALUES(@ActorUserId,CONCAT('genealogy.',@Kind,'.',@Action,'; id=',@Id));
        COMMIT;
        SELECT @Id AS id;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        THROW;
    END CATCH;
END;
GO
