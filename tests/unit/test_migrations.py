import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("migrate", Path(__file__).resolve().parents[2] / "database/migrate.py")
migrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrate)


class Connection:
    def __init__(self): self.batches = []
    def exec_driver_sql(self, sql):
        self.batches.append(sql.strip())
        return self
    def close(self): pass


def test_migration_applies_in_order_without_seed_or_database_init(tmp_path):
    for folder in ("schema", "views", "procedures", "triggers", "shared", "seed"):
        (tmp_path / folder).mkdir()
    (tmp_path / "schema/00_schemas.sql").write_text("DO NOT RUN INIT", encoding="utf-8")
    (tmp_path / "schema/01.sql").write_text("USE [$(DB_NAME)];\r\nGO -- batch\r\nSELECT 1;", encoding="utf-8")
    (tmp_path / "views/01.sql").write_text("SELECT 2;\nGO\n", encoding="utf-8")
    (tmp_path / "shared/06_permissions.sql").write_text("DO NOT CHANGE DATABASE ACCOUNTS", encoding="utf-8")
    (tmp_path / "seed/01.sql").write_text("DO NOT RUN SEED", encoding="utf-8")
    connection = Connection()
    migrate.apply_scripts(connection, "FamilyConnect_Test", tmp_path)
    assert connection.batches == ["USE [FamilyConnect_Test];", "SELECT 1;", "SELECT 2;"]


@pytest.mark.parametrize("database", ["master", "MODEL", "tempdb", "msdb", "bad]; DROP DATABASE x;--", ""])
def test_migration_rejects_system_or_injected_database_names(tmp_path, database):
    connection = Connection()
    with pytest.raises(ValueError): migrate.apply_scripts(connection, database, tmp_path)
    assert not connection.batches
