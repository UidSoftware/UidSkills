# Visão Original — A Semente da Fábrica

> *"preciso da empresa funcionando sem mim"*
> — Luiz Eduardo Ferreira, fundador da Uid Software

---

## O Contexto

Este documento registra a visão original que deu origem ao pipeline
de agents da Uid Software — antes de qualquer skill ser criada,
antes do Studio Fluir ir pra produção, antes do time ter nome.

Era uma ideia. Virou arquitetura. Virou código. Virou fábrica.

---

## A Visão Original (texto do fundador)

> O que eu pensei foi: criar Levantamento de Requisitos, UML, MER,
> todos os processos se criam baseados neles.
>
> Analista: cria Levantamento de Requisitos (Entrevista, Resumo como
> cliente trabalha, Resumo do Sistema, Funcional, Não Funcional, etc),
> UML (UseCase, Class, Atividade, outros), MER.
>
> Porque: esses arquivos bem criados, já são uma base sólida.
> Escolhi a UML pois tem 26 diagramas que focam em partes distintas
> de um mesmo sistema, identificando o todo, e a IA consegue analisar
> cada diagrama. Meu professor da Facul dizia:
> **"Quanto mais informação, melhor sua tomada de decisão."**

---

## O Pipeline Original

```
CLIENTE
   ↓
ANALISTA (Claude.ai chat)
   ├── Levantamento de Requisitos
   │     ├── Entrevista estruturada
   │     ├── Como o cliente trabalha (AS-IS)
   │     ├── Como o sistema vai funcionar (TO-BE)
   │     ├── Requisitos Funcionais
   │     └── Requisitos Não Funcionais
   ├── UML (26 diagramas, conforme necessidade)
   │     ├── Use Case
   │     ├── Classes
   │     ├── Atividade
   │     └── ...
   └── MER
   ↓
DOCUMENTAÇÃO (Claude.ai chat)
   ├── Dicionario_Dados.md
   ├── Regras_Negocio.md
   ├── CLAUDE.md
   ├── Instrucoes_Claude_Code.md
   ├── Arquitetura_Tecnica.md
   ├── README.md
   ├── deploy.sh
   ├── testes.md
   └── Contrato_Servico.md
   ↓
EXECUÇÃO (Claude Code)
   ├── Lê TODOS os arquivos
   ├── Cria o sistema
   ├── CI/CD
   └── Testes (caixa branca e preta)
   ↓
UID SOFTWARE
   ├── Compra domínio
   ├── Provisiona VPS (se necessário)
   └── Manutenção dos softwares utilizados
```

---

## A Análise de Viabilidade (Claude, na época)

| Etapa | Automação | Observação |
|---|---|---|
| Formulário → Banco | 100% ✅ | Simples |
| Banco → Analista | 100% ✅ | Skill lê do banco |
| Analista → UMLs | 85% ⚠️ | Bom mas precisa revisão |
| doc-generator | 90% ✅ | Já funciona bem |
| Claude Code → Código | 80% ⚠️ | Projetos complexos travam |
| Deploy | 95% ✅ | deploy.sh resolve |
| Revisão humana | necessária | 1 ponto de checagem antes do deploy |

> *"A empresa não roda 100% sem você —*
> *mas roda com 1 ponto de controle em vez de 100."*

---

## Como a Visão Evoluiu

```
VISÃO ORIGINAL              →    O QUE FOI CONSTRUÍDO
────────────────────────         ──────────────────────────────
Skill Analista              →    AnalistaSKILL.md (Sommerville)
UML em Mermaid              →    AnalistaUML.md (7 diagramas)
doc-generator               →    doc-generator_SKILL.md ✅
Claude Code gera tudo       →    Forge + Loom + Sentinel
Deploy automatizado         →    PilotSKILL.md (CI/CD)
Empresa sem você            →    PlannerSKILL.md (orquestrador)
1 ponto de checagem         →    Sentinel aprova antes do Pilot
Skill Generalista           →    BrushSKILL.md + BlueprintSKILL.md
Formulário no site          →    SystemD (menu Office → Novo Projeto)
```

---

## O Pipeline Atual (versão evoluída)

```
LEAD NO BANCO (MCP PostgreSQL)
        ↓
   [PLANNER]          ← orquestra tudo autonomamente
        ↓
   [ANALISTA]         ← Sommerville completo
        ↓
   [DOC-GENERATOR]    ← 8 documentos automáticos
        ↓
   [BLUEPRINT] + [BRUSH]  ← técnica + visual (paralelo)
        ↓
   [FORGE] + [LOOM]   ← backend + frontend (paralelo)
        ↓
   [SENTINEL]         ← nada passa sem aprovação
        ↓
   [PILOT]            ← CI/CD, zero SSH manual
        ↓
SISTEMA EM PRODUÇÃO → MENSALIDADE NA CONTA 💰
```

---

## A Frase que Originou Tudo

> *"minha visão: www.uidsoftware.com.br > banco de dados >*
> *skill analista pega informações completas no banco >*
> *cria UMLs > skill doc-generator gera o restante >*
> *todos esses arquivos numa pasta >*
> *Claude Code pega todos os arquivos e gera o código e deploy.*
> *Resumo do que pensei: preciso da empresa funcionando sem mim."*
>
> — Luiz Eduardo Ferreira

---

*Uid Software e Tecnologia LTDA — Uberlândia/MG*
*Fundada em maio de 2025. Fábrica de software concebida em 2024.*
*"Transformando ideias em soluções digitais com tecnologia, inovação e eficiência."*
