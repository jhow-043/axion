---
id: P11
slug: anexos-evidencias
status: approved
version: 1.0.0
owner: jhowworks
depends_on: [P01, P04, P09]
satisfies: [RF-110, RF-111, RF-112, RNF-SEG-010, RNF-INT-004]
adrs: [ADR-0001, ADR-0002]
branch: feature/011-anexos-evidencias
last_updated: 2026-06-01
---

# P11 — Anexos e Evidências (MinIO)

## Objetivo

Permitir que usuários anexem fotos e vídeos como evidências a chamados, usando MinIO como armazenamento de objetos on-premise (S3-compatível). O upload é feito diretamente do frontend para o MinIO via URL pré-assinada, sem trafegar o arquivo pelo backend.

## Escopo

- Geração de URL pré-assinada para upload (PUT) diretamente no MinIO.
- Confirmação de upload: o frontend notifica o backend após o upload bem-sucedido; o backend registra o anexo no banco.
- Listagem e download de anexos de um chamado.
- Exclusão de anexo (com remoção do objeto no MinIO).
- Validação de tipo MIME e tamanho máximo configurável.
- Evento de timeline ao anexar (integração com P10).
- Isolamento de objetos por tenant no bucket (prefixo `tenant_id/`).
- Componente de upload/galeria no frontend.

## Fora do Escopo

- Transcodificação ou compressão de vídeo.
- Visualização de vídeo em streaming avançado.
- Antivírus / varredura de malware (registrar como evolução).
- Assinatura de documentos.
- Integração com CDN externo.

## Dependências

- **P01** (Multi-Tenancy).
- **P04** (Usuários e Permissões).
- **P09** (Chamados) — anexos são vinculados a um chamado; participação é verificada.
- **P10** (Timeline) — `record_event("attachment_added")` chamado após confirmação.
- Infraestrutura MinIO provisionada (Docker Compose — parte do setup de deploy).

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `attachments` | Nova tabela |

### `attachments`
```
id              UUID, PK
tenant_id       UUID, FK → tenants, INDEX
ticket_id       UUID, FK → tickets, INDEX
uploaded_by     UUID, FK → users
filename        String, NOT NULL           # nome original do arquivo
storage_key     String, NOT NULL, UNIQUE   # chave no MinIO: {tenant_id}/{ticket_id}/{uuid}.ext
mime_type       String, NOT NULL
size_bytes      BigInt, NOT NULL
created_at      DateTime
```

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| POST | `/api/v1/tickets/{id}/attachments/upload-url` | Solicitar URL pré-assinada para upload | participante do chamado |
| POST | `/api/v1/tickets/{id}/attachments/confirm` | Confirmar upload e registrar anexo | participante do chamado |
| GET | `/api/v1/tickets/{id}/attachments` | Listar anexos do chamado | `ticket:read` + participante |
| GET | `/api/v1/attachments/{id}/download-url` | Obter URL pré-assinada para download (GET) | participante |
| DELETE | `/api/v1/attachments/{id}` | Excluir anexo | uploader ou admin |

### Body de `POST /upload-url`
```json
{
  "filename": "foto-motor.jpg",
  "mime_type": "image/jpeg",
  "size_bytes": 1048576
}
```
Response `200`:
```json
{
  "upload_url": "https://minio.host/bucket/...",
  "storage_key": "tenant-uuid/ticket-uuid/file-uuid.jpg",
  "expires_in": 300
}
```

### Body de `POST /confirm`
```json
{
  "storage_key": "tenant-uuid/ticket-uuid/file-uuid.jpg",
  "filename": "foto-motor.jpg",
  "mime_type": "image/jpeg",
  "size_bytes": 1048576
}
```

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Componente de Upload | Drag-and-drop ou seleção de arquivo; barra de progresso; validação de tipo/tamanho no cliente |
| Galeria de Anexos | Lista de anexos no detalhe do chamado com preview de imagem (thumbnail) e link para download de vídeos |

## Regras de Negócio

1. **Tipos MIME permitidos (configurável em `core/config.py`):** `image/jpeg`, `image/png`, `image/webp`, `video/mp4`, `video/quicktime`. Outros tipos devem ser rejeitados na validação do `upload-url` (antes de gerar a URL).
2. **Tamanho máximo:** imagens: 10 MB; vídeos: 200 MB (configurável). Validado no backend ao solicitar a URL e verificado no cliente antes do upload.
3. **Chave de armazenamento isolada por tenant:** `{tenant_id}/{ticket_id}/{uuid}.{ext}` — evita colisões entre tenants e chamados.
4. **URL pré-assinada expira em 5 minutos** (tempo suficiente para o upload). URL de download expira em 60 minutos.
5. **Confirmação obrigatória:** o anexo só é persistido no banco após a chamada de `/confirm`. Objetos no MinIO sem confirmação são descartados por job de limpeza periódico (marcados como "orphan" após 1h — registrar como evolução).
6. **Exclusão:** remove o registro no banco e o objeto no MinIO. Exclusão permitida apenas pelo uploader, responsável pelo chamado ou admin.
7. **Evento de timeline:** `attachment_added` registrado após confirmação bem-sucedida.
8. **Participação:** apenas participantes do chamado (solicitante, responsável, observadores) podem anexar e visualizar anexos.

## Critérios de Aceite

- [ ] `POST /upload-url` com tipo MIME inválido → 422.
- [ ] `POST /upload-url` com tamanho acima do limite → 422.
- [ ] URL pré-assinada gerada e válida para upload direto ao MinIO.
- [ ] `POST /confirm` registra o anexo no banco.
- [ ] `GET /attachments` lista anexos do chamado com metadados.
- [ ] `GET /attachments/{id}/download-url` retorna URL de download válida.
- [ ] `DELETE /attachments/{id}` remove do banco e do MinIO.
- [ ] Evento `attachment_added` registrado na timeline (P10).
- [ ] Chave de armazenamento contém o `tenant_id` como prefixo.
- [ ] Usuário não-participante → 403 ao acessar os endpoints.

## Estratégia de Testes

### Testes Unitários

- Validação de MIME e tamanho (antes da geração de URL).
- Geração de `storage_key` com prefixo correto de tenant.
- Verificação de participação no chamado.

### Testes de Integração

- `POST /upload-url` com MIME inválido → 422.
- `POST /upload-url` válido → URL gerada (MinIO de teste ou mock do SDK).
- `POST /confirm` → registro criado no banco + evento de timeline registrado.
- `DELETE /attachments/{id}` → registro removido do banco; verificar chamada ao MinIO SDK para remoção do objeto.
- Acesso de não-participante → 403.

### Testes E2E

- Usuário abre chamado → seleciona foto → upload completa → galeria exibe thumbnail.
- Usuário faz download do anexo → arquivo correto.
- Usuário exclui anexo → galeria atualizada; timeline exibe evento.

## Riscos Técnicos

- **Objetos órfãos no MinIO:** uploads iniciados mas não confirmados acumulam objetos sem registro no banco. Implementar job de limpeza periódica (evolução imediata pós-P11).
- **URL pré-assinada e CORS:** o MinIO deve estar configurado com CORS para aceitar uploads do domínio do frontend. Documentar no guia de deploy.
- **Verificação de tamanho real:** o backend valida o tamanho declarado pelo cliente, mas não o tamanho real do objeto no MinIO. Considerar hook pós-upload (MinIO event notification) ou verificação via `HEAD` após confirmação — registrar como evolução.
- **Lentidão de upload de vídeo:** sem barra de progresso, o usuário não tem feedback. O componente de frontend deve usar upload multipart com progresso.

## Complexidade

**Média** — a lógica de negócio é simples, mas o fluxo de URL pré-assinada e a integração com MinIO adicionam complexidade de infraestrutura.

## Prioridade

**Alta**

## Branch

`feature/011-anexos-evidencias`
