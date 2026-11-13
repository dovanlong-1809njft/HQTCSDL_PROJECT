/* =====================================================================
   database/triggers/03_community_triggers.sql
   TV3 - Trigger leo thang noi dung bi bao cao
   LUU Y: init.sh hien chua chay thu muc triggers/ (chi schema, views,
   procedures, seed). Can them run_scripts cho thu muc nay, hoac chay tay.
   ===================================================================== */
USE [$(DB_NAME)];
GO

/* Khi mot noi dung nhan du 3 bao cao dang cho xu ly (pending), ghi mot
   dong vao reports.AuditLog de quan tri vien biet can xem xet.
   Chi ghi dung luc vuot nguong, khong ghi lap lai o cac bao cao sau. */
CREATE OR ALTER TRIGGER [community].[trg_ReportedContents_Escalation]
ON [community].[ReportedContents]
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Threshold INT = 3;

    INSERT INTO [reports].[AuditLog] ([UserId], [Action])
    SELECT
        NULL,
        LEFT(CONCAT(N'ESCALATE: ', t.[TargetType], N' ',
                    CONVERT(NVARCHAR(36), t.[TargetId]), N' co ',
                    c.[Total], N' bao cao dang cho xu ly'), 300)
    FROM (SELECT DISTINCT [TargetId], [TargetType]
          FROM inserted
          WHERE [Status] = N'pending') AS t
    CROSS APPLY (SELECT
                    COUNT_BIG(*) AS [Total],
                    SUM(CASE WHEN new_report.[Id] IS NOT NULL
                             THEN 1 ELSE 0 END) AS [NewOnes]
                 FROM [community].[ReportedContents] AS r
                 LEFT JOIN inserted AS new_report ON new_report.[Id] = r.[Id]
                 WHERE r.[TargetId]   = t.[TargetId]
                   AND r.[TargetType] = t.[TargetType]
                   AND r.[Status]     = N'pending') AS c
    WHERE c.[Total] >= @Threshold
      AND c.[Total] - c.[NewOnes] < @Threshold;
END;
GO
