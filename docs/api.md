# API

Base URL: `/api`

Auth header: `Authorization: Bearer <access_token>`

## Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`
- `POST /auth/change-password`

## Documents

- `GET /documents`
- `POST /documents` (multipart `file`)
- `GET /documents/{id}`
- `PATCH /documents/{id}`
- `DELETE /documents/{id}`
- `GET /documents/{id}/status`
- `GET /documents/{id}/file`

## Conversations

- `GET /conversations`
- `POST /conversations`
- `GET /conversations/{id}`
- `PATCH /conversations/{id}`
- `DELETE /conversations/{id}`
- `POST /conversations/{id}/messages`
- `POST /conversations/{id}/regenerate`

Chat responses include:

```json
{
  "answer": "...",
  "sources": [
    { "document": "handbook.pdf", "page": 14, "excerpt": "..." }
  ]
}
```

## Users

- `GET /users/me`
- `PATCH /users/me`
- `DELETE /users/me`
- `GET /users/me/stats`
- `GET /analytics/summary`
- `DELETE /users/me/conversations`
