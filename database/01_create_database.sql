-- SQL Server / T-SQL: tạo cơ sở dữ liệu ban đầu (có thể chạy lại).
-- LƯU Ý: Script tạo DATABASE THẬT; chỉ chạy khi được người phụ trách CSDL đồng ý.
IF DB_ID(N'FamilyConnectDB') IS NULL
BEGIN
    EXEC(N'CREATE DATABASE FamilyConnectDB');
END;
GO
