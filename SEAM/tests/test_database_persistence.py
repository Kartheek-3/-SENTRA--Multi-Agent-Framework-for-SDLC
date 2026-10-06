import os
import tempfile
import pytest
from pathlib import Path
from backend.database.engine import DatabaseConfig, DatabaseEngine

def test_database_sqlite_init_and_schema():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_seam.db"
        config = DatabaseConfig()
        config.backend = "sqlite"
        config.sqlite_path = db_path

        engine = DatabaseEngine(config)
        conn_res = engine.validate_connection()
        assert conn_res["status"] == "PASS"
        assert conn_res["writable"] is True

        schema_res = engine.validate_schema()
        assert schema_res["valid"] is True
        assert "projects" in schema_res["present_tables"]
        assert "events" in schema_res["present_tables"]
        assert "artifacts" in schema_res["present_tables"]

def test_database_project_crud_and_persistence_across_restart():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_seam.db"
        config = DatabaseConfig()
        config.backend = "sqlite"
        config.sqlite_path = db_path

        # Step 1: Write project
        engine1 = DatabaseEngine(config)
        project_id = "test-proj-123"
        engine1.save_project(
            project_id=project_id,
            project_name="Test Project",
            domain="Fintech",
            user_requirement="Build ledger",
            state_dict={"version": 1, "status": "running"},
            workflow_status="running"
        )

        proj1 = engine1.get_project(project_id)
        assert proj1 is not None
        assert proj1["project_name"] == "Test Project"
        assert proj1["state"]["status"] == "running"

        # Step 2: Reopen with new engine instance (restart simulation)
        engine2 = DatabaseEngine(config)
        proj2 = engine2.get_project(project_id)
        assert proj2 is not None
        assert proj2["project_name"] == "Test Project"
        assert proj2["domain"] == "Fintech"
        assert proj2["state"]["version"] == 1

        all_projects = engine2.list_projects()
        assert len(all_projects) >= 1
        assert any(p["project_id"] == project_id for p in all_projects)

def test_database_event_store_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_seam.db"
        config = DatabaseConfig()
        config.backend = "sqlite"
        config.sqlite_path = db_path

        engine = DatabaseEngine(config)
        seq1 = engine.append_event({
            "event_id": "evt-01",
            "project_id": "proj-1",
            "event_type": "ANALYSIS_STARTED",
            "timestamp": "2026-10-06T00:00:00Z"
        })
        seq2 = engine.append_event({
            "event_id": "evt-02",
            "project_id": "proj-1",
            "event_type": "PLANNING_COMPLETED",
            "timestamp": "2026-10-06T00:01:00Z"
        })

        assert seq1 == 1
        assert seq2 == 2

        events = engine.list_events(project_id="proj-1")
        assert len(events) == 2
        assert events[0]["event_type"] == "ANALYSIS_STARTED"
        assert events[1]["event_type"] == "PLANNING_COMPLETED"

def test_database_transaction_rollback_on_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_seam.db"
        config = DatabaseConfig()
        config.backend = "sqlite"
        config.sqlite_path = db_path

        engine = DatabaseEngine(config)
        
        # Transaction that fails halfway
        with pytest.raises(ValueError):
            with engine.transaction() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO projects (project_id, project_name) VALUES ('rollback-proj', 'Rollback');")
                raise ValueError("Simulated fault before commit")

        # Verify record was rolled back
        assert engine.get_project("rollback-proj") is None

def test_database_safe_url_masks_credentials():
    config = DatabaseConfig()
    config.backend = "postgresql"
    config.postgres_url = "postgresql://admin:super_secret_password@db.example.com:5432/seam_production"

    safe_url = config.get_safe_url()
    assert "super_secret_password" not in safe_url
    assert "admin:***@db.example.com:5432/seam_production" in safe_url

def test_database_postgresql_status_when_unconfigured():
    config = DatabaseConfig()
    config.backend = "postgresql"
    config.postgres_url = ""

    engine = DatabaseEngine(config)
    res = engine.validate_connection()
    assert res["backend"] == "postgresql"
    assert res["status"] == "NOT_CONFIGURED"
    assert "NOT_CONFIGURED" in res["url"]

def test_database_schema_migrations_deterministic():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_seam.db"
        config = DatabaseConfig()
        config.backend = "sqlite"
        config.sqlite_path = db_path

        engine = DatabaseEngine(config)
        applied = engine.get_applied_migrations()
        assert "001_initial_schema" in applied

        # Running migrations again is a deterministic no-op
        second_run = engine.run_migrations()
        assert second_run == []
        assert engine.get_applied_migrations() == ["001_initial_schema"]

def test_database_artifact_crud_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_seam.db"
        config = DatabaseConfig()
        config.backend = "sqlite"
        config.sqlite_path = db_path

        engine = DatabaseEngine(config)
        artifact_id = "art-test-001"
        project_id = "proj-xyz"
        engine.save_artifact(
            artifact_id=artifact_id,
            project_id=project_id,
            path="src/main.py",
            artifact_type="CODE",
            status="READY",
            metadata_dict={"size": 1024, "author": "CodingAgent"}
        )

        art = engine.get_artifact(artifact_id)
        assert art is not None
        assert art["artifact_id"] == artifact_id
        assert art["project_id"] == project_id
        assert art["path"] == "src/main.py"
        assert art["metadata"]["author"] == "CodingAgent"

        artifacts = engine.list_artifacts(project_id=project_id)
        assert len(artifacts) >= 1
        assert artifacts[0]["artifact_id"] == artifact_id

def test_event_store_and_artifact_registry_dual_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        from backend.foundation.services import EventStore, ArtifactRegistry
        from backend.foundation.models import ArtifactRecord, ArtifactType, ArtifactStatus

        es = EventStore()
        evt = es.append({
            "event_id": "evt-dual-01",
            "project_id": "proj-dual-test",
            "event": "ANALYSIS_STARTED",
            "timestamp": "2026-10-06T12:00:00Z"
        })
        assert evt.sequence_number >= 1

        ar = ArtifactRegistry()
        record = ar.create(ArtifactRecord(
            artifact_id="art-dual-01",
            project_id="proj-dual-test",
            title="Architecture Spec",
            path="docs/architecture.md",
            type=ArtifactType.ARCHITECTURE,
            status=ArtifactStatus.AVAILABLE,
            metadata={"source": "PlanningAgent"}
        ))
        assert record.artifact_id == "art-dual-01"

        fetched_art = ar.get("art-dual-01")
        assert fetched_art is not None
        assert fetched_art.path == "docs/architecture.md"

def test_postgresql_dialect_execution_with_mock():
    from unittest.mock import MagicMock
    config = DatabaseConfig()
    config.backend = "postgresql"
    config.postgres_url = "postgresql://mock_user:mock_pass@localhost:5432/mock_db"

    engine = DatabaseEngine.__new__(DatabaseEngine)
    engine.config = config
    from threading import RLock
    engine._lock = RLock()

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    engine._get_connection = MagicMock(return_value=mock_conn)

    # Test save_project on PostgreSQL
    engine.save_project(
        project_id="pg-proj-1",
        project_name="PG Project",
        domain="Fintech",
        user_requirement="PostgreSQL ledger",
        state_dict={"status": "active"},
        workflow_status="active"
    )
    assert mock_cur.execute.called
    executed_sql = mock_cur.execute.call_args[0][0]
    assert "INSERT INTO projects" in executed_sql
    assert "%s" in executed_sql
    assert "EXCLUDED.project_name" in executed_sql

    # Test append_event on PostgreSQL
    mock_cur.fetchone.return_value = (1,)
    seq = engine.append_event({
        "event_id": "pg-evt-1",
        "project_id": "pg-proj-1",
        "event": "ANALYSIS_STARTED",
        "timestamp": "2026-10-06T12:00:00Z"
    })
    assert seq == 1
    event_sql = mock_cur.execute.call_args[0][0]
    assert "INSERT INTO events" in event_sql
    assert "%s" in event_sql

    # Test save_artifact on PostgreSQL
    engine.save_artifact(
        artifact_id="pg-art-1",
        project_id="pg-proj-1",
        path="src/app.py",
        artifact_type="CODE",
        status="AVAILABLE",
        metadata_dict={"size": 512}
    )
    artifact_sql = mock_cur.execute.call_args[0][0]
    assert "INSERT INTO artifacts" in artifact_sql
    assert "EXCLUDED.metadata_json" in artifact_sql



