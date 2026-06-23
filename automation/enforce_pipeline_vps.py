#!/usr/bin/env python3
# PreToolUse hook — enforcement real do pipeline na VPS
# Regras absolutas valem para TODOS; regras de sessao direta poupam subagentes (Forge/Loom)
import json, sys, re, os

def deny(msg):
    print(json.dumps({"decision": "block", "reason": msg}))
    sys.exit(0)

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "")
ti   = data.get("tool_input", {})
cmd  = ti.get("command", "")
filepath = ti.get("file_path") or ti.get("path", "")

# ── BLOQUEIOS ABSOLUTOS (valem para qualquer sessao, agente ou nao) ──────────

# git push --force jamais
if re.search(r"git push\b.+(-f\b|--force)", cmd):
    deny("git push --force JAMAIS PERMITIDO. Nenhum agente pode forcarbranch.")

# docker compose prod direto — so Pilot via CI/CD
if re.search(r"docker compose\b.*(up|down|build|restart)", cmd) and re.search(r"\bprod\b|\.prod\.", cmd):
    deny("docker compose prod bloqueado. Apenas o Pilot via GitHub Actions CI/CD.")

# ── BLOQUEIOS DE SESSAO DIRETA (nao valem para subagentes Forge/Loom) ────────

is_subagent = os.environ.get("CLAUDE_CODE_IS_SUBAGENT") == "1"
if not is_subagent:
    PROJECT_ROOTS = ("/var/www/", "/root/SystemD/", "/root/SytemD/")
    PIPELINE_MSG = (
        "PIPELINE OBRIGATORIO — use o Boss CLI: "
        "Hotfix -> Planner -> Forge/Loom -> Sentinel -> Pilot. "
        "Edicao direta de codigo em sessao nao delegada e proibida."
    )

    if tool in ("Edit", "Write", "MultiEdit"):
        if any(filepath.startswith(p) for p in PROJECT_ROOTS):
            deny(PIPELINE_MSG)

    if re.search(r"\bgit\s+(push|add|commit)\b", cmd):
        deny(PIPELINE_MSG)

    if re.search(r"\bdocker compose\b.*(up|down|build)\b", cmd):
        deny(PIPELINE_MSG)

sys.exit(0)
