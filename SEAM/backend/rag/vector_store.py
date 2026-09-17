from backend.config import CHROMA_PERSIST_DIRECTORY

class VectorStore:
    def __init__(self):
        self.persist_dir = CHROMA_PERSIST_DIRECTORY
        # Placeholder for ChromaDB initialization
        
    def add_documents(self, documents: list):
        pass
        
    def search(self, query: str, top_k: int = 3) -> list:
        # Placeholder
        return [f"Context regarding {query}"]
