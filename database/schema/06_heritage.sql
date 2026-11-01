/* =====================================================================
   database/schema/06_heritage.sql
   Người 4 — Di sản: tài liệu, câu chuyện và ảnh gia đình
   =====================================================================
   Thứ tự chạy: 00_schemas → 01_core → 02_genealogy → 03_community_events
                → 04_reports_ops → 05_late_foreign_keys → 06_heritage → seed

   Bảng heritage.Items theo ERD tại docs/erd/README.md:
     - Type nhận 'document' (tài liệu), 'story' (câu chuyện), 'photo' (ảnh)
     - Content giữ nội dung văn bản
     - MediaUrl giữ đường dẫn tệp ảnh hoặc tài liệu

   Chạy bằng database/init.sh (sqlcmd truyền sẵn biến DB_NAME).
   Nếu chạy trong SSMS: bật SQLCMD Mode (menu Query → SQLCMD Mode) và
   thêm dòng  :setvar DB_NAME "FamilyConnect"  ở đầu file.

   Script viết theo hướng chạy lại được nhiều lần: đã có bảng thì bỏ qua,
   không xóa dữ liệu sẵn có.
   ===================================================================== */

USE [$(DB_NAME)];
GO

SET XACT_ABORT ON;
GO

/* ---------------------------------------------------------------------
   1. Kiểm tra phụ thuộc
   Dừng ngay với thông báo rõ ràng nếu thành viên khác chưa chạy script
   của họ, thay vì báo lỗi khóa ngoại khó đọc.
   --------------------------------------------------------------------- */

IF SCHEMA_ID('heritage') IS NULL
    THROW 50601, N'Thiếu schema heritage. Chạy database/schema/00_schemas.sql trước.', 1;
GO

IF OBJECT_ID(N'core.Families', N'U') IS NULL
    THROW 50602, N'Thiếu bảng core.Families. Chạy database/schema/01_core.sql trước.', 1;
GO

IF OBJECT_ID(N'core.Users', N'U') IS NULL
    THROW 50603, N'Thiếu bảng core.Users. Chạy database/schema/01_core.sql trước.', 1;
GO


/* ---------------------------------------------------------------------
   2. Bảng heritage.Items
   --------------------------------------------------------------------- */

IF OBJECT_ID(N'heritage.Items', N'U') IS NULL
BEGIN
    CREATE TABLE heritage.Items
    (
        Id              UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT DF_Heritage_Items_Id DEFAULT NEWID()
            CONSTRAINT PK_Heritage_Items PRIMARY KEY,

        FamilyId        UNIQUEIDENTIFIER NOT NULL,
        CreatedByUserId UNIQUEIDENTIFIER NOT NULL,

        Type            NVARCHAR(20)     NOT NULL,
        Title           NVARCHAR(200)    NOT NULL,
        Description     NVARCHAR(500)    NULL,
        Content         NVARCHAR(MAX)    NULL,
        MediaUrl        NVARCHAR(500)    NULL,

        CreatedAt       DATETIME2(3)     NOT NULL
            CONSTRAINT DF_Heritage_Items_CreatedAt DEFAULT SYSUTCDATETIME(),

        /* Tư liệu thuộc về một gia đình và do một tài khoản đóng góp.
           Để mặc định NO ACTION: xóa gia đình hoặc tài khoản sẽ bị chặn
           nếu còn tư liệu, tránh mất dữ liệu di sản ngoài ý muốn. */
        CONSTRAINT FK_Heritage_Items_Family
            FOREIGN KEY (FamilyId)        REFERENCES core.Families (Id),
        CONSTRAINT FK_Heritage_Items_CreatedByUser
            FOREIGN KEY (CreatedByUserId) REFERENCES core.Users (UserId),

        CONSTRAINT CK_Heritage_Items_Type
            CHECK (Type IN (N'document', N'story', N'photo')),

        CONSTRAINT CK_Heritage_Items_Title
            CHECK (LEN(LTRIM(RTRIM(Title))) > 0),

        /* Ràng buộc nghiệp vụ do Người 4 đề xuất, không có trong ERD.
           Mỗi loại phải có phần nội dung tương ứng, tránh tạo bản ghi rỗng:
             photo    bắt buộc có MediaUrl
             story    bắt buộc có Content
             document phải có ít nhất một trong hai
           Nhóm trưởng có thể bỏ ràng buộc này nếu thấy quá chặt. */
        CONSTRAINT CK_Heritage_Items_Payload CHECK
        (
            (Type = N'photo'    AND MediaUrl IS NOT NULL)
         OR (Type = N'story'    AND Content  IS NOT NULL)
         OR (Type = N'document' AND (Content IS NOT NULL OR MediaUrl IS NOT NULL))
        )
    );
END
GO


/* ---------------------------------------------------------------------
   3. Chỉ mục
   Truy vấn thường gặp ở trang di sản: lọc theo gia đình, lọc thêm theo
   loại, và sắp xếp mới nhất trước.
   --------------------------------------------------------------------- */

IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE name = N'IX_Heritage_Items_Family_CreatedAt'
                 AND object_id = OBJECT_ID(N'heritage.Items'))
    CREATE INDEX IX_Heritage_Items_Family_CreatedAt
        ON heritage.Items (FamilyId, CreatedAt DESC)
        INCLUDE (Type, Title);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE name = N'IX_Heritage_Items_Family_Type'
                 AND object_id = OBJECT_ID(N'heritage.Items'))
    CREATE INDEX IX_Heritage_Items_Family_Type
        ON heritage.Items (FamilyId, Type);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE name = N'IX_Heritage_Items_CreatedByUser'
                 AND object_id = OBJECT_ID(N'heritage.Items'))
    CREATE INDEX IX_Heritage_Items_CreatedByUser
        ON heritage.Items (CreatedByUserId);
GO


/* ---------------------------------------------------------------------
   4. Mô tả cột để người khác đọc schema hiểu ngay
   --------------------------------------------------------------------- */

IF NOT EXISTS (SELECT 1 FROM sys.extended_properties
               WHERE major_id = OBJECT_ID(N'heritage.Items')
                 AND minor_id = 0 AND name = N'MS_Description')
    EXEC sys.sp_addextendedproperty
        @name = N'MS_Description',
        @value = N'Tài liệu, câu chuyện và ảnh gia đình của một gia đình.',
        @level0type = N'SCHEMA', @level0name = N'heritage',
        @level1type = N'TABLE',  @level1name = N'Items';
GO

PRINT N'06_heritage.sql: hoan tat bang heritage.Items.';
GO

-- Bảng Vinh danh thành viên xuất sắc
IF OBJECT_ID(N'heritage.Honors', N'U') IS NULL
BEGIN
    CREATE TABLE [heritage].[Honors]
    (
        [Id] UNIQUEIDENTIFIER NOT NULL CONSTRAINT [DF_Honors_Id] DEFAULT NEWSEQUENTIALID(),
        [MemberId] UNIQUEIDENTIFIER NOT NULL,
        [Title] NVARCHAR(200) NOT NULL,
        [Description] NVARCHAR(1000) NULL,
        [DateAwarded] DATE NULL,
        [CreatedAt] DATETIME2(0) NOT NULL CONSTRAINT [DF_Honors_CreatedAt] DEFAULT SYSUTCDATETIME(),
        
        CONSTRAINT [PK_Honors] PRIMARY KEY ([Id]),
        CONSTRAINT [FK_Honors_Members] FOREIGN KEY ([MemberId]) 
            REFERENCES [genealogy].[Members] ([Id]) ON DELETE CASCADE
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE [name] = N'IX_Honors_MemberId' AND [object_id] = OBJECT_ID(N'heritage.Honors'))
    CREATE INDEX [IX_Honors_MemberId] ON [heritage].[Honors] ([MemberId]);
GO