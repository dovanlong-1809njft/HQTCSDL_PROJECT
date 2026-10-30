/* =====================================================================
   database/seed/01_seed.sql
   Người 4 — Dữ liệu mẫu cho toàn bộ 14 bảng
   =====================================================================
   Chạy SAU CÙNG, khi cả 6 file trong database/schema/ đã hoàn tất.

   Nguyên tắc theo database/seed/README.md:
     - Không có thông tin cá nhân thật. Email dùng miền example.invalid
       là miền dành riêng cho ví dụ, không gửi thư tới đâu được.
     - Không có mật khẩu dạng rõ. Cột PasswordHash điền chuỗi đánh dấu
       rõ ràng là giả, không phải hash dùng được để đăng nhập.

   Script chạy lại được nhiều lần: xóa đúng các bản ghi mẫu theo GUID cố
   định rồi chèn lại, không đụng tới dữ liệu do người khác tạo.

   Quy ước GUID để dễ đọc khi tra cứu:
     11111111  Users              22222222  Families
     33333333  Branches           44444444  Members
     55555555  ParentChild        66666666  Marriages
     77777777  Posts              88888888  Comments
     99999999  Reactions          AAAAAAAA  Events
     BBBBBBBB  EventParticipants  CCCCCCCC  AuditLog
     DDDDDDDD  MemberVerifications EEEEEEEE Heritage Items

   Nếu chạy trong SSMS: bật SQLCMD Mode và thêm
   :setvar DB_NAME "FamilyConnect"  ở đầu file.
   ===================================================================== */

USE [$(DB_NAME)];
GO

SET XACT_ABORT ON;
SET NOCOUNT ON;
GO

/* ---------------------------------------------------------------------
   1. Kiểm tra đủ 14 bảng trước khi chèn
   --------------------------------------------------------------------- */

DECLARE @missing NVARCHAR(MAX) = N'';

IF OBJECT_ID(N'core.Users',                N'U') IS NULL SET @missing += N'core.Users, ';
IF OBJECT_ID(N'core.Families',             N'U') IS NULL SET @missing += N'core.Families, ';
IF OBJECT_ID(N'core.Branches',             N'U') IS NULL SET @missing += N'core.Branches, ';
IF OBJECT_ID(N'core.MemberVerifications',  N'U') IS NULL SET @missing += N'core.MemberVerifications, ';
IF OBJECT_ID(N'genealogy.Members',         N'U') IS NULL SET @missing += N'genealogy.Members, ';
IF OBJECT_ID(N'genealogy.ParentChild',     N'U') IS NULL SET @missing += N'genealogy.ParentChild, ';
IF OBJECT_ID(N'genealogy.Marriages',       N'U') IS NULL SET @missing += N'genealogy.Marriages, ';
IF OBJECT_ID(N'community.Posts',           N'U') IS NULL SET @missing += N'community.Posts, ';
IF OBJECT_ID(N'community.Comments',        N'U') IS NULL SET @missing += N'community.Comments, ';
IF OBJECT_ID(N'community.Reactions',       N'U') IS NULL SET @missing += N'community.Reactions, ';
IF OBJECT_ID(N'community.Events',          N'U') IS NULL SET @missing += N'community.Events, ';
IF OBJECT_ID(N'community.EventParticipants', N'U') IS NULL SET @missing += N'community.EventParticipants, ';
IF OBJECT_ID(N'reports.AuditLog',          N'U') IS NULL SET @missing += N'reports.AuditLog, ';
IF OBJECT_ID(N'heritage.Items',            N'U') IS NULL SET @missing += N'heritage.Items, ';

IF LEN(@missing) > 0
BEGIN
    DECLARE @msg NVARCHAR(2000) =
        N'Chua chay duoc seed. Cac bang sau chua ton tai: '
        + LEFT(@missing, LEN(@missing) - 1)
        + N'. Chay het database/schema/ theo thu tu truoc.';
    THROW 50610, @msg, 1;
END
GO


/* ---------------------------------------------------------------------
   2. Khai báo GUID cố định
   --------------------------------------------------------------------- */

DECLARE
    /* Tài khoản */
    @uTruong    UNIQUEIDENTIFIER = '11111111-1111-1111-1111-000000000001',
    @uMai       UNIQUEIDENTIFIER = '11111111-1111-1111-1111-000000000002',
    @uHung      UNIQUEIDENTIFIER = '11111111-1111-1111-1111-000000000003',
    @uLan       UNIQUEIDENTIFIER = '11111111-1111-1111-1111-000000000004',

    /* Gia đình và nhánh */
    @fam        UNIQUEIDENTIFIER = '22222222-2222-2222-2222-000000000001',
    @brTruong   UNIQUEIDENTIFIER = '33333333-3333-3333-3333-000000000001',
    @brThu      UNIQUEIDENTIFIER = '33333333-3333-3333-3333-000000000002',

    /* Thành viên gia phả */
    @mOng       UNIQUEIDENTIFIER = '44444444-4444-4444-4444-000000000001',
    @mBa        UNIQUEIDENTIFIER = '44444444-4444-4444-4444-000000000002',
    @mTruong    UNIQUEIDENTIFIER = '44444444-4444-4444-4444-000000000003',
    @mMai       UNIQUEIDENTIFIER = '44444444-4444-4444-4444-000000000004',
    @mHung      UNIQUEIDENTIFIER = '44444444-4444-4444-4444-000000000005',
    @mLan       UNIQUEIDENTIFIER = '44444444-4444-4444-4444-000000000006',

    /* Thời điểm gốc cho dữ liệu mẫu */
    @t0         DATETIME2(3)     = CAST('2026-01-05T08:00:00' AS DATETIME2(3));

BEGIN TRY
    BEGIN TRANSACTION;

    /* -----------------------------------------------------------------
       3. Dọn dữ liệu mẫu cũ, theo thứ tự con trước cha
       ----------------------------------------------------------------- */

    DELETE FROM heritage.Items            WHERE CAST(Id AS CHAR(36)) LIKE 'EEEEEEEE-%';
    DELETE FROM reports.AuditLog          WHERE CAST(Id AS CHAR(36)) LIKE 'CCCCCCCC-%';
    DELETE FROM community.EventParticipants WHERE CAST(Id AS CHAR(36)) LIKE 'BBBBBBBB-%';
    DELETE FROM community.Events          WHERE CAST(Id AS CHAR(36)) LIKE 'AAAAAAAA-%';
    DELETE FROM community.Reactions       WHERE CAST(Id AS CHAR(36)) LIKE '99999999-%';
    DELETE FROM community.Comments        WHERE CAST(Id AS CHAR(36)) LIKE '88888888-%';
    DELETE FROM community.Posts           WHERE CAST(Id AS CHAR(36)) LIKE '77777777-%';
    DELETE FROM genealogy.Marriages       WHERE CAST(Id AS CHAR(36)) LIKE '66666666-%';
    DELETE FROM genealogy.ParentChild     WHERE CAST(Id AS CHAR(36)) LIKE '55555555-%';
    DELETE FROM core.MemberVerifications  WHERE CAST(Id AS CHAR(36)) LIKE 'DDDDDDDD-%';
    DELETE FROM genealogy.Members         WHERE CAST(Id AS CHAR(36)) LIKE '44444444-%';
    DELETE FROM core.Branches             WHERE CAST(Id AS CHAR(36)) LIKE '33333333-%';
    DELETE FROM core.Families             WHERE CAST(Id AS CHAR(36)) LIKE '22222222-%';
    DELETE FROM core.Users                WHERE CAST(UserId AS CHAR(36)) LIKE '11111111-%';

    /* -----------------------------------------------------------------
       4. core.Users
       PasswordHash là chuỗi đánh dấu, không đăng nhập được.
       ----------------------------------------------------------------- */

    INSERT INTO core.Users (UserId, Email, PasswordHash, FullName, Role, IsActive, CreatedAt)
    VALUES
        (@uTruong, N'truong@example.invalid', N'SEED-ONLY-KHONG-PHAI-HASH-THAT', N'Nguyễn Văn Trường', N'admin',  1, @t0),
        (@uMai,    N'mai@example.invalid',    N'SEED-ONLY-KHONG-PHAI-HASH-THAT', N'Trần Thị Mai',      N'member', 1, DATEADD(DAY, 1, @t0)),
        (@uHung,   N'hung@example.invalid',   N'SEED-ONLY-KHONG-PHAI-HASH-THAT', N'Nguyễn Văn Hùng',   N'member', 1, DATEADD(DAY, 2, @t0)),
        (@uLan,    N'lan@example.invalid',    N'SEED-ONLY-KHONG-PHAI-HASH-THAT', N'Nguyễn Thị Lan',    N'member', 0, DATEADD(DAY, 3, @t0));

    /* -----------------------------------------------------------------
       5. core.Families và core.Branches
       ----------------------------------------------------------------- */

    INSERT INTO core.Families (Id, Name, CreatedAt)
    VALUES (@fam, N'Họ Nguyễn Văn — Thạch Thất', @t0);

    INSERT INTO core.Branches (Id, FamilyId, Name, CreatedAt)
    VALUES
        (@brTruong, @fam, N'Chi trưởng', @t0),
        (@brThu,    @fam, N'Chi thứ',    @t0);

    /* -----------------------------------------------------------------
       6. genealogy.Members
       Ba thế hệ. UserId để NULL với người chưa có tài khoản.
       ----------------------------------------------------------------- */

    INSERT INTO genealogy.Members
        (Id, FamilyId, BranchId, UserId, FullName, BirthDate, Occupation, Location, CreatedAt)
    VALUES
        (@mOng,    @fam, @brTruong, NULL,     N'Nguyễn Văn Cẩn',  '1938-03-12', N'Thợ mộc',       N'Hà Nội',           @t0),
        (@mBa,     @fam, @brTruong, NULL,     N'Lê Thị Tâm',      '1942-07-30', N'Nội trợ',       N'Hà Nội',           @t0),
        (@mTruong, @fam, @brTruong, @uTruong, N'Nguyễn Văn Trường','1968-11-02', N'Giáo viên',     N'Hà Nội',           @t0),
        (@mMai,    @fam, @brTruong, @uMai,    N'Trần Thị Mai',    '1971-05-18', N'Kế toán',       N'Hà Nội',           @t0),
        (@mHung,   @fam, @brThu,    @uHung,   N'Nguyễn Văn Hùng', '1995-09-24', N'Kỹ sư phần mềm', N'TP. Hồ Chí Minh', @t0),
        (@mLan,    @fam, @brThu,    @uLan,    N'Nguyễn Thị Lan',  '1999-02-14', N'Sinh viên',     N'Đà Nẵng',          @t0);

    /* -----------------------------------------------------------------
       7. core.MemberVerifications
       Một yêu cầu đã duyệt, một đang chờ.
       ----------------------------------------------------------------- */

    INSERT INTO core.MemberVerifications (Id, UserId, MemberId, Status, CreatedAt)
    VALUES
        ('DDDDDDDD-DDDD-DDDD-DDDD-000000000001', @uHung, @mHung, N'approved', DATEADD(DAY, 4, @t0)),
        ('DDDDDDDD-DDDD-DDDD-DDDD-000000000002', @uLan,  @mLan,  N'pending',  DATEADD(DAY, 5, @t0));

    /* -----------------------------------------------------------------
       8. genealogy.ParentChild
       ----------------------------------------------------------------- */

    INSERT INTO genealogy.ParentChild (Id, ParentId, ChildId, CreatedAt)
    VALUES
        ('55555555-5555-5555-5555-000000000001', @mOng,    @mTruong, @t0),
        ('55555555-5555-5555-5555-000000000002', @mBa,     @mTruong, @t0),
        ('55555555-5555-5555-5555-000000000003', @mTruong, @mHung,   @t0),
        ('55555555-5555-5555-5555-000000000004', @mMai,    @mHung,   @t0),
        ('55555555-5555-5555-5555-000000000005', @mTruong, @mLan,    @t0),
        ('55555555-5555-5555-5555-000000000006', @mMai,    @mLan,    @t0);

    /* -----------------------------------------------------------------
       9. genealogy.Marriages
       ERD quy định Spouse1Id < Spouse2Id nên sắp xếp ngay khi chèn,
       không phụ thuộc vào thứ tự viết tay.
       ----------------------------------------------------------------- */

    INSERT INTO genealogy.Marriages (Id, Spouse1Id, Spouse2Id, MarriedDate, CreatedAt)
    VALUES
        ('66666666-6666-6666-6666-000000000001',
         CASE WHEN @mOng < @mBa THEN @mOng ELSE @mBa END,
         CASE WHEN @mOng < @mBa THEN @mBa  ELSE @mOng END,
         '1965-12-20', @t0),
        ('66666666-6666-6666-6666-000000000002',
         CASE WHEN @mTruong < @mMai THEN @mTruong ELSE @mMai    END,
         CASE WHEN @mTruong < @mMai THEN @mMai    ELSE @mTruong END,
         '1994-04-10', @t0);

    /* -----------------------------------------------------------------
       10. community.Posts, Comments, Reactions
       ----------------------------------------------------------------- */

    INSERT INTO community.Posts (Id, UserId, FamilyId, Content, CreatedAt)
    VALUES
        ('77777777-7777-7777-7777-000000000001', @uTruong, @fam,
         N'Nhà mình đã scan xong cuốn gia phả cũ, mọi người vào mục Di sản xem nhé.', DATEADD(DAY, 10, @t0)),
        ('77777777-7777-7777-7777-000000000002', @uHung, @fam,
         N'Ảnh chụp buổi giỗ tổ năm ngoái con đã tải lên thư viện ảnh.', DATEADD(DAY, 12, @t0));

    INSERT INTO community.Comments (Id, PostId, UserId, Content, CreatedAt)
    VALUES
        ('88888888-8888-8888-8888-000000000001', '77777777-7777-7777-7777-000000000001', @uMai,
         N'Cảm ơn anh, chữ trong bản scan đọc rõ lắm.', DATEADD(DAY, 10, @t0)),
        ('88888888-8888-8888-8888-000000000002', '77777777-7777-7777-7777-000000000001', @uHung,
         N'Con sẽ gõ lại phần chữ Nôm sang chữ quốc ngữ ạ.', DATEADD(DAY, 11, @t0)),
        ('88888888-8888-8888-8888-000000000003', '77777777-7777-7777-7777-000000000002', @uTruong,
         N'Ảnh đẹp lắm, nhớ ghi chú tên người trong ảnh.', DATEADD(DAY, 12, @t0));

    INSERT INTO community.Reactions (Id, PostId, UserId, Type, CreatedAt)
    VALUES
        ('99999999-9999-9999-9999-000000000001', '77777777-7777-7777-7777-000000000001', @uMai,  N'like',  DATEADD(DAY, 10, @t0)),
        ('99999999-9999-9999-9999-000000000002', '77777777-7777-7777-7777-000000000001', @uHung, N'love',  DATEADD(DAY, 11, @t0)),
        ('99999999-9999-9999-9999-000000000003', '77777777-7777-7777-7777-000000000002', @uTruong, N'like', DATEADD(DAY, 12, @t0));

    /* -----------------------------------------------------------------
       11. community.Events và EventParticipants
       ----------------------------------------------------------------- */

    INSERT INTO community.Events (Id, FamilyId, Title, EventDate, Location, CreatedAt)
    VALUES
        ('AAAAAAAA-AAAA-AAAA-AAAA-000000000001', @fam, N'Giỗ tổ họ Nguyễn Văn',
         CAST('2026-03-15T07:30:00' AS DATETIME2(3)), N'Nhà thờ họ, Thạch Thất, Hà Nội', @t0),
        ('AAAAAAAA-AAAA-AAAA-AAAA-000000000002', @fam, N'Họp mặt đầu xuân',
         CAST('2026-02-20T18:00:00' AS DATETIME2(3)), N'Nhà ông Trường, Hà Nội', @t0);

    INSERT INTO community.EventParticipants (Id, EventId, MemberId, RsvpStatus, CreatedAt)
    VALUES
        ('BBBBBBBB-BBBB-BBBB-BBBB-000000000001', 'AAAAAAAA-AAAA-AAAA-AAAA-000000000001', @mTruong, N'yes',   DATEADD(DAY, 15, @t0)),
        ('BBBBBBBB-BBBB-BBBB-BBBB-000000000002', 'AAAAAAAA-AAAA-AAAA-AAAA-000000000001', @mMai,    N'yes',   DATEADD(DAY, 15, @t0)),
        ('BBBBBBBB-BBBB-BBBB-BBBB-000000000003', 'AAAAAAAA-AAAA-AAAA-AAAA-000000000001', @mHung,   N'maybe', DATEADD(DAY, 16, @t0)),
        ('BBBBBBBB-BBBB-BBBB-BBBB-000000000004', 'AAAAAAAA-AAAA-AAAA-AAAA-000000000001', @mLan,    N'no',    DATEADD(DAY, 16, @t0)),
        ('BBBBBBBB-BBBB-BBBB-BBBB-000000000005', 'AAAAAAAA-AAAA-AAAA-AAAA-000000000002', @mTruong, N'yes',   DATEADD(DAY, 17, @t0)),
        ('BBBBBBBB-BBBB-BBBB-BBBB-000000000006', 'AAAAAAAA-AAAA-AAAA-AAAA-000000000002', @mHung,   N'yes',   DATEADD(DAY, 17, @t0));

    /* -----------------------------------------------------------------
       12. reports.AuditLog
       ----------------------------------------------------------------- */

    INSERT INTO reports.AuditLog (Id, UserId, Action, CreatedAt)
    VALUES
        ('CCCCCCCC-CCCC-CCCC-CCCC-000000000001', @uTruong, N'core.Families: tạo gia đình',             @t0),
        ('CCCCCCCC-CCCC-CCCC-CCCC-000000000002', @uTruong, N'core.MemberVerifications: duyệt Nguyễn Văn Hùng', DATEADD(DAY, 4, @t0)),
        ('CCCCCCCC-CCCC-CCCC-CCCC-000000000003', @uHung,   N'heritage.Items: tải lên ảnh giỗ tổ',      DATEADD(DAY, 12, @t0)),
        ('CCCCCCCC-CCCC-CCCC-CCCC-000000000004', NULL,     N'system: chạy sao lưu định kỳ',            DATEADD(DAY, 20, @t0));

    /* -----------------------------------------------------------------
       13. heritage.Items — phần của Người 4
       Đủ cả ba loại để kiểm thử ràng buộc CK_Heritage_Items_Payload.
       ----------------------------------------------------------------- */

    INSERT INTO heritage.Items
        (Id, FamilyId, CreatedByUserId, Type, Title, Description, Content, MediaUrl, CreatedAt)
    VALUES
        /* document: có cả Content và MediaUrl */
        ('EEEEEEEE-EEEE-EEEE-EEEE-000000000001', @fam, @uTruong, N'document',
         N'Gia phả họ Nguyễn Văn bản scan 1998',
         N'Bản scan cuốn gia phả viết tay, 42 trang.',
         N'Cuốn gia phả do cụ Nguyễn Văn Cẩn chép tay năm 1998, ghi lại bảy đời kể từ cụ tổ Nguyễn Văn Đạt.',
         N'/media/heritage/gia-pha-1998.pdf',
         DATEADD(DAY, 10, @t0)),

        /* document: chỉ có MediaUrl */
        ('EEEEEEEE-EEEE-EEEE-EEEE-000000000002', @fam, @uTruong, N'document',
         N'Sắc phong thời Nguyễn',
         N'Ảnh chụp sắc phong lưu tại nhà thờ họ.',
         NULL,
         N'/media/heritage/sac-phong.jpg',
         DATEADD(DAY, 11, @t0)),

        /* story: chỉ có Content */
        ('EEEEEEEE-EEEE-EEEE-EEEE-000000000003', @fam, @uMai, N'story',
         N'Chuyện cụ Cẩn dựng nhà thờ họ',
         N'Lời kể của bà Lê Thị Tâm, ghi lại năm 2024.',
         N'Năm 1975 cụ Cẩn trở về làng, góp gỗ và công của cả chi trưởng lẫn chi thứ để dựng lại nhà thờ họ trên nền cũ. Công việc kéo dài hai mùa, tới giỗ tổ năm 1977 mới xong phần mái.',
         NULL,
         DATEADD(DAY, 13, @t0)),

        /* story */
        ('EEEEEEEE-EEEE-EEEE-EEEE-000000000004', @fam, @uHung, N'story',
         N'Nghề mộc truyền trong họ',
         N'Ghi chép về nghề mộc ba đời.',
         N'Nghề mộc theo họ Nguyễn Văn từ đời cụ tổ. Cụ Cẩn học nghề năm mười bốn tuổi, sau truyền cho con cháu trong chi trưởng. Tới nay trong họ còn hai xưởng mộc ở Thạch Thất.',
         NULL,
         DATEADD(DAY, 14, @t0)),

        /* photo: bắt buộc có MediaUrl */
        ('EEEEEEEE-EEEE-EEEE-EEEE-000000000005', @fam, @uHung, N'photo',
         N'Giỗ tổ năm 2025 — chụp tập thể',
         N'Ảnh chụp trước sân nhà thờ họ.',
         NULL,
         N'/media/heritage/gio-to-2025-tap-the.jpg',
         DATEADD(DAY, 12, @t0)),

        ('EEEEEEEE-EEEE-EEEE-EEEE-000000000006', @fam, @uHung, N'photo',
         N'Nhà thờ họ sau khi tu sửa',
         N'Ảnh chụp năm 2024.',
         NULL,
         N'/media/heritage/nha-tho-ho-2024.jpg',
         DATEADD(DAY, 12, @t0)),

        ('EEEEEEEE-EEEE-EEEE-EEEE-000000000007', @fam, @uLan, N'photo',
         N'Bộ đục chạm của cụ Cẩn',
         N'Hiện vật còn giữ tại nhà thờ họ.',
         NULL,
         N'/media/heritage/bo-duc-cham.jpg',
         DATEADD(DAY, 18, @t0));

    COMMIT TRANSACTION;
    PRINT N'01_seed.sql: da chen xong du lieu mau.';
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    PRINT N'01_seed.sql: loi, da rollback toan bo.';
    THROW;
END CATCH
GO


/* ---------------------------------------------------------------------
   14. Đối chiếu số dòng sau khi seed
   Dùng khi nghiệm thu và khi chụp ảnh minh chứng.
   --------------------------------------------------------------------- */

SELECT N'core.Users'                AS BangDuLieu, COUNT(*) AS SoDong FROM core.Users               WHERE CAST(UserId AS CHAR(36)) LIKE '11111111-%'
UNION ALL SELECT N'core.Families',                 COUNT(*) FROM core.Families                      WHERE CAST(Id AS CHAR(36)) LIKE '22222222-%'
UNION ALL SELECT N'core.Branches',                 COUNT(*) FROM core.Branches                      WHERE CAST(Id AS CHAR(36)) LIKE '33333333-%'
UNION ALL SELECT N'core.MemberVerifications',      COUNT(*) FROM core.MemberVerifications           WHERE CAST(Id AS CHAR(36)) LIKE 'DDDDDDDD-%'
UNION ALL SELECT N'genealogy.Members',             COUNT(*) FROM genealogy.Members                  WHERE CAST(Id AS CHAR(36)) LIKE '44444444-%'
UNION ALL SELECT N'genealogy.ParentChild',         COUNT(*) FROM genealogy.ParentChild              WHERE CAST(Id AS CHAR(36)) LIKE '55555555-%'
UNION ALL SELECT N'genealogy.Marriages',           COUNT(*) FROM genealogy.Marriages                WHERE CAST(Id AS CHAR(36)) LIKE '66666666-%'
UNION ALL SELECT N'community.Posts',               COUNT(*) FROM community.Posts                    WHERE CAST(Id AS CHAR(36)) LIKE '77777777-%'
UNION ALL SELECT N'community.Comments',            COUNT(*) FROM community.Comments                 WHERE CAST(Id AS CHAR(36)) LIKE '88888888-%'
UNION ALL SELECT N'community.Reactions',           COUNT(*) FROM community.Reactions                WHERE CAST(Id AS CHAR(36)) LIKE '99999999-%'
UNION ALL SELECT N'community.Events',              COUNT(*) FROM community.Events                   WHERE CAST(Id AS CHAR(36)) LIKE 'AAAAAAAA-%'
UNION ALL SELECT N'community.EventParticipants',   COUNT(*) FROM community.EventParticipants        WHERE CAST(Id AS CHAR(36)) LIKE 'BBBBBBBB-%'
UNION ALL SELECT N'reports.AuditLog',              COUNT(*) FROM reports.AuditLog                   WHERE CAST(Id AS CHAR(36)) LIKE 'CCCCCCCC-%'
UNION ALL SELECT N'heritage.Items',                COUNT(*) FROM heritage.Items                     WHERE CAST(Id AS CHAR(36)) LIKE 'EEEEEEEE-%';
GO
