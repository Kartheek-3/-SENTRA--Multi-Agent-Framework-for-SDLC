---
category: domain
topic: ai_ml_applications
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# AI and ML Applications

Description: Guidance for applications that use models, prompts, embeddings, or retrieval.

Principles:
- Separate model calls from deterministic business logic.
- Persist inputs, outputs, model names, and validation status where appropriate.
- Use retrieval to provide context; do not retrain models for ordinary knowledge updates.

Recommended practices:
- Add timeouts and retries for model calls.
- Validate structured model output.
- Avoid exposing hidden chain-of-thought.

Common mistakes:
- Treating model output as trusted without validation.
- Sending excessive context to every call.
- Storing sensitive prompts or secrets in reusable knowledge.

Applicable project types: agentic IDEs, RAG apps, assistants, workflow automation.

Relevant technologies: Ollama, ChromaDB, embeddings, FastAPI.
