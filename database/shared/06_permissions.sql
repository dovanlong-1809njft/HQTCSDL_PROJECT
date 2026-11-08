USE FamilyConnect;
GO

SET NOCOUNT ON;

DECLARE @Accounts TABLE (
    UserName SYSNAME PRIMARY KEY,
    RoleName SYSNAME
);

INSERT INTO @Accounts (UserName, RoleName)
VALUES
    (N'dev_core',      N'role_dev_core'),
    (N'dev_genealogy', N'role_dev_genealogy'),
    (N'dev_community', N'role_dev_community'),
    (N'dev_heritage',  N'role_dev_heritage'),
    (N'dev_reports',   N'role_dev_reports'),
    (N'dev_seed',      N'role_seed'),
    (N'app_backend',   N'role_backend');

DECLARE @UserName SYSNAME;
DECLARE @RoleName SYSNAME;
DECLARE @Sql NVARCHAR(MAX);

WHILE EXISTS (SELECT 1 FROM @Accounts)
BEGIN
    SELECT TOP (1)
        @UserName = UserName,
        @RoleName = RoleName
    FROM @Accounts
    ORDER BY UserName;

    -- Tạo role nếu chưa có.
    IF DATABASE_PRINCIPAL_ID(@RoleName) IS NULL
    BEGIN
        SET @Sql = N'CREATE ROLE ' + QUOTENAME(@RoleName)
                 + N' AUTHORIZATION [dbo];';
        EXEC sys.sp_executesql @Sql;
    END;

    -- Tạo database user tương ứng với server login.
    IF DATABASE_PRINCIPAL_ID(@UserName) IS NULL
    BEGIN
        SET @Sql = N'CREATE USER ' + QUOTENAME(@UserName)
                 + N' FOR LOGIN ' + QUOTENAME(@UserName) + N';';
        EXEC sys.sp_executesql @Sql;
    END;

    -- Thêm user vào role nếu chưa là thành viên.
    IF IS_ROLEMEMBER(@RoleName, @UserName) = 0
    BEGIN
        SET @Sql = N'ALTER ROLE ' + QUOTENAME(@RoleName)
                 + N' ADD MEMBER ' + QUOTENAME(@UserName) + N';';
        EXEC sys.sp_executesql @Sql;
    END;

    PRINT N'Da gan: ' + @UserName + N' -> ' + @RoleName;

    DELETE FROM @Accounts WHERE UserName = @UserName;
END;

-- Kiểm tra kết quả.
SELECT
    member.name AS UserName,
    role.name AS RoleName
FROM sys.database_role_members AS membership
JOIN sys.database_principals AS role
    ON role.principal_id = membership.role_principal_id
JOIN sys.database_principals AS member
    ON member.principal_id = membership.member_principal_id
WHERE member.name IN (
    N'dev_core', N'dev_genealogy', N'dev_community',
    N'dev_heritage', N'dev_reports', N'dev_seed',
    N'app_backend'
)
ORDER BY member.name;
GO
--------------------------------------------------------------
USE FamilyConnect;
GO

SET NOCOUNT ON;

-- 1. Các role phát triển được quản lý đối tượng trong schema được giao.
DECLARE @DevScopes TABLE (
    RoleName SYSNAME,
    SchemaName SYSNAME
);

INSERT INTO @DevScopes
VALUES
    (N'role_dev_core',      N'core'),
    (N'role_dev_genealogy', N'genealogy'),
    (N'role_dev_community', N'community'),
    (N'role_dev_heritage',  N'heritage'),
    (N'role_dev_reports',   N'reports'),
    (N'role_dev_reports',   N'heritage'); -- Phần AI của TV5.

DECLARE @RoleName SYSNAME;
DECLARE @SchemaName SYSNAME;
DECLARE @Sql NVARCHAR(MAX);

WHILE EXISTS (SELECT 1 FROM @DevScopes)
BEGIN
    SELECT TOP (1)
        @RoleName = RoleName,
        @SchemaName = SchemaName
    FROM @DevScopes
    ORDER BY RoleName, SchemaName;

    SET @Sql =
        N'GRANT CREATE TABLE, CREATE VIEW, CREATE PROCEDURE, '
        + N'CREATE FUNCTION TO ' + QUOTENAME(@RoleName) + N';'
        + N'GRANT ALTER, SELECT, INSERT, UPDATE, DELETE, '
        + N'REFERENCES, EXECUTE, VIEW DEFINITION ON SCHEMA::'
        + QUOTENAME(@SchemaName)
        + N' TO ' + QUOTENAME(@RoleName) + N';';

    EXEC sys.sp_executesql @Sql;

    DELETE FROM @DevScopes
    WHERE RoleName = @RoleName AND SchemaName = @SchemaName;
END;

-- 2. Quyền tham chiếu cho khóa ngoại giữa các schema.
GRANT REFERENCES ON SCHEMA::genealogy TO role_dev_core;

GRANT REFERENCES ON SCHEMA::core TO role_dev_genealogy;

GRANT REFERENCES ON SCHEMA::core TO role_dev_community;
GRANT REFERENCES ON SCHEMA::genealogy TO role_dev_community;

GRANT REFERENCES ON SCHEMA::core TO role_dev_heritage;
GRANT REFERENCES ON SCHEMA::genealogy TO role_dev_heritage;

GRANT REFERENCES ON SCHEMA::core TO role_dev_reports;
GRANT REFERENCES ON SCHEMA::genealogy TO role_dev_reports;

-- 3. Backend đọc dữ liệu, gọi SP/function.
--    Seed được thao tác dữ liệu, không được sửa cấu trúc.
DECLARE @Schemas TABLE (SchemaName SYSNAME PRIMARY KEY);

INSERT INTO @Schemas
VALUES
    (N'core'), (N'genealogy'), (N'community'),
    (N'reports'), (N'heritage');

WHILE EXISTS (SELECT 1 FROM @Schemas)
BEGIN
    SELECT TOP (1) @SchemaName = SchemaName FROM @Schemas;

    SET @Sql =
        N'GRANT SELECT, EXECUTE ON SCHEMA::'
        + QUOTENAME(@SchemaName) + N' TO [role_backend];'
        + N'GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::'
        + QUOTENAME(@SchemaName) + N' TO [role_seed];';

    EXEC sys.sp_executesql @Sql;

    DELETE FROM @Schemas WHERE SchemaName = @SchemaName;
END;

-- API đăng ký hiện thêm tài khoản trực tiếp bằng SQLAlchemy.
GRANT INSERT ON OBJECT::core.Users TO role_backend;

-- 4. Cho phép đọc/thêm audit, chặn sửa/xóa trực tiếp.
DECLARE @AuditRoles TABLE (RoleName SYSNAME PRIMARY KEY);

INSERT INTO @AuditRoles
VALUES
    (N'role_dev_core'),
    (N'role_dev_genealogy'),
    (N'role_dev_community'),
    (N'role_dev_heritage'),
    (N'role_dev_reports'),
    (N'role_seed'),
    (N'role_backend');

WHILE EXISTS (SELECT 1 FROM @AuditRoles)
BEGIN
    SELECT TOP (1) @RoleName = RoleName FROM @AuditRoles;

    SET @Sql =
        N'GRANT SELECT, INSERT ON OBJECT::reports.AuditLog TO '
        + QUOTENAME(@RoleName) + N';'
        + N'DENY UPDATE, DELETE ON OBJECT::reports.AuditLog TO '
        + QUOTENAME(@RoleName) + N';';

    EXEC sys.sp_executesql @Sql;

    DELETE FROM @AuditRoles WHERE RoleName = @RoleName;
END;

PRINT N'Da cap quyen cho cac role.';
GO
