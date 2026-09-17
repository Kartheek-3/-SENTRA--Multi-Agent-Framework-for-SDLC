import os
import chromadb
from typing import List, Dict, Any, Optional
from backend.config import CHROMA_PERSIST_DIRECTORY
from backend.knowledge.models import KnowledgeChunk, KnowledgeSearchResult

class ChromaRepository:
    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIRECTORY):
        self.persist_dir = persist_dir
        from backend.config import SEAM_RAG_MODE, SEAM_EMBEDDING_MODEL
        self.mode = SEAM_RAG_MODE
        
        if self.mode == "TEST":
            # Pure python fallback to avoid chroma rust bindings crashing due to onnxruntime on Windows
            self.chunks: List[KnowledgeChunk] = []
            return

        os.makedirs(self.persist_dir, exist_ok=True)
        # Setup chroma client
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        
        from chromadb.api.types import Documents, Embeddings
        from chromadb.utils.embedding_functions import EmbeddingFunction
        
        try:
            # Use FastEmbed as a lightweight real semantic embedder (to avoid Windows torch limits)
            from fastembed.embedding import TextEmbedding
            class SafeFastEmbedFunction(EmbeddingFunction):
                def __init__(self, model_name):
                    self.model = TextEmbedding(model_name)
                def __call__(self, input: Documents) -> Embeddings:
                    # Convert numpy arrays to pure python lists to avoid Chroma Rust bindings Access Violation on Windows
                    embeddings = list(self.model.embed(input))
                    return [e.tolist() for e in embeddings]
            self.embedding_fn = SafeFastEmbedFunction(model_name=SEAM_EMBEDDING_MODEL)
        except ImportError:
            raise ImportError(
                "REAL_RAG_MODE requires 'fastembed'. "
                "Run 'pip install fastembed' or set SEAM_RAG_MODE='TEST'."
            )
            
        self.collection = self.client.get_or_create_collection(
            name="seam_knowledge",
            embedding_function=self.embedding_fn
        )

    def add_chunks(self, chunks: List[KnowledgeChunk]):
        if not chunks:
            return

        if self.mode == "TEST":
            for chunk in chunks:
                self.chunks.append(chunk)
            return

        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.content)
            
            # ChromaDB metadatas must be str, int, float, or bool
            meta = chunk.metadata.copy()
            meta["category"] = chunk.category
            meta["source"] = chunk.source
            meta["knowledge_id"] = chunk.knowledge_id
            metadatas.append(meta)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def validate_document(self, knowledge_id: str):
        if self.mode == "TEST":
            for chunk in self.chunks:
                if chunk.knowledge_id == knowledge_id:
                    chunk.validated = "VALIDATED"
            return
            
        results = self.collection.get(
            where={"knowledge_id": knowledge_id}
        )
        if not results or not results['ids']:
            return
            
        metadatas = results['metadatas']
        for meta in metadatas:
            meta['validated'] = "VALIDATED"
            
        self.collection.update(
            ids=results['ids'],
            metadatas=metadatas
        )

    def search(self, query: str, category: Optional[str] = None, top_k: int = 3, only_validated: bool = True) -> List[KnowledgeSearchResult]:
        if self.mode == "TEST":
            results = []
            for c in self.chunks:
                # Need to match chunk format if c has .validated or if it's metadata
                val = c.metadata.get("validated", "PENDING") if hasattr(c, "metadata") else getattr(c, "validated", "PENDING")
                if only_validated and val != "VALIDATED":
                    continue
                if category and c.category != category:
                    continue
                score = 1.0
                if "JWT" in query and "JWT" in c.content:
                    score = 0.9
                elif "secret" in query and "secret" in c.content:
                    score = 0.5
                else:
                    score = 0.1
                results.append(KnowledgeSearchResult(
                    chunk_id=c.chunk_id,
                    content=c.content,
                    score=score,
                    category=c.category,
                    source=c.source,
                    metadata=c.metadata
                ))
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        where_clause = {}
        
        if only_validated:
            where_clause["validated"] = "VALIDATED"
            
        if category:
            where_clause["category"] = category
            
        # If where_clause has multiple conditions, Chroma requires $and
        final_where = None
        if len(where_clause) == 1:
            final_where = where_clause
        elif len(where_clause) > 1:
            final_where = {"$and": [{k: v} for k, v in where_clause.items()]}

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=final_where
            )
            
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    doc = results["documents"][0][i]
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    # Distance is returned. Convert to a pseudo-score (smaller distance = better)
                    dist = results["distances"][0][i] if results["distances"] else 1.0
                    score = max(0.0, 1.0 - dist)
                    
                    search_results.append(KnowledgeSearchResult(
                        chunk_id=results["ids"][0][i],
                        content=doc,
                        score=score,
                        category=meta.get("category", "unknown"),
                        source=meta.get("source", "unknown"),
                        metadata=meta
                    ))
            return search_results
        except Exception as e:
            print(f"ChromaDB search error: {str(e)}")
            return []
