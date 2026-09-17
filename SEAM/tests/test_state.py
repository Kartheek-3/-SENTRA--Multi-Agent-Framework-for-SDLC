from backend.models.state import ProjectState

def test_project_state_initialization():
    state = ProjectState(project_id="123", user_requirement="Build a store")
    assert state.project_id == "123"
    assert state.user_requirement == "Build a store"
    assert state.tasks == {}
    assert state.completed_tasks == []
