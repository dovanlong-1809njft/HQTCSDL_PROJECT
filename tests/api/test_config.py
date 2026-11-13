from pathlib import Path


def test_config_loads_from_short_docker_path(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "config-import-test-secret-at-least-32-characters")
    monkeypatch.setenv("MSSQL_DB", "ConfigImportTest")
    source = Path(__file__).resolve().parents[2] / "apps/backend/app/core/config.py"
    namespace = {"__file__": "/app/app/core/config.py", "__name__": "config_import_test"}
    exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), namespace)
    assert namespace["JWT_SECRET_KEY"] == "config-import-test-secret-at-least-32-characters"
    assert namespace["MSSQL_DB"] == "ConfigImportTest"
