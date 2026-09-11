# Case study — DocuAsk

## Problem

Handbooks, academic calendars, SOPs, and contracts already contain the answers people need — but PDF search is slow, and general chatbots invent details when the file is silent. Recruiters, registrars, and operators need a workspace that **grounds every claim in a source page**.

## Research and design goals

- Evidence first: citations with document, page, and excerpt
- Honest abstention when retrieval cannot support an answer
- Editorial UI suitable for university / HR / compliance contexts
- Modes with one job: Ask, Research, Compare, Extract

## Solution

DocuAsk uploads and indexes documents, retrieves with hybrid search, generates grounded answers (or extractive fallbacks), verifies claims, and opens the cited page in a viewer.

## Architecture and retrieval

See [architecture.md](architecture.md) and [rag-pipeline.md](rag-pipeline.md).

## Security decisions

See [security.md](security.md). User-level isolation is non-negotiable for a portfolio demo that mirrors production expectations.

## Challenges

- OpenAI rate limits → fail-fast + extractive provider for local demos
- Citation ranking for list-style answers (titles/dates) without hardcoding resume domains
- Keeping marketing density without clutter

## Testing and evaluation

Backend pytest covers auth isolation, ingestion basics, citation ranking, and no-answer behavior. Demo questions live in `demo-data/questions/`. **Do not invent portfolio metrics** — report only measured results (e.g. local extractive ask latency under one second after warmup).

## Future improvements

- First-class document versions and collections
- Signed URLs and richer audit history
- Calibrated confidence only if evaluation justifies it
- Optional `/api/v1` prefix cutover for public API clients
