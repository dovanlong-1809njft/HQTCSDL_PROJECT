-- TV1: audit thay doi quyen/trang thai tai khoan va thoi diem sua cau hinh.
USE [$(DB_NAME)];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

CREATE OR ALTER TRIGGER [core].[trg_Users_AuditRoleAndStatus]
ON [core].[Users]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT (UPDATE([Role]) OR UPDATE([IsActive]))
        RETURN;

    -- API quan tri co the dat SESSION_CONTEXT('actor_user_id') tu JWT da xac thuc.
    -- Neu thao tac SQL truc tiep khong co actor, UserId cua audit la NULL;
    -- Action van luu target va SQL login. Khong gan nham target thanh actor.
    DECLARE @ActorValue SQL_VARIANT = SESSION_CONTEXT(N'actor_user_id');
    DECLARE @ActorUserId UNIQUEIDENTIFIER = TRY_CONVERT(UNIQUEIDENTIFIER, @ActorValue);

    IF @ActorValue IS NOT NULL AND
       (@ActorUserId IS NULL OR NOT EXISTS
        (SELECT 1 FROM [core].[Users] WHERE [UserId] = @ActorUserId))
        THROW 51021, N'actor_user_id trong SESSION_CONTEXT khong hop le.', 1;

    -- INSERT ... SELECT xu ly dung ca UPDATE nhieu tai khoan trong mot lenh.
    INSERT INTO [reports].[AuditLog] ([UserId], [Action])
    SELECT
        @ActorUserId,
        CONVERT(NVARCHAR(300), CONCAT(
            N'users.role_status_changed; target=', CONVERT(NVARCHAR(36), current_user_row.[UserId]),
            N'; role=', previous_user_row.[Role], N'->', current_user_row.[Role],
            N'; active=', CONVERT(NVARCHAR(1), previous_user_row.[IsActive]),
            N'->', CONVERT(NVARCHAR(1), current_user_row.[IsActive]),
            N'; sql_login=', LEFT(ORIGINAL_LOGIN(), 64)))
    FROM inserted AS current_user_row
    INNER JOIN deleted AS previous_user_row
        ON previous_user_row.[UserId] = current_user_row.[UserId]
    WHERE current_user_row.[Role] <> previous_user_row.[Role]
       OR current_user_row.[IsActive] <> previous_user_row.[IsActive];
END;
GO

CREATE OR ALTER TRIGGER [core].[trg_SystemConfigs_UpdatedAt]
ON [core].[SystemConfigs]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Hoat dong ca khi RECURSIVE_TRIGGERS bat; bo qua lan tu goi de cap nhat timestamp.
    IF TRIGGER_NESTLEVEL(OBJECT_ID(N'core.trg_SystemConfigs_UpdatedAt')) > 1
        RETURN;

    DECLARE @UpdatedAt DATETIME2(0) = SYSUTCDATETIME();

    UPDATE config
    SET config.[UpdatedAt] = @UpdatedAt
    FROM [core].[SystemConfigs] AS config
    INNER JOIN inserted AS changed
        ON changed.[ConfigKey] = config.[ConfigKey];
END;
GO
