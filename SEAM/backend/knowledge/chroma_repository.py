import os
import chromadb
import hashlib
import re
from typing import List, Dict, Any, Optional
from backend.config import CHROMA_PERSIST_DIRECTORY
from backend.knowledge.models import KnowledgeChunk, KnowledgeSearchResult, PRODUCTION_KNOWLEDGE_STATUSES

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
        from chromadb.config import Settings
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        class DeterministicHashEmbeddingFunction:
            def __init__(self, dimensions: int = 384):
                self.dimensions = dimensions

            def __call__(self, input: List[str]) -> List[List[float]]:
                vectors = []
                for text in input:
                    vector = [0.0] * self.dimensions
                    tokens = re.findall(r"[a-zA-Z0-9_]+", (text or "").lower())
                    for token in tokens:
                        digest = hashlib.sha256(token.encode("utf-8")).digest()
                        index = int.from_bytes(digest[:4], "big") % self.dimensions
                        sign = 1.0 if digest[4] % 2 == 0 else -1.0
                        vector[index] += sign
                    norm = sum(value * value for value in vector) ** 0.5 or 1.0
                    vectors.append([value / norm for value in vector])
                return vectors

        class FastEmbedEmbeddingFunction:
            def __init__(self, model_name: str):
                from fastembed import TextEmbedding
                self.model = TextEmbedding(model_name=model_name)

            def __call__(self, input: List[str]) -> List[List[float]]:
                return [vector.tolist() if hasattr(vector, "tolist") else list(vector) for vector in self.model.embed(input)]

        self.embedding_backend = "fastembed"
        try:
            self.embedding_fn = FastEmbedEmbeddingFunction(SEAM_EMBEDDING_MODEL)
        except Exception as exc:
            self.embedding_backend = f"deterministic_fallback:{exc}"
            self.embedding_fn = DeterministicHashEmbeddingFunction()
            
        self.collection = self.client.get_or_create_collection(
            name="seam_knowledge"
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
            metadatas=metadatas,
            embeddings=self.embedding_fn(documents)
        )

    def count(self) -> int:
        if self.mode == "TEST":
            return len(self.chunks)
        return self.collection.count()

    def delete_missing_sources(self, valid_sources: List[str]):
        if self.mode == "TEST":
            self.chunks = [chunk for chunk in self.chunks if chunk.source in valid_sources]
            return
        existing = self.collection.get()
        ids = []
        for item_id, metadata in zip(existing.get("ids", []), existing.get("metadatas", [])):
            if metadata.get("source") not in valid_sources:
                ids.append(item_id)
        if ids:
            self.collection.delete(ids=ids)

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

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3,
        only_validated: bool = True,
        domain: Optional[str] = None,
        allowed_domains: Optional[List[str]] = None,
    ) -> List[KnowledgeSearchResult]:
        if self.mode == "TEST":
            results = []
            for c in self.chunks:
                # Need to match chunk format if c has .validated or if it's metadata
                val = c.metadata.get("status", c.metadata.get("validated", "PENDING")) if hasattr(c, "metadata") else getattr(c, "validated", "PENDING")
                if only_validated and val not in PRODUCTION_KNOWLEDGE_STATUSES:
                    continue
                if category and c.category != category:
                    continue
                chunk_domain = c.metadata.get("domain", "general")
                if domain and chunk_domain not in {domain, "general"}:
                    continue
                if allowed_domains and chunk_domain not in allowed_domains:
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
            where_clause["status"] = {"$in": sorted(PRODUCTION_KNOWLEDGE_STATUSES)}
            
        if category:
            where_clause["category"] = category

        if domain:
            allowed_domains = allowed_domains or [domain, "general"]
        if allowed_domains:
            where_clause["domain"] = {"$in": allowed_domains}
            
        # If where_clause has multiple conditions, Chroma requires $and
        final_where = None
        if len(where_clause) == 1:
            key, value = next(iter(where_clause.items()))
            final_where = {key: value}
        elif len(where_clause) > 1:
            final_where = {"$and": [{k: v} for k, v in where_clause.items()]}

        try:
            results = self.collection.query(
                query_embeddings=self.embedding_fn([query]),
                n_results=top_k,
                where=final_where
            )
            
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    doc = results["documents"][0][i]
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    # Distance is returned. Convert to a positive relevance score.
                    dist = results["distances"][0][i] if results["distances"] else 1.0
                    score = 1.0 / (1.0 + max(0.0, dist))
                    
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
