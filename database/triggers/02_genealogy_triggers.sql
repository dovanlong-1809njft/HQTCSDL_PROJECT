-- T-SQL Triggers - Thanh vien 2 (genealogy)
SET QUOTED_IDENTIFIER ON;
GO
USE [$(DB_NAME)];
GO

-- Chặn chu trình huyết thống và giới hạn tối đa 2 cha/mẹ cho mỗi người con.
CREATE OR ALTER TRIGGER [genealogy].[trg_ParentChild_PreventCycle]
ON [genealogy].[ParentChild]
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Với UPDATE, chỉ kiểm tra khi đổi ParentId hoặc ChildId
    IF NOT EXISTS (SELECT 1 FROM inserted)
        RETURN;
    IF EXISTS (SELECT 1 FROM deleted) AND NOT (UPDATE([ParentId]) OR UPDATE([ChildId]))
        RETURN;

    -- 1. Mỗi người con tối đa 2 cha/mẹ
    IF EXISTS
    (
        SELECT 1
        FROM [genealogy].[ParentChild] pc
        WHERE pc.[ChildId] IN (SELECT [ChildId] FROM inserted)
        GROUP BY pc.[ChildId]
        HAVING COUNT(*) > 2
    )
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50001, N'Một thành viên chỉ có tối đa 2 cha/mẹ.', 1;
    END;

    -- 2. Không cho tạo chu trình: con không được là tổ tiên của cha/mẹ.
    -- Từ mỗi người con vừa thêm, đi xuống các hậu duệ; nếu gặp lại cha/mẹ thì có chu trình.
    DECLARE @HasCycle BIT = 0;

    ;WITH Walk AS
    (
        SELECT i.[Id] AS EdgeId,
               i.[ParentId] AS TargetId,
               pc.[ChildId] AS CurrentId,
               1 AS Lvl
        FROM inserted i
        INNER JOIN [genealogy].[ParentChild] pc ON pc.[ParentId] = i.[ChildId]

        UNION ALL

        SELECT w.EdgeId,
               w.TargetId,
               pc.[ChildId],
               w.Lvl + 1
        FROM Walk w
        INNER JOIN [genealogy].[ParentChild] pc ON pc.[ParentId] = w.CurrentId
        WHERE w.CurrentId <> w.TargetId
          AND w.Lvl < 100
    )
    SELECT @HasCycle = 1
    FROM Walk
    WHERE CurrentId = TargetId
    OPTION (MAXRECURSION 200);

    IF @HasCycle = 1
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50002, N'Quan hệ cha/mẹ - con tạo ra chu trình huyết thống (con là tổ tiên của cha/mẹ).', 1;
    END;
END;
GO  
