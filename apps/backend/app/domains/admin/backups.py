"""Native SQL Server backups; paths and the target database never come from clients."""
from contextlib import contextmanager
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine
from app.core.maintenance import application_lock, master_engine


def command(connection, statement, parameters=()):
    # BACKUP/RESTORE emit progress result sets; closing before draining them cancels the operation.
    cursor = connection.connection.cursor()
    try:
        cursor.execute(statement, parameters)
        while cursor.nextset():
            pass
    except connection.dialect.dbapi.Error:
        raise SQLAlchemyError("SQL Server maintenance command failed") from None
    finally:
        cursor.close()


class DatabaseBackups:
    def __init__(self, target_engine):
        self.target_engine = target_engine
        self.database = target_engine.url.database
        if (not self.database or len(self.database) > 128
                or self.database.lower() in {"master", "model", "msdb", "tempdb"}
                or any(ord(c) < 32 for c in self.database)):
            raise ValueError("A user database is required")
        self.quoted_database = "[" + self.database.replace("]", "]]") + "]"

    @contextmanager
    def connection(self):
        try:
            with master_engine.connect() as connection:
                yield connection
        except SQLAlchemyError:
            raise HTTPException(503, "Không thực hiện được thao tác SQL Server. Kiểm tra quyền backup/restore, dung lượng và file sao lưu trên máy chủ.") from None

    def _catalog(self, connection):
        return connection.execute(text("""
            SELECT b.name,
                   SWITCHOFFSET(TODATETIMEOFFSET(b.backup_finish_date,
                       CASE WHEN b.time_zone BETWEEN -48 AND 48 THEN b.time_zone * 15
                            ELSE DATEPART(TZOFFSET, SYSDATETIMEOFFSET()) END), '+00:00') AS created_at,
                   CAST(b.backup_size AS bigint) AS size_bytes, m.physical_device_name AS path
            FROM msdb.dbo.backupset b
            JOIN msdb.dbo.backupmediafamily m ON m.media_set_id=b.media_set_id
            CROSS APPLY sys.dm_os_file_exists(m.physical_device_name) f
            WHERE b.database_name=:database AND b.type='D' AND b.is_copy_only=1
              AND b.has_backup_checksums=1 AND b.is_damaged=0 AND b.position=1
              AND b.name LIKE 'FamilyConnect:%' AND f.file_exists=1
            ORDER BY b.backup_finish_date DESC, b.backup_set_id DESC
        """), {"database": self.database}).mappings().all()

    def _directory(self, connection):
        path = connection.execute(text("SELECT CONVERT(nvarchar(4000), SERVERPROPERTY('InstanceDefaultBackupPath'))")).scalar_one()
        if not path:
            raise HTTPException(503, "SQL Server chưa có thư mục sao lưu mặc định.")
        return path.rstrip("/\\") + ("\\" if "\\" in path else "/")

    def _rows(self, connection):
        directory = self._directory(connection)
        rows = []
        for row in self._catalog(connection):
            try:
                identifier = UUID(row["name"].removeprefix("FamilyConnect:"))
            except ValueError:
                continue
            if row["path"] == directory + f"fc_{identifier}.bak":
                rows.append({**row, "id": str(identifier), "file_name": f"fc_{identifier}.bak"})
        return rows

    def list(self):
        with self.connection() as connection:
            return {"database": self.database, "backups": [self._public(row) for row in self._rows(connection)]}

    @staticmethod
    def _public(row):
        return {key: row[key] for key in ("id", "file_name", "created_at", "size_bytes")}

    def _find(self, connection, identifier):
        row = next((row for row in self._rows(connection) if row["id"] == str(identifier)), None)
        if row is None:
            raise HTTPException(404, "Không tìm thấy bản sao lưu của database này.")
        return row

    def _verify(self, connection, row):
        header = connection.execute(text("RESTORE HEADERONLY FROM DISK=:path"), {"path": row["path"]}).mappings().one()
        if (header["DatabaseName"] != self.database or header["BackupType"] != 1
                or header["BackupName"] != row["name"] or not header["HasBackupChecksums"]
                or header["IsDamaged"]):
            raise HTTPException(409, "File sao lưu không đúng database hoặc không còn hợp lệ.")
        command(connection, "RESTORE VERIFYONLY FROM DISK=? WITH CHECKSUM", (row["path"],))

    def _audit(self, connection, actor_id, action):
        connection.execute(text(f"""
            INSERT INTO {self.quoted_database}.reports.AuditLog (UserId, Action)
            VALUES ((SELECT UserId FROM {self.quoted_database}.core.Users WHERE UserId=:actor), :action)
        """), {"actor": str(actor_id), "action": f"{action}; actor={actor_id}"}).close()

    def _check_admin(self, connection, actor_id):
        active = connection.execute(text(f"""SELECT COUNT(*) FROM {self.quoted_database}.core.Users
            WHERE UserId=:actor AND Role='admin' AND IsActive=1"""), {"actor": str(actor_id)}).scalar_one()
        if not active:
            raise HTTPException(403, "Tài khoản không còn quyền quản trị.")

    def _create(self, connection, actor_id):
        identifier = uuid4()
        path = self._directory(connection) + f"fc_{identifier}.bak"
        command(connection, f"BACKUP DATABASE {self.quoted_database} TO DISK=? WITH COPY_ONLY, CHECKSUM, NAME=?",
                (path, f"FamilyConnect:{identifier}"))
        row = self._find(connection, identifier)
        self._verify(connection, row)
        self._audit(connection, actor_id, f"BACKUP_DATABASE {identifier}")
        return row

    def create(self, actor_id):
        with self.connection() as connection:
            with application_lock(connection, f"FamilyConnect:operations:{self.database}"):
                self._check_admin(connection, actor_id)
                return self._public(self._create(connection, actor_id))

    def delete(self, identifier, actor_id):
        with self.connection() as connection:
            with application_lock(connection, f"FamilyConnect:operations:{self.database}"):
                self._check_admin(connection, actor_id)
                row = self._find(connection, identifier)
                # Delete one catalog-owned backup file; never pass a directory or wildcard.
                command(connection, "EXEC master.dbo.xp_delete_file 0, ?", (row["path"],))
                exists = connection.execute(text("SELECT file_exists FROM sys.dm_os_file_exists(:path)"),
                                            {"path": row["path"]}).scalar_one()
                if exists:
                    raise HTTPException(503, "SQL Server chưa xóa được file sao lưu. Hãy kiểm tra quyền truy cập file trên máy chủ.")
                try:
                    self._audit(connection, actor_id, f"DELETE_BACKUP {identifier}")
                except SQLAlchemyError:
                    raise HTTPException(503, "Đã xóa file sao lưu nhưng chưa ghi được nhật ký. Hãy tải lại danh sách và kiểm tra SQL Server.") from None

    def _restore(self, connection, row):
        try:
            command(connection, f"ALTER DATABASE {self.quoted_database} SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            command(connection, f"RESTORE DATABASE {self.quoted_database} FROM DISK=? WITH REPLACE, CHECKSUM, RECOVERY", (row["path"],))
        finally:
            command(connection, f"ALTER DATABASE {self.quoted_database} SET MULTI_USER")

    def restore(self, identifier, actor_id):
        # shortcut: synchronous operations suit this demo database; use jobs before backups exceed the proxy timeout.
        with self.connection() as connection:
            with application_lock(connection, f"FamilyConnect:operations:{self.database}"):
                with application_lock(connection, f"FamilyConnect:maintenance:{self.database}", timeout=15000):
                    self._check_admin(connection, actor_id)
                    selected = self._find(connection, identifier)
                    self._verify(connection, selected)
                    safety = self._create(connection, actor_id)
                    self.target_engine.dispose()
                    try:
                        self._restore(connection, selected)
                    except SQLAlchemyError:
                        try:
                            self._restore(connection, safety)
                            self._audit(connection, actor_id, f"RESTORE_FAILED_RECOVERED {identifier}")
                        except SQLAlchemyError:
                            raise HTTPException(503, f"Khôi phục thất bại. Cần quản trị SQL Server kiểm tra. Bản an toàn: {safety['file_name']}.") from None
                        raise HTTPException(503, "Khôi phục thất bại; đã phục hồi dữ liệu từ bản an toàn. Vui lòng tải lại trang.") from None
                    self._audit(connection, actor_id, f"RESTORE_DATABASE {identifier}; safety={safety['id']}")
                    return {"database": self.database, "safety_backup_id": safety["id"],
                            "message": "Đã khôi phục database. Hãy đăng nhập lại bằng tài khoản có trong bản sao lưu."}


database_backups = DatabaseBackups(engine)


def get_database_backups():
    return database_backups
