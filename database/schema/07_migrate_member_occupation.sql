-- Chuyển Occupation cũ sang WorkHistories trước khi bỏ cột.
USE [$(DB_NAME)];
GO
SET XACT_ABORT ON;
GO

-- Chạy phần tham chiếu Occupation động để schema mới không lỗi biên dịch.
IF COL_LENGTH(N'genealogy.Members', N'Occupation') IS NOT NULL
BEGIN
    EXEC sys.sp_executesql N'
        BEGIN TRANSACTION;

        INSERT INTO genealogy.WorkHistories
            (Id, MemberId, Company, Position, StartDate, EndDate, CreatedAt)
        SELECT
            NEWID(), [Id], N''Chưa cập nhật'', LTRIM(RTRIM([Occupation])),
            NULL, NULL, SYSUTCDATETIME()
        FROM genealogy.Members
        WHERE NULLIF(LTRIM(RTRIM([Occupation])), N'''') IS NOT NULL;

        ALTER TABLE genealogy.Members DROP COLUMN [Occupation];

        COMMIT TRANSACTION;
    ';
END;
GO