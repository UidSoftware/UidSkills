# CLAUDE.md — UidSkills
> Leia este arquivo SEMPRE antes de qualquer ação.
> Repositório: github.com/UidSoftware/UidSkills
> Última atualização: 2026-06-30

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

## Dois pipelines — como a fábrica funciona

### Pipeline Novo Sistema (lead → produção)

```
TEXTO DO LEAD/VENDEDOR (banco SystemD via MCP)
        ↓
   [ANALISTA] modo novo_sistema / lead_vendedor
   ← parser universal: extrai RF/RNF do texto de não-dev
   ← input vago? notifica Luiz Eduardo via banco SystemD
        ↓
   [PLANNER] — triagem
   ← decide qual pipeline executar baseado no tipo do Analista
        ↓
   [ARQUITETURA]      ← Luiz Eduardo preenche no SystemD
                         Office → Novo Projeto → Arquitetura Técnica
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

### Pipeline Manutenção — dois fluxos

```
FLUXO 1 — Boss CLI (manual, urgente)
  Luiz Eduardo clica no sprite do boss no Claw Empire
        ↓
   [HOTFIX]  ← lê CLAUDE.md do projeto, delega ao Planner
        ↓
   [PLANNER] → Forge + Loom (paralelo) → Sentinel → Pilot

FLUXO 2 — Form do cliente (automático, assíncrono)
  Cliente não-dev preenche form de manutenção no próprio sistema
        ↓
   [ANALISTA] modo manutencao
   ← classifica: bug | melhoria_ux | feature_pequena | feature_grande | adicional_contrato
   ← input vago? envia email via Mailcow pedindo clareza
        ↓
   [PLANNER] — triagem por tipo:
   ├── bug / melhoria_ux    → Pipeline B: Forge+Loom direto → Sentinel → Pilot
   ├── feature_pequena      → Pipeline C: Blueprint lite → Forge+Loom → Sentinel → Pilot
   └── feature_grande /
       adicional_contrato   → Pipeline D: PARAR, notificar Luiz Eduardo (aprovação comercial)
```

---

## Estrutura do repositório

```
UidSkills/
├── CLAUDE.md                        ← este arquivo
├── automation/                      ← scripts de automação do host VPS
│   ├── disparar_planner.py          ← cron 4h — detecta lead pronto e cria task Planner
│   ├── disparar_hotfix.py           ← cron 4h — detecta manutenção pendente e cria task Hotfix
│   ├── retomar_agente.py            ← cron 30min — retoma tasks paradas por token limit
│   └── sync_skills.py               ← cron 15min — git pull → sincroniza skills no Empire
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
| Analista | AnalistaSKILL.md | Parser universal de intenção humana | Toda entrada (lead, form, vendedor) |
| Planner | PlannerSKILL.md | Roteador central + Gerente | Após Analista classificar |
| Hotfix | HotfixSKILL.md | Entry point manual urgente (Boss CLI) | Bug crítico via Claw Empire |
| Blueprint | BlueprintSKILL.md | Arquiteto | Após doc-generator (novo sistema) |
| Brush | BrushSKILL.md | Designer UI/UX | Paralelo ao Blueprint |
| Forge | ForgeSKILL.md | Dev Backend | Após Blueprint (ou direto no Pipeline B/C) |
| Loom | LoomSKILL.md | Dev Frontend | Paralelo ao Forge |
| Sentinel | SentinelSKILL.md | QA | Após Forge + Loom |
| Pilot | PilotSKILL.md | DevOps | Após Sentinel aprovar |
| doc-generator | doc-generator_SKILL.md | Gera 8 docs | Novo sistema, após Analista |

**Skills de suporte:**
- AnalistaUML.md → consultar ao gerar qualquer diagrama UML em Mermaid

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

## Automação da Fábrica

Os scripts em `automation/` rodam no host da VPS (`/opt/uid-automation/`) via cron.
São versionados aqui para que qualquer clone do repositório tenha a infraestrutura completa.

| Script | Cron | Função |
|---|---|---|
| `disparar_planner.py` | `0 */4 * * *` | Detecta `PRONTO_PARA_PLANNER` no SystemD e cria task para o Planner no Empire |
| `disparar_hotfix.py` | `0 */4 * * *` | Detecta manutenções `pendente` no SystemD e cria task para o Hotfix |
| `retomar_agente.py` | `*/30 * * * *` | Detecta tasks `in_progress` paradas há 25 min e cria retomada (máx. 5 por cadeia) |
| `sync_skills.py` | `*/15 * * * *` | `git pull` neste repo e copia skills alteradas para `/app/data/custom-skills/` no Empire |
| `generate_agents.py` | manual / pós-merge | `git pull` + gera/atualiza `/root/.claude/agents/*.md` a partir das skills |

**Fluxo do sync_skills:**
1. `git pull origin main` em `/opt/uid-skills`
2. Para cada `*.md` em `.claude/skills/`: deriva canonical name via frontmatter `name:`
3. Se o conteúdo mudou: `docker cp` para o container + atualiza `meta.json`
4. Qualquer `git push` neste repo propaga para o Empire em até 15 minutos

**Fluxo do generate_agents:**
1. `git pull origin main` em `/opt/uid-skills`
2. Para cada `*.md` em `.claude/skills/`: extrai `name:` do frontmatter
3. Cria/atualiza `/root/.claude/agents/{name}.md` com o conteúdo da skill
4. Skills sem frontmatter `name:` são ignoradas (corrigir o frontmatter da skill)

```bash
# Forçar sincronização imediata (sem esperar cron)
FORCE=1 python3 /opt/uid-automation/sync_skills.py

# Regenerar todos os agents globais (rodar após adicionar nova skill)
python3 /opt/uid-automation/generate_agents.py

# Logs
tail -f /opt/uid-automation/sync_skills.log
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
| HotfixSKILL | `HotfixSKILL.md` | ✅ Atualizada 2026-06-18 — Agent tool removido do fallback |

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

### [2026-06-22/23] — Pasta automation/ + fix SentinelSKILL TaskCreate

**`automation/` adicionada ao repositório (commit `cf3230f`):**
- `disparar_planner.py`, `disparar_hotfix.py`, `retomar_agente.py`, `sync_skills.py`
- Scripts antes existiam apenas em `/opt/uid-automation/` na VPS (sem versionamento)

**`sync_skills.py` criado:**
- Automatiza a sincronização `UidSkills (GitHub) → Empire custom-skills`
- Cron 15min: `git pull` + `docker cp` das skills alteradas + atualiza `meta.json`
- Suporta `FORCE=1` para sincronização imediata

**`SentinelSKILL.md` corrigida (commit `53ff281`):**
- **Bug:** seção "Passagem de bastão" dizia "Pilot executa o deploy" — narrativa, não instrução
- Sentinel narrava "task criada para Pilot" sem nunca chamar `TaskCreate`
- **Fix:** instrução explícita `TaskCreate(agent="Pilot")` (APROVADO) e `TaskCreate(agent="Forge/Loom")` (REPROVADO), com alerta: *NUNCA escrever 'task criada' sem ter chamado TaskCreate*
- Padrão seguido: PlannerSKILL MODO HOTFIX

**Limpeza de worktrees SystemD:**
- 7 worktrees removidos (6 mergeados em main + 1 residual da task 9d265c44)
- `e128e7ee-1` (EntrevistaPage) rebased em main, Sentinel aprovado, Pilot deployou

### [2026-06-18] — Fix crítico: Agent tool bypassa Empire no pipeline hotfix

**Problema diagnosticado:** task `9d265c44` ("Cadastrar manutenção — SystemD") ficou em
`status=review` sem Sentinel nem Pilot terem rodado. Causa raiz: `HotfixSKILL` usava
`Agent tool` como fallback para chamar o Planner. O `Agent tool` cria um subagente local
**sem acesso às ferramentas do Empire** (TaskCreate, Workflow) — então o Planner não
conseguia criar tasks para Forge, Loom, Sentinel e Pilot, e implementava tudo sozinho,
sem commitar. Resultado: código ficou solto no worktree, sem validação, sem deploy.

**Regra crítica aprendida:**

```
Agent tool    → subagente local (sem TaskCreate/Workflow/ferramentas Empire)
Workflow/TaskCreate → task Empire real (worktree isolado + ferramentas completas)

Forge e Loom  → Agent tool OK (implementam código no worktree atual do Planner)
Sentinel/Pilot → OBRIGATÓRIO TaskCreate (precisam de worktree isolado no Empire)
Commit        → OBRIGATÓRIO entre Loom e Sentinel (sem commit = Sentinel vê vazio)
```

**Correções aplicadas:**

| Arquivo | Mudança |
|---|---|
| `HotfixSKILL.md` | `Agent tool` **removido** da cadeia — agora: Workflow → TaskCreate → PARAR |
| `PlannerSKILL.md` | Seção **MODO HOTFIX** adicionada: pipeline abreviado + commit obrigatório + Sentinel/Pilot via TaskCreate |
| `ForgeSKILL.md` | **Commit obrigatório** adicionado na Passagem de bastão (git add + git commit + verificação git status) |
| `LoomSKILL.md` | **Commit obrigatório** adicionado na Passagem de bastão |
| Planner (banco Empire) | Personalidade atualizada com MODO HOTFIX e commit obrigatório |

**Commit:** `5f32cd4` — fix(skills): corrige esteira hotfix

---

### [2026-06-30] — Analista 3 modos + Planner roteador + Hotfix dois fluxos

**Motivação:** leads são escritos por vendedores (não-devs) e futuramente clientes
vão solicitar manutenções via form no próprio sistema deles. O Analista precisa
funcionar sem entrevista interativa em ambos os casos.

**AnalistaSKILL — parser universal de intenção humana:**
- `modo novo_sistema` — lê lead do banco (vitrine/vendedor), sem entrevista interativa
- `modo manutencao` — lê form do cliente, classifica tipo: bug | melhoria_ux | feature_pequena | feature_grande | adicional_contrato
- `modo lead_vendedor` — briefing do vendedor, avança com lacunas marcadas `[CONFIRMAR]`
- Input vago (lead) → notifica Luiz Eduardo via `notificacoes_notificacao` no SystemD
- Input vago (manutenção) → envia email para o cliente via Mailcow
- Nunca inventa, nunca avança no escuro — para e pede luz

**PlannerSKILL — seção TRIAGEM adicionada:**
- Recebe briefing classificado do Analista e decide o pipeline:
  - Pipeline A (novo_sistema completo)
  - Pipeline B (bug/melhoria_ux → Forge+Loom direto)
  - Pipeline C (feature_pequena → Blueprint lite)
  - Pipeline D (feature_grande/contrato → parar, escalar Luiz Eduardo)
- Tipos de notificação no SystemD documentados
- Preserva MODO HOTFIX, REGRA FUNDAMENTAL e regras de Agent tool do remote

**HotfixSKILL — dois fluxos distinguidos:**
- Fluxo 1: Boss CLI (manual, urgente) → Hotfix é o entry point
- Fluxo 2: form de cliente (automático) → Analista modo manutencao é o entry point, não o Hotfix
- Edge case adicionado: solicitação via form vai para Analista

**Commit:** `f63a2ce`

---

## Próximos passos do repositório

```
⬜ Testar pipeline completo com projeto fictício (salão de beleza)
⬜ Ajustar skills baseado nos travamentos encontrados
✅ Skills instaladas globalmente em ~/.claude/skills/ (29/05/2026)
✅ Scripts de automação versionados em automation/ (2026-06-22)
✅ sync_skills.py — propagação automática GitHub → Empire (2026-06-22)
✅ SentinelSKILL corrigida — TaskCreate obrigatório na passagem de bastão (2026-06-22)
✅ AnalistaSKILL — 3 modos: novo_sistema, manutencao, lead_vendedor (2026-06-30)
✅ PlannerSKILL — triagem com Pipeline A/B/C/D (2026-06-30)
✅ HotfixSKILL — dois fluxos distinguidos: Boss CLI vs form de cliente (2026-06-30)
⬜ Implementar disparar_hotfix ligado ao form de manutenção dos sistemas de clientes
⬜ Adicionar n8n ao pipeline (notificações WhatsApp + email)
⬜ Criar templates por segmento (saúde, salão, loja, agro...)
⬜ Versionamento das skills (tag por projeto executado com sucesso)
```

---

*Uid Software e Tecnologia LTDA — Uberlândia/MG*
*"Transformando ideias em soluções digitais com tecnologia, inovação e eficiência"*
*🚀 Lead entra. Fábrica roda. Mensalidade chega.*
