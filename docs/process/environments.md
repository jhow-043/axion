# Ambientes e Deploy

## Ambientes

| Ambiente | Branch | URL | Propósito |
|----------|--------|-----|-----------|
| **Desenvolvimento** | qualquer `feature/*` | `localhost` | Dev local com hot reload |
| **Homologação** | `develop` | `homolog.cliente.local` | Testes de integração e aceite |
| **Produção** | `main` | `app.cliente.local` | Ambiente real do cliente |

---

## Desenvolvimento local

### Subir o ambiente completo

```bash
docker compose up -d            # PostgreSQL, Redis, MinIO, Mailhog

# Backend
cd backend
uv sync
alembic upgrade head            # aplica migrations
uvicorn app.main:app --reload   # porta 8000

# Frontend
cd frontend
pnpm install
pnpm dev                        # porta 3000
```

### Variáveis de ambiente (`.env`)

Copie `.env.example` para `.env` e preencha:

```bash
cp .env.example .env
```

Variáveis obrigatórias:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/manutencao_dev
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<gerar com: openssl rand -hex 32>
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=manutencao-dev
SMTP_HOST=localhost
SMTP_PORT=1025
```

### Mailhog (captura de e-mails em dev)

Acesse `http://localhost:8025` para ver todos os e-mails enviados.
Nenhum e-mail real é enviado em desenvolvimento.

---

## Homologação

### Deploy automático

Toda merge para `develop` dispara o pipeline de CI/CD que:
1. Roda testes e lint.
2. Faz build da imagem Docker.
3. Executa `alembic upgrade head` no banco de homologação.
4. Sobe a nova versão com zero downtime (rolling update).

### Smoke tests pós-deploy

Após cada deploy em homologação:
- [ ] `GET /health` retorna `200 OK` com `database: "ok"`
- [ ] `GET /api/v1/ping` retorna `{"pong": true}`
- [ ] Login com usuário de teste funciona
- [ ] Listagem de chamados retorna dados do tenant de teste

---

## Produção

### Promoção `develop → main`

1. Verificar que todos os smoke tests de homologação passaram.
2. Criar tag de release: `git tag v1.2.0 && git push --tags`.
3. Merge commit de `develop → main` (preserva o conjunto da release).
4. Pipeline de produção executa automaticamente.

### Migrations em produção

Toda migration deve ter `downgrade()` implementado.
Antes de fazer deploy com migration:
1. Verificar que a migration é retrocompatível com o código atual (schema additive).
2. Testar o `downgrade` em homologação.
3. Documentar no PR a instrução de rollback de schema.

```bash
# Rollback de migration
alembic downgrade -1
```

### Rollback de código

```bash
# Reverter commit de merge
git revert <merge-commit-hash>
git push origin main

# Redeploy da última tag estável
git checkout v1.1.0
docker compose up -d --build
```

---

## Docker Compose de produção

```yaml
# docker-compose.prod.yml
services:
  api:
    image: ${IMAGE_REGISTRY}/manutencao-api:${IMAGE_TAG}
    restart: always
    env_file: .env.prod
    depends_on: [postgres, redis]

  frontend:
    image: ${IMAGE_REGISTRY}/manutencao-frontend:${IMAGE_TAG}
    restart: always

  worker:
    image: ${IMAGE_REGISTRY}/manutencao-api:${IMAGE_TAG}
    command: celery -A app.worker worker --loglevel=info
    restart: always
    env_file: .env.prod
    depends_on: [redis, postgres]

  beat:
    image: ${IMAGE_REGISTRY}/manutencao-api:${IMAGE_TAG}
    command: celery -A app.worker beat --loglevel=info
    restart: always
    env_file: .env.prod

  postgres:
    image: postgres:16
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    env_file: .env.prod

  redis:
    image: redis:7
    restart: always
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio
    restart: always
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    env_file: .env.prod

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/ssl/certs:ro
```

---

## Backup

### PostgreSQL

```bash
# Backup diário (crontab)
0 2 * * * pg_dump -U postgres manutencao_prod | gzip > /backups/db_$(date +%Y%m%d).sql.gz

# Retenção: 30 dias locais + envio para armazenamento externo configurado pelo cliente
```

### MinIO

```bash
# Sync para backup externo
mc mirror minio/manutencao-prod /backups/minio/
```

---

## Variáveis de ambiente por ambiente

| Variável | Dev | Homologação | Produção |
|----------|-----|------------|----------|
| `DATABASE_URL` | localhost | servidor-homolog | servidor-prod |
| `SECRET_KEY` | qualquer | gerada | rotacionada periodicamente |
| `SMTP_HOST` | Mailhog | SMTP real (relay) | SMTP real |
| `MINIO_ENDPOINT` | localhost:9000 | homolog-minio | prod-minio |
| `CORS_ORIGINS` | `*` | domínio específico | domínio específico |
| `DEBUG` | `true` | `false` | `false` |
