# DocuAsk

**Ask your documents. Verify every answer.**

DocuAsk is a source-controlled document intelligence platform — not a general-purpose chatbot. Upload PDFs, Word, or text; ask in plain language; get answers grounded only in your files, with page citations and highlighted excerpts.

Built as a portfolio-quality full-stack product: Angular 19 frontend, FastAPI RAG backend, hybrid retrieval, citation verification, Research / Compare / Extract modes, and user-level document isolation.

## Quick start

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env  # or ensure project-root .env exists
mkdir -p storage/uploads
PYTHONPATH=. .venv/bin/python -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npx ng serve --host localhost --port 4200
```

Open [http://localhost:4200](http://localhost:4200). Demo login: `demo@docuask.app` / value of `DEMO_PASSWORD` in `.env`.

Public demo: [http://localhost:4200/demo](http://localhost:4200/demo) (seeds sample HE + handbook documents when the API is up; offline seeded Q&A if not).

## Product modes

| Mode | Route | Behavior |
|------|-------|----------|
| Ask | `/app/ask` | Concise grounded answers + citations |
| Research | `/app/research` | Cross-document synthesis |
| Compare | `/app/compare` | Diff-style comparison of two files |
| Extract | `/app/extract` | Structured field extraction |

Also: `/`, `/architecture`, `/case-study`, `/security`, `/app/documents`, `/app/settings`.

## Local AI defaults

For fast local demos without OpenAI quota issues:

```
LLM_PROVIDER=extractive
EMBEDDING_PROVIDER=local
```

Set `LLM_PROVIDER=auto` when a working OpenAI key is available. API modules live under `backend/app/api/v1/` and are mounted at `/api` (`API_V1_PREFIX`).

## Docs

- [Architecture](docs/architecture.md)
- [RAG pipeline](docs/rag-pipeline.md)
- [Security](docs/security.md)
- [Case study](docs/case-study.md)
- [API notes](docs/api.md)

## Demo data

Fictional higher-education samples (no confidential data):

- `demo-data/documents/` — academic calendar + student handbook excerpt
- `demo-data/questions/he-questions.json` — evaluation questions

## Tests

```bash
cd backend && PYTHONPATH=. .venv/bin/pytest -q
cd frontend && npx ng build
```

## Positioning

DocuAsk does **not** claim a better general model than ChatGPT or Claude. It is a better **document workflow, verification, and evidence** system for organizations that need searchable, citable answers from trusted files.
