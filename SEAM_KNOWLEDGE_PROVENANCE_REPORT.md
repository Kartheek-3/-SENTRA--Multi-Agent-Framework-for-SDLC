# SEAM Knowledge Provenance Report

## 1. Knowledge Categories

Repository categories include:

- architecture
- coding
- database
- domain
- lesson_learned
- past_project
- repository
- reusable_code
- security
- testing

## 2. Source Types

Implemented source types:

- `AUTHORITATIVE`
- `OFFICIAL_TECHNICAL_DOCUMENTATION`
- `ACADEMIC`
- `VALIDATED_PROJECT_KNOWLEDGE`
- `SEAM_CURATED`
- `LESSON_LEARNED`

## 3. Number Of Documents Per Source Type

Actual parsed repository counts:

- `SEAM_CURATED`: 34
- `AUTHORITATIVE`: 4
- `OFFICIAL_TECHNICAL_DOCUMENTATION`: 6
- `ACADEMIC`: 2
- `VALIDATED_PROJECT_KNOWLEDGE`: 1
- `LESSON_LEARNED`: 1

Total documents: 48

Indexed ChromaDB chunks: 53

## 4. Validation Lifecycle

Supported lifecycle states:

- `PENDING`
- `REVIEWED`
- `VALIDATED`
- `ACTIVE`
- `REJECTED`
- `ARCHIVED`
- `SOURCE_UNAVAILABLE`

Production retrieval states:

- `VALIDATED`
- `ACTIVE`

## 5. Active Knowledge

Actual status counts:

- `ACTIVE`: 14
- `VALIDATED`: 34

## 6. Rejected Knowledge

Rejected documents currently in repository: 0

Invalid/fake authoritative URLs are rejected by validation and are not indexed.

## 7. Academic Sources

- Retrieval-Augmented Generation For Knowledge-Intensive NLP Tasks
  - Source type: `ACADEMIC`
  - Organization: arXiv
  - DOI: `10.48550/arXiv.2005.11401`
- SWE-agent Agent-Computer Interfaces Enable Automated Software Engineering
  - Source type: `ACADEMIC`
  - Organization: arXiv
  - DOI: `10.48550/arXiv.2405.15793`

## 8. Authoritative Sources

- OWASP Input Validation Guidance
  - Organization: OWASP
  - URL: `https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html`
- NIST Cybersecurity Framework 2.0
  - Organization: NIST
  - URL: `https://www.nist.gov/publications/nist-cybersecurity-framework-csf-20`
- WHO Recommendations On Digital Interventions For Health System Strengthening
  - Organization: World Health Organization
  - URL: `https://www.who.int/publications/i/item/9789241550505`
- RBI Cyber Security Framework For Banks
  - Organization: Reserve Bank of India
  - URL: `https://systemhealth.rbi.org.in/Scripts/Bs_viewcontent.aspx_Id%3D3864.html`

## 9. Official Technical Documentation

- Python 3 Documentation
- FastAPI Tutorial User Guide
- React Quick Start
- PostgreSQL Documentation
- AWS Well-Architected Framework
- Google Cloud Well-Architected Framework

## 10. SEAM-Curated Knowledge

SEAM-curated documents remain separate from official or authoritative documents. They are not labeled as official.

Examples:

- architecture patterns
- coding practices
- testing practices
- security practices
- domain seed guidance

## 11. Project-Derived Knowledge

- Expense Tracker PostgreSQL Selection Lesson
  - Source type: `VALIDATED_PROJECT_KNOWLEDGE`
  - Domain: finance
  - Validation result: QA passed with transactional requirements documented

## 12. Example Retrieved Sources

Healthcare retrieval can return:

- WHO digital health intervention guidance
- Healthcare appointment management SEAM-curated knowledge
- Healthcare security and audit SEAM-curated knowledge
- OWASP/NIST security guidance where semantically relevant

Finance retrieval can return:

- RBI cybersecurity framework knowledge
- finance transaction/auditability SEAM-curated knowledge
- validated expense tracker PostgreSQL lesson

## 13. Known Limitations

- The repository contains concise SEAM-authored summaries of official/academic sources, not full external documents.
- External source retrieval is not automated; no arbitrary web scraping was added.
- URL validation checks known official domains for configured organizations. It does not prove that every source remains current forever.
- The old historical backend test suite still has unrelated failures in mock-router and artifact-registration tests.

## 14. Validation Commands

```powershell
python -m compileall backend
npm.cmd run build
python -m pytest tests\test_knowledge_sources.py tests\test_domain_intelligence.py tests\test_rag_repository.py -q
python -c "from backend.knowledge.indexer import index_knowledge; import json; print(json.dumps(index_knowledge(), indent=2))"
python -c "from backend.knowledge.indexer import discover_documents, load_document; from collections import Counter; docs=[load_document(p) for p in discover_documents()]; print('docs', len(docs)); print('source_types', dict(Counter(d.source_type for d in docs))); print('statuses', dict(Counter(d.validated for d in docs)))"
```

## 15. Actual Validation Results

- Backend compile: PASS
- Frontend build: PASS
- Focused source/domain/RAG tests: `18 passed in 93.47s`
- Repository indexing: 48 discovered, 48 indexed, 53 chunks, 53 collection count
- Metadata counts: 48 documents
- FastEmbed remains the intended embedding backend. A standalone post-index count check hung during Chroma/FastEmbed startup, but indexing itself completed and reported the persisted collection count.
- Full backend suite: INCOMPLETE. `python -m pytest tests -q` was stopped after roughly three minutes with no final summary.
