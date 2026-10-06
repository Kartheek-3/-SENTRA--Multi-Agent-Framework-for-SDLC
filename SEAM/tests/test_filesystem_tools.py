from backend.tools.builtin import FileReadTool, FileSearchTool, FileWriteTool
from backend.tools.schemas import ToolExecutionContext


def test_file_write_and_read_are_project_root_restricted(tmp_path):
    context = ToolExecutionContext(project_id="p", agent_name="CodingAgent", project_root=str(tmp_path))
    write = FileWriteTool()
    read = FileReadTool()

    write_result = write.execute(write.validate_input({"path": "src/app.py", "content": "print('ok')"}), context)
    read_result = read.execute(read.validate_input({"path": "src/app.py"}), context)

    assert write_result.success is True
    assert "print" in read_result.stdout


def test_file_search_finds_matching_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x", encoding="utf-8")
    tool = FileSearchTool()

    result = tool.execute(tool.validate_input({"pattern": "main"}), ToolExecutionContext(project_id="p", agent_name="QAAgent", project_root=str(tmp_path)))

    assert result.structured_data["matches"] == ["src\\main.py"] or result.structured_data["matches"] == ["src/main.py"]
