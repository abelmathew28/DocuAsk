# RAG pipeline

1. **Upload** — validate type/size; store under the user id.
2. **Extract** — PDF (PyMuPDF / pypdf), DOCX, TXT; OCR fallback for scanned PDFs when RapidOCR is installed.
3. **Structure** — preserve headings/sections where available; clean repeated headers when possible.
4. **Chunk** — semantic/section-aware chunking with page and metadata.
5. **Embed** — local BGE (or hash in tests) or OpenAI embeddings.
6. **Index** — vectors + metadata in SQLite or Postgres/pgvector.
7. **Query** — optional rewrite/expand; hybrid keyword + vector retrieval (RRF).
8. **Rerank** — lexical or cross-encoder (`RERANKER`).
9. **Answer** — LLM when configured; **extractive** grounded fallback otherwise.
10. **Verify** — claim support against retrieved passages; abstain if insufficient.
11. **Cite** — return document name, page, excerpt; UI opens the source.
12. **Support status** — `supported` | `partially_supported` | `not_found` (no uncalibrated confidence %).

Abstention copy:

> I could not find enough information in the selected documents to answer this.
