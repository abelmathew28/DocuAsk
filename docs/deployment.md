# Deployment

## Docker Compose (local / small VPS)

```bash
cp .env.example .env
# set JWT_SECRET. OPENAI_API_KEY is optional (local embeddings + extractive/Ollama answers work without it).
docker compose up --build
```

Frontend: http://localhost:8080  
API: http://localhost:8000/api/health

## AWS outline

1. Provision RDS PostgreSQL 16 and enable the `vector` extension.
2. Create an S3 bucket for PDFs. Set `STORAGE_BACKEND=s3`.
3. Build and push the backend image. Run it on ECS Fargate or App Runner with the production environment variables.
4. Build the Angular app (`npm run build`) and host `dist/frontend/browser` on S3 + CloudFront, or deploy the same static files to Netlify/Vercel.
5. Point `FRONTEND_URL` and `CORS_ORIGINS` at the public frontend origin.
6. Store secrets in AWS Secrets Manager or SSM. Do not bake keys into images.

## Netlify / Vercel frontend

Set the production API URL if the backend is on a different origin (update `environment.prod.ts` or inject at build time). Add a rewrite from `/api/*` to the FastAPI origin, or call the backend absolute URL and keep CORS locked to the frontend origin.

`frontend/nginx.conf` already proxies `/api/` when using the Compose frontend container.
