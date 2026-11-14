-- =====================================================================
-- PERF 99: Don du lieu do hieu nang (dong ho N'__PERF_TEST__')
--
-- Xoa theo lo de khong phinh log. Chi dong cham toi dong ho perf, khong anh huong
-- du lieu seed that. Chay lai an toan (khong co du lieu perf thi chi in thong bao).
-- Chay: sqlcmd -S localhost -E -C -b -I -d FamilyConnect -v DB_NAME="FamilyConnect" -i database/perf/99_perf_cleanup.sql
-- =====================================================================
SET QUOTED_IDENTIFIER ON;
SET NOCOUNT ON;
GO
USE [$(DB_NAME)];
GO

DECLARE @FamilyId UNIQUEIDENTIFIER =
    (SELECT [Id] FROM [core].[Families] WHERE [Name] = N'__PERF_TEST__');

IF @FamilyId IS NULL
BEGIN
    PRINT N'Khong co du lieu perf de don.';
END
ELSE
BEGIN
    DECLARE @Batch INT = 50000;

    -- 1. MemberClosure (moi cap deu nam trong dong ho perf)
    WHILE 1 = 1
    BEGIN
        DELETE TOP (@Batch) c
        FROM [genealogy].[MemberClosure] c
        WHERE EXISTS (SELECT 1 FROM [genealogy].[Members] m
                      WHERE m.[Id] = c.[AncestorId] AND m.[FamilyId] = @FamilyId);
        IF @@ROWCOUNT = 0 BREAK;
    END;

    -- 2. ParentChild (trigger chi chay khi INSERT/UPDATE nen xoa khong ton them)
    WHILE 1 = 1
    BEGIN
        DELETE TOP (@Batch) pc
        FROM [genealogy].[ParentChild] pc
        WHERE EXISTS (SELECT 1 FROM [genealogy].[Members] m
                      WHERE m.[Id] = pc.[ParentId] AND m.[FamilyId] = @FamilyId);
        IF @@ROWCOUNT = 0 BREAK;
    END;

    -- 3. Members (Educations, WorkHistories xoa theo ON DELETE CASCADE)
    WHILE 1 = 1
    BEGIN
        DELETE TOP (@Batch) FROM [genealogy].[Members] WHERE [FamilyId] = @FamilyId;
        IF @@ROWCOUNT = 0 BREAK;
    END;

    -- 4. Chi nhanh va dong ho
    DELETE FROM [core].[Branches] WHERE [FamilyId] = @FamilyId;
    DELETE FROM [core].[Families] WHERE [Id] = @FamilyId;

    PRINT N'Da don xong du lieu perf.';
END;
GO