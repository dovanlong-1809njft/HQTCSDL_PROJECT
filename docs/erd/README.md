# Sơ đồ ERD FamilyConnect

Đây là sơ đồ thiết kế dữ liệu mà nhóm thống nhất cho FamilyConnect. Các file SQL tương ứng trong `database/schema/` đang để trống để thành viên lần lượt triển khai.

```mermaid
erDiagram
    CORE_USERS {
        uniqueidentifier UserId PK
        nvarchar Email UK
        nvarchar PasswordHash
        nvarchar FullName
        nvarchar Role
        bit IsActive
        datetime2 CreatedAt
    }
    CORE_FAMILIES {
        uniqueidentifier Id PK
        nvarchar Name
        datetime2 CreatedAt
    }
    CORE_BRANCHES {
        uniqueidentifier Id PK
        uniqueidentifier FamilyId FK
        nvarchar Name
        datetime2 CreatedAt
    }
    CORE_MEMBER_VERIFICATIONS {
        uniqueidentifier Id PK
        uniqueidentifier UserId FK
        uniqueidentifier MemberId FK
        nvarchar Status
        datetime2 CreatedAt
    }
    GENEALOGY_MEMBERS {
        uniqueidentifier Id PK
        uniqueidentifier FamilyId FK
        uniqueidentifier BranchId FK "nullable"
        uniqueidentifier UserId FK "nullable, unique"
        nvarchar FullName
        date BirthDate "nullable"
        nvarchar Occupation "nullable"
        nvarchar Location "nullable"
        datetime2 CreatedAt
    }
    GENEALOGY_PARENT_CHILD {
        uniqueidentifier Id PK
        uniqueidentifier ParentId FK
        uniqueidentifier ChildId FK
        datetime2 CreatedAt
    }
    GENEALOGY_MARRIAGES {
        uniqueidentifier Id PK
        uniqueidentifier Spouse1Id FK
        uniqueidentifier Spouse2Id FK
        date MarriedDate "nullable"
        datetime2 CreatedAt
    }
    COMMUNITY_POSTS {
        uniqueidentifier Id PK
        uniqueidentifier UserId FK
        uniqueidentifier FamilyId FK
        nvarchar Content
        datetime2 CreatedAt
    }
    COMMUNITY_COMMENTS {
        uniqueidentifier Id PK
        uniqueidentifier PostId FK
        uniqueidentifier UserId FK
        nvarchar Content
        datetime2 CreatedAt
    }
    COMMUNITY_REACTIONS {
        uniqueidentifier Id PK
        uniqueidentifier PostId FK
        uniqueidentifier UserId FK
        nvarchar Type
        datetime2 CreatedAt
    }
    COMMUNITY_EVENTS {
        uniqueidentifier Id PK
        uniqueidentifier FamilyId FK
        nvarchar Title
        datetime2 EventDate
        nvarchar Location
        datetime2 CreatedAt
    }
    COMMUNITY_EVENT_PARTICIPANTS {
        uniqueidentifier Id PK
        uniqueidentifier EventId FK
        uniqueidentifier MemberId FK
        nvarchar RsvpStatus
        datetime2 CreatedAt
    }
    REPORTS_AUDIT_LOG {
        uniqueidentifier Id PK
        uniqueidentifier UserId FK "nullable"
        nvarchar Action
        datetime2 CreatedAt
    }
    HERITAGE_ITEMS {
        uniqueidentifier Id PK
        uniqueidentifier FamilyId FK
        uniqueidentifier CreatedByUserId FK
        nvarchar Type
        nvarchar Title
        nvarchar Description "nullable"
        nvarchar Content "nullable"
        nvarchar MediaUrl "nullable"
        datetime2 CreatedAt
    }

    CORE_FAMILIES ||--o{ CORE_BRANCHES : has
    CORE_FAMILIES ||--o{ GENEALOGY_MEMBERS : contains
    CORE_BRANCHES o|--o{ GENEALOGY_MEMBERS : groups
    CORE_USERS o|--o| GENEALOGY_MEMBERS : linked_account
    CORE_USERS ||--o{ CORE_MEMBER_VERIFICATIONS : requests
    GENEALOGY_MEMBERS ||--o{ CORE_MEMBER_VERIFICATIONS : verified_member
    GENEALOGY_MEMBERS ||--o{ GENEALOGY_PARENT_CHILD : parent
    GENEALOGY_MEMBERS ||--o{ GENEALOGY_PARENT_CHILD : child
    GENEALOGY_MEMBERS ||--o{ GENEALOGY_MARRIAGES : spouse1
    GENEALOGY_MEMBERS ||--o{ GENEALOGY_MARRIAGES : spouse2
    CORE_USERS ||--o{ COMMUNITY_POSTS : writes
    CORE_FAMILIES ||--o{ COMMUNITY_POSTS : owns
    COMMUNITY_POSTS ||--o{ COMMUNITY_COMMENTS : has
    CORE_USERS ||--o{ COMMUNITY_COMMENTS : writes
    COMMUNITY_POSTS ||--o{ COMMUNITY_REACTIONS : receives
    CORE_USERS ||--o{ COMMUNITY_REACTIONS : reacts
    CORE_FAMILIES ||--o{ COMMUNITY_EVENTS : hosts
    COMMUNITY_EVENTS ||--o{ COMMUNITY_EVENT_PARTICIPANTS : has
    GENEALOGY_MEMBERS ||--o{ COMMUNITY_EVENT_PARTICIPANTS : attends
    CORE_USERS o|--o{ REPORTS_AUDIT_LOG : performs
    CORE_FAMILIES ||--o{ HERITAGE_ITEMS : preserves
    CORE_USERS ||--o{ HERITAGE_ITEMS : contributes
```

## Quy ước trong thiết kế

- Theo thiết kế, ERD có 14 bảng: `core` có 4, `genealogy` có 3, `community` có 5, `reports` có 1 và `heritage` có 1. Đây là số bảng dự kiến, chưa phải số bảng đã tạo trong database.
- `heritage.Items` lưu tài liệu (`document`), câu chuyện (`story`) hoặc ảnh (`photo`). Cột `Content` dùng cho nội dung văn bản; `MediaUrl` lưu đường dẫn tệp ảnh hoặc tài liệu.
- Theo thiết kế, `genealogy.Marriages` lưu một cặp theo thứ tự `Spouse1Id < Spouse2Id`; backend cần sắp xếp hai UUID trước khi ghi.
- `genealogy.Members.UserId` là tùy chọn và duy nhất khi có giá trị. `core.MemberVerifications.MemberId` tham chiếu thành viên qua FK được thêm ở script cuối.
- Theo thiết kế, xóa bài viết sẽ xóa bình luận và reaction; xóa sự kiện sẽ xóa các RSVP liên quan.

## Nguồn dữ liệu

Khi triển khai SQL, đối chiếu các bảng và quan hệ với sơ đồ này. Xem [hướng dẫn database](../../database/README.md) để biết thứ tự file và cách chạy sau khi nhóm hoàn thành script.
