class Retriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        
    def retrieve_context(self, query: str, top_k: int = 3) -> list:
        # Placeholder for similarity search
        return self.vector_store.search(query, top_k)
