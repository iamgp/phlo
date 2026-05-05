"""Unit tests for PostgREST lifecycle hooks."""

from __future__ import annotations


def test_reload_schema_notifies_postgrest(monkeypatch, tmp_path):
    """Schema reload should use PostgREST's NOTIFY channel."""
    from phlo_postgrest import hooks

    config_dir = tmp_path / ".phlo" / "postgrest" / "conf"
    config_dir.mkdir(parents=True)
    (config_dir / "postgrest.conf").write_text(
        'db-uri = "postgresql://phlo:secret@postgres:5432/phlo"\n'
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(hooks, "_resolve_container_name", lambda service: f"demo-{service}-1")

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd

        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr(hooks.subprocess, "run", fake_run)

    hooks.reload_schema()

    assert captured["cmd"][:3] == ["docker", "exec", "-e"]
    assert "PGPASSWORD=secret" in captured["cmd"]
    assert "demo-postgres-1" in captured["cmd"]
    assert "NOTIFY pgrst, 'reload schema';" in captured["cmd"]
