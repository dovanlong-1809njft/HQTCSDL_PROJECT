-- T-SQL task 9: run after task6.integration.sql, only in the disposable test database.
USE [$(DB_NAME)];
GO
IF DB_NAME() NOT LIKE N'FamilyConnect[_]Task6Test[_]%'
BEGIN
    SET NOEXEC ON;
    THROW 51990, N'Chi duoc chay fixtures task 9 tren database thu rieng.', 1;
END;
GO

-- Match role_backend for real authentication, statistics and moderation reads.
GRANT INSERT ON OBJECT::core.Users TO [task6_backend];
GRANT SELECT, EXECUTE ON SCHEMA::community TO [task6_backend];
GRANT SELECT, EXECUTE ON SCHEMA::reports TO [task6_backend];
GRANT SELECT, EXECUTE ON SCHEMA::heritage TO [task6_backend];

-- EmailStr rejects the reserved .invalid domain used by the JWT-only task 6 fixtures.
UPDATE core.Users SET Email = REPLACE(Email, N'@test.invalid', N'@example.com');
INSERT core.SystemConfigs (ConfigKey, ConfigValue, Description)
VALUES ('task9.admin_only', N'TASK9 private configuration', N'Login E2E fixture');
GO
