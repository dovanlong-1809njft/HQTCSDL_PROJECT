/* MANUAL ONLY. Run on an explicitly provisioned disposable database, never group DB.
   Apply TV4 view -> procedure -> trigger first. No schema/seed/init is run here.
   SQLCMD Mode: set DB_NAME to FamilyConnect_TV4_Test_<suffix>.
   Opt in in the SAME connection: EXEC sys.sp_set_session_context N'allow_tv4_tests', 1;
   Every scenario rolls back generated rows. Throws stop sqlcmd -b on failure.
*/
USE [$(DB_NAME)];
GO
IF DB_NAME() NOT LIKE N'FamilyConnect[_]TV4[_]Test[_]%'
   OR COALESCE(TRY_CONVERT(INT, SESSION_CONTEXT(N'allow_tv4_tests')), 0) <> 1
    THROW 51499, N'TV4 tests require an explicitly opted-in disposable test DB.', 1;
GO
SET NOCOUNT ON;
GO
CREATE OR ALTER PROCEDURE #TV4Fixture
    @Family UNIQUEIDENTIFIER, @Other UNIQUEIDENTIFIER, @Head UNIQUEIDENTIFIER,
    @User UNIQUEIDENTIFIER, @Member UNIQUEIDENTIFIER, @Second UNIQUEIDENTIFIER
AS
BEGIN
    -- Recheck inside the fixture: SSMS may continue after a failed earlier GO batch.
    IF DB_NAME() NOT LIKE N'FamilyConnect[_]TV4[_]Test[_]%'
       OR COALESCE(TRY_CONVERT(INT, SESSION_CONTEXT(N'allow_tv4_tests')),0)<>1
        THROW 51499,N'TV4 fixture requires an opted-in disposable test DB.',1;
    INSERT core.Families (Id, Name) VALUES (@Family,N'TV4 synthetic A'),(@Other,N'TV4 synthetic B');
    INSERT core.Users (UserId,Email,PasswordHash,FullName,Role)
    VALUES (@Head,CONCAT(CONVERT(NVARCHAR(36),@Head),N'@example.invalid'),N'not-a-real-hash',N'TV4 Head',N'family_head'),
           (@User,CONCAT(CONVERT(NVARCHAR(36),@User),N'@example.invalid'),N'not-a-real-hash',N'TV4 Member',N'member');
    INSERT genealogy.Members (Id,FamilyId,UserId,FullName)
    VALUES (@Member,@Family,@Head,N'TV4 A'),(@Second,@Family,@User,N'TV4 B');
END;
GO
-- Positive CRUD, audit count, ties/zero honors, tree JSON, context restoration.
DECLARE @Family UNIQUEIDENTIFIER=NEWID(), @Other UNIQUEIDENTIFIER=NEWID(), @Head UNIQUEIDENTIFIER=NEWID(),
        @User UNIQUEIDENTIFIER=NEWID(), @Member UNIQUEIDENTIFIER=NEWID(), @Second UNIQUEIDENTIFIER=NEWID();
BEGIN TRY
    BEGIN TRANSACTION;
    EXEC #TV4Fixture @Family,@Other,@Head,@User,@Member,@Second;
    CREATE TABLE #Item (Id UNIQUEIDENTIFIER,FamilyId UNIQUEIDENTIFIER,CreatedByUserId UNIQUEIDENTIFIER,
        Type NVARCHAR(20),Title NVARCHAR(200),Description NVARCHAR(500),Content NVARCHAR(MAX),MediaUrl NVARCHAR(500),
        CreatedAt DATETIME2(3),VersionToken VARCHAR(64));
    INSERT #Item EXEC heritage.usp_CreateHeritageItem @User,@Family,N'story',N'A',NULL,N'B',NULL;
    DECLARE @ItemId UNIQUEIDENTIFIER=(SELECT Id FROM #Item), @Version VARCHAR(64)=(SELECT VersionToken FROM #Item);
    EXEC heritage.usp_UpdateHeritageItem @User,@Family,@ItemId,@Version,N'story',N'Updated',NULL,N'B',NULL;
    SELECT @Version=VersionToken FROM heritage.vw_HeritageItems WHERE Id=@ItemId;
    EXEC heritage.usp_DeleteHeritageItem @User,@Family,@ItemId,@Version;
    IF EXISTS (SELECT 1 FROM heritage.Items WHERE Id=@ItemId) THROW 51498,N'Item delete failed.',1;

    CREATE TABLE #Honor (Id UNIQUEIDENTIFIER,MemberId UNIQUEIDENTIFIER,Title NVARCHAR(200),Description NVARCHAR(1000),
        DateAwarded DATE,CreatedAt DATETIME2(0),FamilyId UNIQUEIDENTIFIER,FullName NVARCHAR(200),VersionToken VARCHAR(64));
    INSERT #Honor EXEC heritage.usp_GrantMemberHonor @Head,@Family,@Member,N'Award',NULL,NULL;
    DECLARE @HonorId UNIQUEIDENTIFIER=(SELECT Id FROM #Honor);
    SELECT @Version=VersionToken FROM #Honor;
    EXEC heritage.usp_UpdateMemberHonor @Head,@Family,@HonorId,@Version,N'Updated',NULL,NULL;
    SELECT @Version=VersionToken FROM heritage.vw_Honors WHERE Id=@HonorId;
    EXEC heritage.usp_DeleteMemberHonor @Head,@Family,@HonorId,@Version;
    IF (SELECT COUNT(*) FROM reports.AuditLog WHERE UserId=@Head AND Action LIKE N'heritage.honor.%')<>3
        THROW 51498,N'Honor audit must occur once per mutation.',1;
    IF SESSION_CONTEXT(N'actor_user_id') IS NOT NULL THROW 51498,N'Actor context leaked.',1;

    EXEC sys.sp_set_session_context @key=N'actor_user_id',@value=@Head;
    INSERT heritage.Honors (MemberId,Title) VALUES (@Member,N'One'),(@Second,N'Two');
    UPDATE heritage.Honors SET Title=N'Both' WHERE MemberId IN (@Member,@Second);
    IF (SELECT COUNT(*) FROM reports.AuditLog WHERE UserId=@Head AND Action LIKE N'heritage.honor.%')<>7
        THROW 51498,N'Multi-row audit failed.',1;
    IF (SELECT COUNT(*) FROM heritage.vw_MemberHonorsRanking WHERE FamilyId=@Family AND Rank=1 AND HonorCount=1)<>2
        THROW 51498,N'Dense ranking ties failed.',1;
    DELETE heritage.Honors WHERE MemberId IN (@Member,@Second);
    IF (SELECT COUNT(*) FROM heritage.vw_MemberHonorsRanking WHERE FamilyId=@Family AND HonorCount=0)<>2
        THROW 51498,N'Zero-honor members missing.',1;
    EXEC sys.sp_set_session_context @key=N'actor_user_id',@value=NULL;

    DECLARE @Spouse UNIQUEIDENTIFIER=NEWID();
    INSERT genealogy.Members (Id,FamilyId,FullName) VALUES (@Spouse,@Family,N'TV4 Spouse');
    INSERT genealogy.ParentChild (ParentId,ChildId) VALUES (@Member,@Second);
    INSERT genealogy.Marriages (Spouse1Id,Spouse2Id)
    SELECT CASE WHEN CONVERT(CHAR(36),@Second)<CONVERT(CHAR(36),@Spouse) THEN @Second ELSE @Spouse END,
           CASE WHEN CONVERT(CHAR(36),@Second)<CONVERT(CHAR(36),@Spouse) THEN @Spouse ELSE @Second END;
    CREATE TABLE #Tree (TreeJson NVARCHAR(MAX));
    INSERT #Tree EXEC heritage.usp_GetFamilyTreeJson @User,@Family;
    IF (SELECT ISJSON(TreeJson) FROM #Tree)<>1 THROW 51498,N'Tree is not JSON.',1;
    IF (SELECT COUNT(*) FROM #Tree CROSS APPLY OPENJSON(TreeJson,'$.nodes'))<>3 THROW 51498,N'Tree node scope failed.',1;
    IF (SELECT COUNT(*) FROM #Tree CROSS APPLY OPENJSON(TreeJson,'$.edges'))<>2 THROW 51498,N'Missing parent/marriage edges.',1;
    ROLLBACK TRANSACTION;
    PRINT N'PASS positive CRUD, ranking, multi-row trigger, JSON, context, rollback';
END TRY
BEGIN CATCH
    IF XACT_STATE()<>0 ROLLBACK TRANSACTION;
    EXEC sys.sp_set_session_context @key=N'actor_user_id',@value=NULL;
    THROW;
END CATCH;
GO
-- Negative cases each use a new transaction: XACT_ABORT may doom a transaction.
DECLARE @Case INT=1;
WHILE @Case<=7
BEGIN
    DECLARE @Family UNIQUEIDENTIFIER=NEWID(), @Other UNIQUEIDENTIFIER=NEWID(), @Head UNIQUEIDENTIFIER=NEWID(),
            @User UNIQUEIDENTIFIER=NEWID(), @Member UNIQUEIDENTIFIER=NEWID(), @Second UNIQUEIDENTIFIER=NEWID(),
            @Id UNIQUEIDENTIFIER=NEWID(), @Expected INT;
    BEGIN TRY
        BEGIN TRANSACTION;
        EXEC #TV4Fixture @Family,@Other,@Head,@User,@Member,@Second;
        IF @Case=1 BEGIN SET @Expected=51403; EXEC heritage.usp_CreateHeritageItem @User,@Other,N'story',N'A',NULL,N'B',NULL; END;
        IF @Case=2 BEGIN SET @Expected=51422; EXEC heritage.usp_CreateHeritageItem @User,@Family,N'photo',N'A',NULL,NULL,NULL; END;
        IF @Case=3 BEGIN SET @Expected=51403; EXEC heritage.usp_GrantMemberHonor @User,@Family,@Member,N'A'; END;
        IF @Case=4 BEGIN SET @Expected=51404; EXEC heritage.usp_GrantMemberHonor @Head,@Family,@Id,N'A'; END;
        IF @Case IN (5,6,7)
        BEGIN
            INSERT heritage.Items (Id,FamilyId,CreatedByUserId,Type,Title,Content) VALUES (@Id,@Family,@User,N'story',N'A',N'B');
            IF @Case=5 BEGIN SET @Expected=51409; EXEC heritage.usp_DeleteHeritageItem @User,@Family,@Id,'bad-version'; END;
            IF @Case=6
            BEGIN
                -- Member cannot change another author's row, even within the family.
                UPDATE heritage.Items SET CreatedByUserId=@Head WHERE Id=@Id;
                SET @Expected=51403;
                EXEC heritage.usp_UpdateHeritageItem @User,@Family,@Id,'bad-version',N'story',N'A',NULL,N'B',NULL;
            END;
            IF @Case=7
            BEGIN
                -- Failed multi-row insert must roll back all rows and audit entries.
                SET @Expected=51422;
                INSERT heritage.Honors (MemberId,Title) VALUES (@Member,N'Valid'),(@Second,N' ');
            END;
        END;
        THROW 51498,N'Expected rejection did not occur.',1;
    END TRY
    BEGIN CATCH
        DECLARE @Actual INT=ERROR_NUMBER();
        IF XACT_STATE()<>0 ROLLBACK TRANSACTION;
        IF @Expected IS NULL OR @Actual<>@Expected THROW;
        IF EXISTS (SELECT 1 FROM core.Families WHERE Id=@Family) THROW 51498,N'Rollback leaked test data.',1;
        PRINT CONCAT(N'PASS negative case ',@Case,N' (',@Actual,N')');
    END CATCH;
    SET @Case+=1;
END;
GO
