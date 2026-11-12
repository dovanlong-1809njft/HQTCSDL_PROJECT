-- TV1: danh sach yeu cau xac minh dang cho xu ly.
USE [$(DB_NAME)];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

CREATE OR ALTER VIEW [core].[vw_PendingVerifications]
AS
    SELECT
        verification.[Id] AS [VerificationId],
        verification.[UserId],
        applicant.[FullName] AS [UserFullName],
        applicant.[Email] AS [UserEmail],
        applicant.[IsActive] AS [UserIsActive],
        verification.[MemberId],
        member.[FullName] AS [MemberFullName],
        member.[BirthDate],
        member.[FamilyId],
        family.[Name] AS [FamilyName],
        member.[BranchId],
        branch.[Name] AS [BranchName],
        member.[UserId] AS [LinkedUserId],
        verification.[Status],
        verification.[CreatedAt] AS [RequestedAt]
    FROM [core].[MemberVerifications] AS verification
    INNER JOIN [core].[Users] AS applicant
        ON applicant.[UserId] = verification.[UserId]
    INNER JOIN [genealogy].[Members] AS member
        ON member.[Id] = verification.[MemberId]
    INNER JOIN [core].[Families] AS family
        ON family.[Id] = member.[FamilyId]
    LEFT JOIN [core].[Branches] AS branch
        ON branch.[Id] = member.[BranchId]
    WHERE verification.[Status] = N'pending';
GO
