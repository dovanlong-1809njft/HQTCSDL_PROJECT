CREATE OR ALTER PROCEDURE community.usp_SetCommentReaction
    @CommentId UNIQUEIDENTIFIER, @ActorUserId UNIQUEIDENTIFIER, @Type NVARCHAR(20)=NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @FamilyId UNIQUEIDENTIFIER;
        SELECT @FamilyId=p.FamilyId FROM community.Comments c WITH(UPDLOCK,HOLDLOCK)
            JOIN community.Posts p ON p.Id=c.PostId WHERE c.Id=@CommentId;
        IF @FamilyId IS NULL THROW 51404, N'[TV4_SQL:51404] Bình luận không tồn tại.', 1;
        EXEC heritage.usp_AssertFamilyAccess @ActorUserId,@FamilyId;
        IF @Type IS NOT NULL AND @Type NOT IN ('Like','Love','Haha','Wow','Sad','Angry')
            THROW 51522, N'[TV4_SQL:51522] Loại cảm xúc không hợp lệ.', 1;
        IF @Type IS NULL
            DELETE community.CommentReactions WHERE CommentId=@CommentId AND UserId=@ActorUserId;
        ELSE
        BEGIN
            UPDATE community.CommentReactions WITH(UPDLOCK,HOLDLOCK)
                SET Type=@Type,UpdatedAt=SYSUTCDATETIME()
                WHERE CommentId=@CommentId AND UserId=@ActorUserId;
            IF @@ROWCOUNT=0
                INSERT community.CommentReactions(CommentId,UserId,Type) VALUES(@CommentId,@ActorUserId,@Type);
        END;
        COMMIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK;
        IF ERROR_NUMBER()=51403 THROW 51403, N'[TV4_SQL:51403] Không có quyền tương tác.', 1;
        THROW;
    END CATCH;
END;
GO
IF DATABASE_PRINCIPAL_ID(N'role_backend') IS NOT NULL
BEGIN
    GRANT SELECT ON OBJECT::community.CommentReactions TO role_backend;
    GRANT EXECUTE ON OBJECT::community.usp_SetCommentReaction TO role_backend;
END;
GO
