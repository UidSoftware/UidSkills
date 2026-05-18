# 🏭 UidSkills — Fábrica de Software da Uid

> *"preciso da empresa funcionando sem mim"*
> — Luiz Eduardo Ferreira, fundador

Skills e agents da linha de produção da **Uid Software e Tecnologia LTDA** — uma fábrica de software orientada a agentes de IA que transforma leads em sistemas em produção.

---

## O Time

| Agent | Papel | Metáfora |
|---|---|---|
| 🎯 **Planner** | Lead Agent + Gerente de Projeto | O maestro |
| 🔍 **Analista** | Levantamento de Requisitos (Sommerville) | O tradutor |
| 🎨 **Brush** | Designer UI/UX | O pintor |
| 🏗️ **Blueprint** | Arquiteto de Software | O arquiteto |
| ⚒️ **Forge** | Dev Backend (Django + DRF) | O ferreiro |
| 🧵 **Loom** | Dev Frontend (React + Vite) | O tecelão |
| 🛡️ **Sentinel** | QA / Testes | O sentinela |
| ✈️ **Pilot** | DevOps / Deploy | O piloto |

---

## O Pipeline

```
LEAD NO BANCO
      ↓
  [PLANNER]        ← orquestra tudo
      ↓
  [ANALISTA]       ← elicita, modela, documenta
      ↓
  [DOC-GENERATOR]  ← gera 8 documentos
      ↓
  [BLUEPRINT]  +  [BRUSH]   ← técnica + visual (paralelo)
      ↓
  [FORGE]  +  [LOOM]        ← backend + frontend (paralelo)
      ↓
  [SENTINEL]       ← valida tudo
      ↓
  [PILOT]          ← CI/CD, deploy na VPS
      ↓
💰 SISTEMA EM PRODUÇÃO
```

---

## Estrutura

```
UidSkills/
├── CLAUDE.md                  ← âncora — leia primeiro
├── README.md                  ← este arquivo
├── .gitignore
├── .claude/
│   └── skills/                ← skills dos agents
│       ├── PlannerSKILL.md
│       ├── AnalistaSKILL.md
│       ├── AnalistaUML.md
│       ├── BrushSKILL.md
│       ├── BlueprintSKILL.md
│       ├── ForgeSKILL.md
│       ├── LoomSKILL.md
│       ├── SentinelSKILL.md
│       ├── PilotSKILL.md
│       └── doc-generator_SKILL.md
└── docs/
    └── visao_original.md      ← a história da fábrica
```

---

## Como usar

```bash
# 1. Clonar o repo
git clone git@github.com:UidSoftware/UidSkills.git
cd UidSkills

# 2. Abrir o Claude Code
claude

# 3. Iniciar o pipeline com um lead
# "Planner, tenho um lead novo: João da Silva,
#  Salão de Beleza Corte & Estilo, Uberlândia/MG.
#  Inicie o pipeline."
```

O Claude Code vai ler o `CLAUDE.md` automaticamente e carregar todas as skills. O Planner orquestra o resto.

---

## Metodologia

```
Scrum  → Uid ↔ cliente (sprints, backlog, review)
Kanban → agents internos (fluxo contínuo em tempo real)
```

---

## Stack padrão

```
Backend:  Django 5.x + DRF + SimpleJWT
Frontend: React 18 + Vite + Tailwind CSS + PWA
Banco:    PostgreSQL 16
Infra:    Docker + Nginx + Gunicorn
CI/CD:    GitHub Actions
VPS:      Ubuntu 24.04
```

---

## Sobre a Uid

**Uid Software e Tecnologia LTDA**
Micro empresa | Simples Nacional | CNPJ 60.939.393/0001-25
Uberlândia/MG | Operação 100% remota

> *"Transformando ideias em soluções digitais com tecnologia, inovação e eficiência."*

📧 contato@uidsoftware.com.br
🌐 www.uidsoftware.com.br
🐙 github.com/UidSoftware
