# Security

- **Authentication** — Argon2 password hashes; short-lived JWT access tokens; refresh tokens stored hashed and revocable.
- **Authorization** — every document and conversation load filters by the current user id (foreign IDs look like not found).
- **Storage** — files under `{user_id}/{document_id}/…`; optional S3 backend.
- **API keys** — never shipped in the Angular bundle; the browser talks only to DocuAsk.
- **Uploads** — type/size validation; treat document text as untrusted input (prompt-injection aware prompts).
- **Logging** — avoid logging full document bodies in normal application logs.
- **Product messaging** — no-training-by-default: uploaded content is used to answer the user’s questions, not presented as public model training data by default.

Deferred for a later pass: signed download URLs, organization/workspace multi-tenancy, full audit-event UI.
