-- T-SQL: tạo database và các schema theo từng miền nghiệp vụ.
IF DB_ID(N'$(DB_NAME)') IS NULL
BEGIN
    CREATE DATABASE [$(DB_NAME)];
END;
GO

USE [$(DB_NAME)];
GO

IF SCHEMA_ID(N'core') IS NULL EXEC(N'CREATE SCHEMA [core]');
IF SCHEMA_ID(N'genealogy') IS NULL EXEC(N'CREATE SCHEMA [genealogy]');
IF SCHEMA_ID(N'community') IS NULL EXEC(N'CREATE SCHEMA [community]');
IF SCHEMA_ID(N'reports') IS NULL EXEC(N'CREATE SCHEMA [reports]');
IF SCHEMA_ID(N'heritage') IS NULL EXEC(N'CREATE SCHEMA [heritage]');
GO
