-- Chuyển nghề nghiệp cũ sang lịch sử công tác trước khi bỏ cột.
USE [$(DB_NAME)];
GO
SET XACT_ABORT ON;
GO
IF COL_LENGTH(N'genealogy.Members', N'Occupation') IS NOT NULL
BEGIN
    BEGIN TRANSACTION;
    INSERT INTO genealogy.WorkHistories (Id,MemberId,Company,Position,StartDate,EndDate,CreatedAt)
    SELECT NEWID(),Id,N'Chưa cập nhật',LTRIM(RTRIM(Occupation)),NULL,NULL,SYSUTCDATETIME()
    FROM genealogy.Members WHERE NULLIF(LTRIM(RTRIM(Occupation)),N'') IS NOT NULL;
    ALTER TABLE genealogy.Members DROP COLUMN Occupation;
    COMMIT TRANSACTION;
END;
GO
