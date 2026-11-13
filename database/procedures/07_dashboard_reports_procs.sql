-- T-SQL task 8: thong ke theo gia dinh; admin xem tat ca, family_head xem gia dinh da lien ket.
USE [$(DB_NAME)];
GO

CREATE OR ALTER PROCEDURE [reports].[usp_GetDashboardStatistics]
    @ActorUserId UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @ActorRole NVARCHAR(20);
    SELECT @ActorRole = [Role] FROM [core].[Users]
    WHERE [UserId] = @ActorUserId AND [IsActive] = 1;
    IF @ActorRole IS NULL OR @ActorRole NOT IN (N'admin', N'family_head')
        THROW 51201, N'Tai khoan khong co quyen xem thong ke.', 1;

    SELECT summary.[FamilyId], summary.[FamilyName], summary.[MemberCount],
           summary.[PostCount], summary.[EventCount]
    FROM [reports].[vw_FamilyActivitySummary] AS summary
    WHERE @ActorRole = N'admin' OR EXISTS
        (SELECT 1 FROM [genealogy].[Members] AS member
         WHERE member.[UserId] = @ActorUserId AND member.[FamilyId] = summary.[FamilyId])
    ORDER BY summary.[FamilyName], summary.[FamilyId];
END;
GO
