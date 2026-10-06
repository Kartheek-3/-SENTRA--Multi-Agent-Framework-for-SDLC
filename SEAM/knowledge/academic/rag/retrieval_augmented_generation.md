---
title: Retrieval-Augmented Generation For Knowledge-Intensive NLP Tasks
category: architecture
domain: general
topic: retrieval_augmented_generation
source_type: ACADEMIC
organization: arXiv
url: https://doi.org/10.48550/arXiv.2005.11401
document_version: arXiv v4
publication_date: 2021-04-12
accessed_date: 2026-09-19
license:
status: ACTIVE
authors: Patrick Lewis; Ethan Perez; Aleksandra Piktus; Fabio Petroni; Vladimir Karpukhin; Naman Goyal; Heinrich Kuttler; Mike Lewis; Wen-tau Yih; Tim Rocktaschel; Sebastian Riedel; Douwe Kiela
publication: NeurIPS 2020
year: 2020
doi: 10.48550/arXiv.2005.11401
created_at: 2026-09-19
updated_at: 2026-09-19
---

# Retrieval-Augmented Generation

Engineering use:
- RAG combines model generation with retrieved external knowledge.
- Retrieval helps provenance and updateability when compared with relying only on model parameters.
- Retrieved knowledge quality, chunking, metadata, and ranking affect final usefulness.

SEAM application:
- SEAM should preserve source metadata with every retrieved chunk.
- Agents should receive retrieved content and provenance together.
- Academic RAG evidence should guide architecture choices, not be treated as universal product requirements.
