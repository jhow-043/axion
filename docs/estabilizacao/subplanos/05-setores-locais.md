# Subplano 05 — Setores e Locais

**Specs:** P06 (Setores e Locais Prediais)
**Prioridade:** Alto — pré-requisito para equipamentos e chamados
**Status diagnóstico:** ⏳ Pendente

---

## Escopo da spec

- CRUD setores (unidades organizacionais): criar, listar, editar, desativar/reativar
- CRUD locais (alvos de chamados prediais): criar, listar, editar, desativar/reativar
- Nome único por tenant por entidade
- Inativo não aparece em dropdowns de criação
- Aviso ao desativar se estiver em uso (sem bloquear)

---

## Arquivos relevantes

### Backend
- `backend/app/modules/locations/router.py`
- `backend/app/modules/locations/service.py`
- `backend/app/modules/locations/repository.py`
- `backend/app/modules/locations/models.py` (Sector, Location)
- `backend/app/modules/locations/schemas.py`

### Frontend
- `frontend/src/features/locations/components/SetoresLocaisPage.tsx`
- `frontend/src/features/locations/components/SectorList.tsx`
- `frontend/src/features/locations/components/SectorForm.tsx`
- `frontend/src/features/locations/components/LocationList.tsx`
- `frontend/src/features/locations/components/LocationForm.tsx`
- `frontend/src/features/locations/api.ts`
- Rota: `/setores`, `/locais`

---

## Fluxos a validar

### Setores
- [ ] Listar setores: exibe todos do tenant atual
- [ ] Criar setor: nome → aparece na lista
- [ ] Editar setor: alteração persistida
- [ ] Desativar setor: não aparece em dropdowns de criação de equipamentos/chamados
- [ ] Reativar setor: volta a aparecer nos dropdowns
- [ ] Nome duplicado no mesmo tenant → erro adequado
- [ ] Setor de outro tenant não visível

### Locais
- [ ] Listar locais: exibe todos do tenant atual
- [ ] Criar local: nome → aparece na lista
- [ ] Editar local: alteração persistida
- [ ] Desativar local: não aparece em dropdowns de criação de chamados prediais
- [ ] Reativar local: volta a aparecer
- [ ] Nome duplicado → erro adequado

### Uso em módulos dependentes
- [ ] Setor aparece no formulário de criação de equipamento (select)
- [ ] Local aparece no formulário de criação de chamado predial (select)

---

## Problemas catalogados (Fase A)

| EST-ID | Classificação | Descrição | Arquivo:Linha | Reprodução |
|--------|--------------|-----------|---------------|------------|
| — | — | *A preencher* | — | — |
