# Architecture

```
Angular 19  →  FastAPI (/api)  →  Document processing  →  Hybrid retrieval
                                                         →  Reranking
                                                         →  Answer generation
                                                         →  Citation verification
```

## Frontend

- Standalone Angular components under `frontend/src/app/features/`
- Authenticated shell with sidebar: Dashboard, Documents, Ask, Research, Compare, Extract, Settings
- Marketing: landing knowledge-network canvas, case study, architecture, security
- Ask workspace: three panels (scope/docs, conversation, evidence)

## Backend

- Routers in `backend/app/api/v1/` mounted at `API_V1_PREFIX` (default `/api`)
- Services for auth, documents, conversations, intelligence (research/compare/extract)
- AI package: embeddings, hybrid search, rerank, chat, citations, extractive fallback
- Storage: per-user local paths or S3-compatible backends

## Data isolation

Every document, chunk, conversation, and message query is scoped by `user_id`. JWT access tokens + hashed refresh tokens.

## Configuration

See `.env.example`. Provider abstraction allows swapping embedding and LLM backends without rewriting product code.
