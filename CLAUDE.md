# CLAUDE.md — UidSkills
> Leia este arquivo SEMPRE antes de qualquer ação.
> Repositório: github.com/UidSoftware/UidSkills
> Última atualização: 2026-05-29

---

## O que é este repositório

Este é o repositório de **Skills e Agents** da Uid Software e Tecnologia LTDA.

Não é um sistema — é a **linha de produção** da fábrica de software.
Contém as skills que guiam cada agent no pipeline de desenvolvimento,
do lead ao deploy.

---

## Como o Claude Code usa este repositório

Ao abrir o Claude Code neste diretório, você tem acesso ao time
completo de agents da Uid. Cada skill é um especialista.

As skills também estão instaladas **globalmente** em `~/.claude/skills/`
— disponíveis em qualquer projeto sem precisar abrir este diretório.

**Nunca execute uma skill sem ler sua descrição primeiro.**
**Nunca pule etapas do pipeline — o Planner orquestra a ordem.**

---

## O Pipeline da Fábrica

```
LEAD NO BANCO (MCP PostgreSQL — vitrine_lead)
        ↓
   [PLANNER]          ← lê lead via MCP, qualifica, orquestra tudo
        ↓
   [ANALISTA]         ← elicita, modela, documenta (Sommerville)
        ↓
   [ARQUITETURA]      ← Luiz Eduardo preenche no SystemD
                         Office → Novo Projeto → Arquitetura Técnica
                         Salva em ordens_arquiteturatecnica (banco)
                         Planner lê via MCP e continua
        ↓
   [DOC-GENERATOR]    ← gera 8 documentos do projeto
        ↓
   [BLUEPRINT] + [BRUSH] ← técnica + visual (paralelo)
        ↓
   [FORGE] + [LOOM]   ← backend + frontend (paralelo)
        ↓
   [SENTINEL]         ← valida tudo — nada passa sem aprovação
        ↓
   [PILOT]            ← CI/CD, deploy na VPS, zero SSH manual
        ↓
SISTEMA EM PRODUÇÃO → MENSALIDADE NA CONTA 💰
```

---

## Estrutura do repositório

```
UidSkills/
├── CLAUDE.md                        ← este arquivo
└── .claude/
    └── skills/                      ← skills carregadas pelo Claude Code
        ├── PlannerSKILL.md          ← Lead Agent + Gerente de Projeto
        ├── AnalistaSKILL.md         ← Analista (Sommerville completo)
        ├── AnalistaUML.md           ← 7 diagramas UML em Mermaid
        ├── BrushSKILL.md            ← Designer UI/UX
        ├── BlueprintSKILL.md        ← Arquiteto de Software
        ├── ForgeSKILL.md            ← Dev Backend (Django + DRF)
        ├── LoomSKILL.md             ← Dev Frontend (React + Vite)
        ├── SentinelSKILL.md         ← QA / Testes
        ├── PilotSKILL.md            ← DevOps / Deploy
        └── doc-generator_SKILL.md   ← Gerador de 8 documentos
```

> Arquitetura Técnica → SystemD: uidsoftware.com.br/sistema → Office → Novo Projeto → Arquitetura Técnica
> Artigo Engenharia de Requisitos → conteúdo Uid (LinkedIn, blog)

---

## Os Agents — quem faz o quê

| Agent | Skill | Papel | Quando usar |
|---|---|---|---|
| Planner | PlannerSKILL.md | Lead Agent + Gerente | Sempre primeiro |
| Analista | AnalistaSKILL.md | Levantamento de requisitos | Após lead qualificado |
| Blueprint | BlueprintSKILL.md | Arquiteto | Após doc-generator |
| Brush | BrushSKILL.md | Designer UI/UX | Paralelo ao Blueprint |
| Forge | ForgeSKILL.md | Dev Backend | Após Blueprint |
| Loom | LoomSKILL.md | Dev Frontend | Paralelo ao Forge |
| Sentinel | SentinelSKILL.md | QA | Após Forge + Loom |
| Pilot | PilotSKILL.md | DevOps | Após Sentinel aprovar |
| doc-generator | doc-generator_SKILL.md | Gera 8 docs | Após Analista |

**Skills de suporte (usadas por outros agents):**
- AnalistaUML.md → consultar ao gerar qualquer diagrama UML

---

## Metodologia

```
Scrum  → relacionamento Uid ↔ cliente
         sprints quinzenais, backlog visível, review com cliente
         board no SystemD (menu Office)

Kanban → execução interna dos agents
         fluxo contínuo, sem cerimônia
         visualização no Claude Office (pixel art)
```

---

## Stack padrão Uid (todos os projetos)

```
Backend:  Python 3.12 + Django 5.x + DRF + SimpleJWT
Frontend: React 18 + Vite + Tailwind CSS + PWA
Banco:    PostgreSQL 16
Infra:    Docker Compose + Nginx + Gunicorn
CI/CD:    GitHub Actions (zero SSH manual)
VPS:      Ubuntu 24.04 — 209.50.241.122
```

Adaptar stack apenas se o cliente tiver tecnologia legada
ou requisito técnico específico documentado no ADR.

---

## Regras absolutas (todos os agents respeitam)

```
✅ Soft delete em todos os models — NUNCA objeto.delete()
✅ DecimalField para dinheiro — NUNCA Float
✅ Autenticação por email — NUNCA username
✅ response.data.results no frontend — NUNCA .data direto
✅ Migrations geradas no dev — NUNCA na VPS
✅ Credenciais no .env — NUNCA hardcode
✅ App 'os' proibido — usar 'ordens' com URL /api/os/
✅ LivroCaixa imutável — ReadCreateViewSet
✅ Signals com transaction.atomic() — SEMPRE
✅ CI/CD via GitHub Actions — NUNCA SSH manual no fluxo normal
✅ Testes passando antes de qualquer deploy
✅ Sentinel aprova antes do Pilot executar
✅ Brush define design system antes do Loom começar
✅ Fontes: Plus Jakarta Sans + DM Sans — NUNCA Inter/Roboto/Arial
✅ Overflow-hidden NUNCA no SistemaLayout root
```

---

## MCP — Acesso ao banco do SystemD

O Planner acessa o banco via MCP PostgreSQL configurado na VPS.

**Conexão:** `postgresql://uid_user:***@127.0.0.1:5433/uid_sistema`
**Verificar:** `claude mcp list` → `systemd: ... ✓ Connected`

**Queries principais do Planner:**
```sql
-- Novos leads aguardando qualificação
SELECT * FROM vitrine_lead WHERE convertido = false ORDER BY criado_em DESC;

-- Arquitetura Técnica salva no SystemD
SELECT * FROM ordens_arquiteturatecnica ORDER BY criado_em DESC LIMIT 1;

-- Criar OS após aprovação
INSERT INTO ordens_os (cliente_id, titulo, status) VALUES (...);

-- Marcar lead como convertido
UPDATE vitrine_lead SET convertido = true WHERE id = X;
```

**Permissões MCP** (em `/root/.claude/settings.json`):
`mcp__systemd__query`, `mcp__systemd__list_tables`, `mcp__systemd__describe_table`

---

## Infra VPS — portas ocupadas

| Projeto | Porta | Domínio |
|---|---|---|
| Studio Fluir | 8001 | nostudiofluir.com.br |
| SystemD | 8002 | uidsoftware.com.br |
| Mailcow HTTP | 8080 | mail.uidsoftware.com.br |
| Mailcow HTTPS | 8443 | mail.uidsoftware.com.br |
| UidMail | 8084 | uidmail.uidsoftware.com.br |
| **OfficeUid** | **8004** | office.uidsoftware.com.br |
| **Próximo cliente** | **8003+** | a definir |

> Sempre verificar porta disponível antes de definir no docker-compose.prod.yml

---

## Como testar o pipeline (projeto fictício)

Antes de rodar com cliente real, testar com lead fake:

```bash
# 1. Abrir Claude Code neste diretório
claude

# 2. Simular lead qualificado
"Tenho um lead: João da Silva, Salão de Beleza Corte & Estilo,
 Uberlândia/MG. Problema: controla tudo no papel e WhatsApp.
 Quer sistema para agendamentos, clientes e financeiro.
 Planner, avalie e inicie o pipeline."

# 3. Acompanhar a esteira rodar
# Planner → Analista → doc-generator → Blueprint + Brush → Forge + Loom → ...

# 4. Validar cada output antes de avançar
# 5. Identificar onde trava e ajustar a skill correspondente
```

---

## Contatos Uid Software

```
WhatsApp: (34) 99134-9194
Email:    contato@uidsoftware.com.br
Site:     www.uidsoftware.com.br
GitHub:   github.com/UidSoftware
VPS:      209.50.241.122 (usuário: notuidsoftware)
```

---


---

### [2026-06-04/05] — HotfixSKILL criada + pipeline Hotfix→Planner corrigido

#### Nova skill: `HotfixSKILL.md`

Skill criada para o agente Hotfix com:
- Papel exclusivo de **diagnóstico e handoff** — nunca implementa código
- Leitura do `CLAUDE.md` do projeto para carregar contexto
- Handoff imediato para o Planner via `Agent(subagent_type='planner')`
- Guardrail explícito contra auto-recursão: `❌ NUNCA chamar Agent(subagent_type='hotfix')`
- Bash PERMITIDO apenas para leitura: `git status`, `git log`, `docker ps`, `docker logs`
- Bash PROIBIDO para qualquer modificação: `git add`, `docker compose`, `npm`, `rm`

#### Correções nas skills existentes

**`BrushSKILL.md` — simplificada:**
- Removida seção de integração com motor `ui-ux-pro-max` (script Python `search.py`)
- Brush agora aplica o padrão Uid diretamente + referências visuais por segmento

**Pipeline corrigido — Hotfix→Planner (não Planner→Hotfix):**
```
Boss CLI
    ↓
Hotfix (lê CLAUDE.md do projeto, diagnóstico, handoff)
    ↓
Planner (classifica tarefas, monta briefings, orquestra)
    ↓
Forge + Loom (paralelo)
    ↓
Sentinel → Pilot
```

#### Uso do pipeline de manutenção validado em produção

Pipeline rodado com sucesso no **Studio Fluir** (2026-06-04/05):
- Boss CLI → Hotfix → Planner → Forge + Loom → Sentinel → Pilot
- Tarefa: dashboard profissional + análise UI/UX completa (P0→P3)
- 30 melhorias implementadas, 42 arquivos com emojis, build Docker sem erros
- CI/CD GitHub Actions passando (117 testes)

#### Status atual das skills

| Skill | Arquivo | Status |
|---|---|---|
| Planner | `planner.md` | ✅ Atualizado (pipeline único, edge cases) |
| Analista | `analista.md` | ✅ Estável |
| doc-generator | `doc-generator.md` | ✅ Estável |
| Blueprint | `blueprint.md` | ✅ Estável |
| Brush | `brush.md` | ✅ Simplificado (sem ui-ux-pro-max) |
| Forge | `forge.md` | ✅ Estável |
| Loom | `loom.md` | ✅ Estável |
| Sentinel | `sentinel.md` | ✅ Estável |
| Pilot | `pilot.md` | ✅ Estável |
| Hotfix | `hotfix.md` | ✅ Restrições explícitas adicionadas |
| HotfixSKILL | `HotfixSKILL.md` | ✅ Nova — criada neste ciclo |

#### Próximos passos

```
✅ HotfixSKILL.md criada
✅ Pipeline Hotfix→Planner corrigido e validado em produção
✅ BrushSKILL simplificada
⬜ AnalistaSKILL — integrar com MCP PostgreSQL do SystemD (lead real)
⬜ PlannerSKILL — integrar com MCP PostgreSQL do SystemD
⬜ Criar skill de n8n (notificações automáticas)
⬜ Testar pipeline completo com novo cliente (projeto fictício salão de beleza)
⬜ Criar templates de projeto por segmento (saúde, salão, agro, loja)
```

---

## Próximos passos do repositório

```
⬜ Testar pipeline completo com projeto fictício (salão de beleza)
⬜ Ajustar skills baseado nos travamentos encontrados
✅ Skills instaladas globalmente em ~/.claude/skills/ (29/05/2026)
⬜ Adicionar n8n ao pipeline (notificações WhatsApp + email)
⬜ Criar templates por segmento (saúde, salão, loja, agro...)
⬜ Versionamento das skills (tag por projeto executado com sucesso)
```

---

*Uid Software e Tecnologia LTDA — Uberlândia/MG*
*"Transformando ideias em soluções digitais com tecnologia, inovação e eficiência"*
*🚀 Lead entra. Fábrica roda. Mensalidade chega.*
