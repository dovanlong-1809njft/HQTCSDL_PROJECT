-- T-SQL Triggers - Thanh vien 4 (heritage & family tree)
USE [$(DB_NAME)];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO
CREATE OR ALTER TRIGGER heritage.trg_Honors_ValidateAndAudit
ON heritage.Honors
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM inserted) AND NOT EXISTS (SELECT 1 FROM deleted) RETURN;
    IF EXISTS (SELECT 1 FROM inserted WHERE NULLIF(LTRIM(RTRIM(Title)), N'') IS NULL)
        THROW 51422, N'Honor title must not be blank.', 1;

    DECLARE @Value SQL_VARIANT = SESSION_CONTEXT(N'actor_user_id');
    DECLARE @Actor UNIQUEIDENTIFIER = TRY_CONVERT(UNIQUEIDENTIFIER, @Value);
    -- Direct SQL/seed/cascade operations have a NULL actor and retain SQL login.
    -- Authenticated procedures set and restore this value; never use a request body actor.
    IF @Value IS NOT NULL
    BEGIN
        IF @Actor IS NULL OR NOT EXISTS
            (SELECT 1 FROM core.Users WHERE UserId = @Actor AND IsActive = 1 AND Role IN (N'admin', N'family_head'))
            THROW 51403, N'Invalid honor audit actor.', 1;
        IF NOT EXISTS (SELECT 1 FROM core.Users WHERE UserId = @Actor AND Role = N'admin')
           AND EXISTS (
               SELECT 1 FROM (
                   SELECT MemberId FROM inserted UNION SELECT MemberId FROM deleted
               ) changed
               LEFT JOIN genealogy.Members target ON target.Id = changed.MemberId
               WHERE target.Id IS NULL OR NOT EXISTS (
                   SELECT 1 FROM genealogy.Members actor
                   WHERE actor.UserId = @Actor AND actor.FamilyId = target.FamilyId))
            THROW 51403, N'Honor is outside actor family.', 1;
    END;

    -- Exactly one entry per changed honor, including multi-row DML. SPs do not duplicate it.
    INSERT INTO reports.AuditLog (UserId, Action)
    SELECT @Actor, CONCAT(N'heritage.honor.',
        CASE WHEN d.Id IS NULL THEN N'created' WHEN i.Id IS NULL THEN N'deleted' ELSE N'updated' END,
        N'; id=', CONVERT(NVARCHAR(36), COALESCE(i.Id, d.Id)),
        N'; member=', CONVERT(NVARCHAR(36), COALESCE(i.MemberId, d.MemberId)),
        N'; sql_login=', LEFT(ORIGINAL_LOGIN(), 64))
    FROM inserted i FULL OUTER JOIN deleted d ON d.Id = i.Id;
END;
GO
