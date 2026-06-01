---
id: P00
slug: fundacao-plataforma
status: done
version: 1.0.0
owner: jhowworks
depends_on: []
satisfies: [RF-001, RF-002, RF-003, RF-004, RNF-OBS-001, RNF-OBS-002, RNF-OBS-003, RNF-MANUT-001, RNF-MANUT-002, RNF-DADOS-002]
adrs: []
branch: feature/000-fundacao-plataforma
last_updated: 2026-06-01
---

# P00 — Fundação da Plataforma (Backend)

## Objetivo

Estabelecer o esqueleto do projeto backend e as convenções técnicas comuns que todos os módulos irão reutilizar. É o ponto de partida de todo o sistema; nenhum outro plano pode começar sem este concluído.

## Escopo

- Estrutura de diretórios do projeto backend conforme convenção definida em `docs/README.md`.
- Aplicação FastAPI base com ciclo de vida (`lifespan`), CORS configurável e middleware de logging.
- Módulo `core/config.py`: carregamento de variáveis de ambiente via `pydantic-settings` (sem hardcode de segredos).
- Módulo `core/exceptions.py`: hierarquia de exceções da aplicação + handler global que retorna envelope de erro padronizado.
- Envelope de resposta de erro padrão (JSON com campos `error`, `message`, `detail`, `timestamp`).
- Módulo `core/pagination.py`: esquema de paginação (cursor ou offset) reutilizável por todos os routers.
- Módulo `core/deps.py`: dependências FastAPI comuns (sessão de banco, paginação).
- Módulo `db/`: engine async (`AsyncEngine`), sessão (`AsyncSession`), base declarativa (`DeclarativeBase`).
- Healthcheck: `GET /health` e `GET /api/v1/ping`.
- Setup de testes: `pytest` + `pytest-asyncio` + banco de teste (SQLite in-memory ou PostgreSQL de teste), fixtures de sessão, cliente de teste (`httpx.AsyncClient`).
- Configuração de lint/format: `ruff` + `black` (ou `ruff format`).
- `pyproject.toml` com dependências e scripts.
- Estrutura vazia dos módulos (`modules/auth/`, `modules/users/`, …) com `__init__.py`.

## Fora do Escopo

- Qualquer regra de negócio de domínio.
- Autenticação e autorização (P03, P04).
- Multi-tenancy (P01).
- Frontend (P02).

## Dependências

Nenhuma (ponto de partida do projeto).

## Entidades Impactadas

Nenhuma entidade de domínio. Apenas infraestrutura técnica.

## APIs Necessárias

| Método | Rota | Descrição | Autenticação |
|--------|------|-----------|-------------|
| GET | `/health` | Status da aplicação e do banco | Pública |
| GET | `/api/v1/ping` | Verificação mínima de disponibilidade | Pública |

Resposta de `/health`:
```json
{
  "status": "ok",
  "database": "ok",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

Envelope de erro padrão (toda exceção tratada):
```json
{
  "error": "NOT_FOUND",
  "message": "Recurso não encontrado.",
  "detail": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Telas Necessárias

Nenhuma (fundação de backend).

## Regras de Negócio

- Nenhuma regra de domínio.
- **Convenção de resposta de erro:** toda exceção capturada pelo handler global deve retornar o envelope padronizado; exceções não tratadas retornam HTTP 500 com mensagem genérica (sem expor stack trace em produção).
- **Convenção de paginação:** parâmetros `page` (int, ≥1, padrão 1) e `page_size` (int, 1–100, padrão 20). Resposta inclui `total`, `page`, `page_size`, `items`.
- **Configuração por ambiente:** toda variável sensível (credenciais de banco, chaves JWT, SMTP) deve vir de variável de ambiente, nunca de valor padrão fixo.

## Critérios de Aceite

- [ ] `GET /health` retorna `200 OK` com status do banco quando o serviço sobe.
- [ ] `GET /api/v1/ping` retorna `200 OK` com `{"pong": true}`.
- [ ] Rota inexistente retorna `404` com o envelope de erro padrão.
- [ ] Exceção não tratada retorna `500` com mensagem genérica (sem stack trace).
- [ ] Paginação funciona via parâmetros `page` e `page_size` com validação de limites.
- [ ] `pytest` roda e passa com fixtures de sessão e cliente HTTP.
- [ ] `ruff check .` e `ruff format --check .` (ou equivalente) passam sem erros.
- [ ] Estrutura de módulos vazia criada conforme convenção.

## Estratégia de Testes

### Testes Unitários

- Utilitários de paginação: cálculo de offset, validação de limites.
- Envelope de erro: serialização correta para cada tipo de exceção.
- Carregamento de config: campos obrigatórios ausentes levantam erro claro na inicialização.

### Testes de Integração

- `GET /health` → banco conectado → status "ok".
- `GET /health` → banco indisponível → retorna status de degradação.
- `GET /api/v1/ping` → `200 {"pong": true}`.
- Rota inexistente → `404` com envelope padronizado.
- Sessão de banco: abrir, operar e fechar dentro de uma requisição (fixture de rollback por teste).

### Testes E2E

Não aplicável neste plano (sem interface de usuário ou fluxo de negócio).

## Riscos Técnicos

- **Configuração async do SQLAlchemy 2.0:** sessão async requer cuidados com `expire_on_commit=False` e propagação de contexto; erros aqui afetam todos os módulos.
- **Padronização do envelope de erro:** uma inconsistência na fundação propaga para todos os módulos — definir e testar antes de qualquer outra rota.
- **Compatibilidade do engine async em testes:** SQLite async tem limitações; preferir PostgreSQL de teste (docker-compose para CI).

## Complexidade

**Média** — sem regra de negócio, mas requer decisões técnicas que afetam toda a base de código.

## Prioridade

**Crítica** — bloqueador de todos os outros planos.

## Branch

`feature/000-fundacao-plataforma`
