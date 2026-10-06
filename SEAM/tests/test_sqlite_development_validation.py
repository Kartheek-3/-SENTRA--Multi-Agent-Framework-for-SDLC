import tempfile
import pytest
from pathlib import Path
from backend.database.engine import DatabaseConfig, DatabaseEngine
from backend.models.state import ProjectState
from backend.foundation.models import ArtifactRecord, ArtifactType, ArtifactStatus

def test_sqlite_development_full_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_lifecycle_seam.db"
        config = DatabaseConfig()
        config.backend = "sqlite"
        config.sqlite_path = db_path

        # 1. Backend starts & 2. Database initializes
        engine = DatabaseEngine(config)
        conn_res = engine.validate_connection()
        assert conn_res["status"] == "PASS"
        assert conn_res["writable"] is True

        schema_res = engine.validate_schema()
        assert schema_res["valid"] is True
        assert "projects" in schema_res["present_tables"]
        assert "events" in schema_res["present_tables"]
        assert "artifacts" in schema_res["present_tables"]
        assert "schema_migrations" in schema_res["present_tables"]

        # 3. Project can be created & 4. ProjectState persists
        project_id = "proj-lifecycle-101"
        state = ProjectState(
            project_id=project_id,
            user_requirement="Build a real-time analytics dashboard",
            domain="Analytics"
        )
        engine.save_project(
            project_id=project_id,
            project_name="Analytics Dashboard",
            domain="Analytics",
            user_requirement=state.user_requirement,
            state_dict=state.model_dump(),
            workflow_status="pending"
        )
        fetched_proj = engine.get_project(project_id)
        assert fetched_proj is not None
        assert fetched_proj["project_name"] == "Analytics Dashboard"
        assert fetched_proj["state"]["domain"] == "Analytics"

        # 5. EventStore persists
        seq1 = engine.append_event({
            "event_id": "evt-lc-1",
            "project_id": project_id,
            "event": "PROJECT_CREATED",
            "timestamp": "2026-10-06T12:00:00Z"
        })
        seq2 = engine.append_event({
            "event_id": "evt-lc-2",
            "project_id": project_id,
            "event": "ANALYSIS_STARTED",
            "timestamp": "2026-10-06T12:01:00Z"
        })
        assert seq1 == 1
        assert seq2 == 2
        events = engine.list_events(project_id=project_id)
        assert len(events) == 2
        assert events[0]["event"] == "PROJECT_CREATED"

        # 6. Artifact metadata persists
        artifact_id = "art-lc-1"
        engine.save_artifact(
            artifact_id=artifact_id,
            project_id=project_id,
            path="src/dashboard.tsx",
            artifact_type="CODE",
            status="AVAILABLE",
            metadata_dict={"size": 2048, "generator": "CodingAgent"}
        )
        art = engine.get_artifact(artifact_id)
        assert art is not None
        assert art["path"] == "src/dashboard.tsx"
        assert art["metadata"]["generator"] == "CodingAgent"

        # 7. Evaluation data persists (stored as EVALUATION artifact)
        eval_artifact_id = "eval-lc-1"
        engine.save_artifact(
            artifact_id=eval_artifact_id,
            project_id=project_id,
            path="evaluation/datasets/experiment_results.json",
            artifact_type="SUMMARY",
            status="AVAILABLE",
            metadata_dict={"benchmark_score": 0.94, "pass_rate": 1.0}
        )
        eval_art = engine.get_artifact(eval_artifact_id)
        assert eval_art is not None
        assert eval_art["metadata"]["benchmark_score"] == 0.94

        # 8. Restart preserves expected persistent data
        engine_restarted = DatabaseEngine(config)
        restored_proj = engine_restarted.get_project(project_id)
        assert restored_proj is not None
        assert restored_proj["project_name"] == "Analytics Dashboard"
        assert restored_proj["state"]["user_requirement"] == "Build a real-time analytics dashboard"

        restored_events = engine_restarted.list_events(project_id=project_id)
        assert len(restored_events) == 2

        restored_artifacts = engine_restarted.list_artifacts(project_id=project_id)
        assert len(restored_artifacts) == 2

        # 9. Transactions work
        with engine_restarted.transaction() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE projects SET workflow_status = 'completed' WHERE project_id = ?;", (project_id,))
        updated_proj = engine_restarted.get_project(project_id)
        assert updated_proj["workflow_status"] == "completed"

        # 10. Errors roll back correctly
        with pytest.raises(RuntimeError):
            with engine_restarted.transaction() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE projects SET workflow_status = 'corrupted' WHERE project_id = ?;", (project_id,))
                raise RuntimeError("Simulated transaction fault")

        rolled_back_proj = engine_restarted.get_project(project_id)
        assert rolled_back_proj["workflow_status"] == "completed"
