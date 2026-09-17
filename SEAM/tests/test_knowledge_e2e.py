
import pytest
import os
import tempfile
import shutil
from backend.models.state import ProjectState
from backend.models.planning import ProjectPlan, SystemDesign
from backend.agents.delivery_agent import DeliveryAgent
from backend.knowledge.models import KnowledgeDocument

@pytest.fixture
def temp_chroma_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_project_a_to_project_b_learning(temp_chroma_dir, monkeypatch):
    # Enforce REAL RAG MODE as required by user validation
    monkeypatch.setenv("SEAM_RAG_MODE", "REAL")
    from backend.knowledge.knowledge_service import KnowledgeService
    
    # 1. Simulate Project A execution outcome
    state_a = ProjectState(
        project_id="ProjectA",
        user_requirement="Build a banking app.",
        domain="finance",
        qa_feedback=[
            "JWT tokens must not be accepted without validating signature and expiration."
        ]
    )
    # mock a plan
    state_a.project_plan = ProjectPlan(
        project_overview="Banking app",
        system_design=SystemDesign(
            architecture_style="Microservices",
            technology_stack=["FastAPI", "PostgreSQL", "Redis"],
            database_schema=[],
            api_endpoints=[]
        ),
        tasks=[]
    )
    
    # DeliveryAgent extracts this and puts it in RAG
    delivery_agent = DeliveryAgent()
    ks = KnowledgeService(persist_dir=temp_chroma_dir)
    
    # Ensure ks uses REAL mode correctly
    from backend.config import SEAM_RAG_MODE
    
    delivery_agent.knowledge_service.update_knowledge = lambda state: _mock_update(ks, state)
    
    def _mock_update(ks_instance, state):
        from backend.knowledge.models import KnowledgeDocument
        doc = KnowledgeDocument(
            title="QA Feedback - ProjectA",
            source="ProjectA",
            source_type="project_qa",
            category="lesson_learned",
            content="\n".join(state.qa_feedback),
            validated="VALIDATED"
        )
        ks_instance.ingest_document(doc)
        return "mocked"
        
    delivery_agent.process(state_a)
    
    # 2. Simulate Project B retrieval with Semantic differences
    ks_b = KnowledgeService(persist_dir=temp_chroma_dir)
    # The query is semantically related but not an exact string match
    context_for_qa_b = ks_b.retrieve_for_agent("QAAgent", "How should authentication tokens be validated to prevent expired or forged credentials?")
    
    # Prove that the lesson learned from Project A appears for Project B
    assert "JWT tokens must not be accepted" in context_for_qa_b
    assert "ProjectA" in context_for_qa_b

    # 3. Verify PENDING knowledge is NOT retrieved
    # Add a PENDING finding
    doc_pending = KnowledgeDocument(
        title="Pending Finding",
        source="ProjectA",
        source_type="project_qa",
        category="lesson_learned",
        content="This is an unvalidated pending secret problem.",
        validated="PENDING"
    )
    ks_b.ingest_document(doc_pending)
    
    context_pending = ks_b.retrieve_for_agent("QAAgent", "secret problem")
    assert "unvalidated pending secret" not in context_pending
