#!/usr/bin/env python3
"""
generate_agents.py — Gera/atualiza os agent files globais em ~/.claude/agents/
a partir das skills em /opt/uid-skills/.claude/skills/.

Deve ser executado sempre que novas skills forem adicionadas ou atualizadas.
Pode ser encadeado após sync_skills.py ou rodado manualmente.

Uso:
  python3 generate_agents.py
"""

import logging
import os
import re
import subprocess
import sys
from pathlib import Path

SKILLS_DIR  = Path("/opt/uid-skills/.claude/skills")
AGENTS_DIR  = Path("/root/.claude/agents")
LOG_FILE    = "/opt/uid-automation/generate_agents.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def git_pull() -> str:
    result = subprocess.run(
        ["git", "pull", "origin", "main"],
        cwd="/opt/uid-skills",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git pull falhou: {result.stderr.strip()}")
    return result.stdout.strip()


def extract_name(content: str) -> str | None:
    m = re.search(r"^name:\s*(\S+)", content, re.MULTILINE)
    return m.group(1).strip() if m else None


def main():
    log.info("=== generate_agents iniciado ===")

    try:
        pull_out = git_pull()
        log.info(f"git pull: {pull_out}")
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    criados = atualizados = pulados = 0

    for md in sorted(SKILLS_DIR.glob("*.md")):
        content = md.read_text(encoding="utf-8")
        name = extract_name(content)

        if not name:
            log.warning(f"  {md.name}: sem name no frontmatter — pulando")
            pulados += 1
            continue

        agent_path = AGENTS_DIR / f"{name}.md"
        existe = agent_path.exists()
        atual  = agent_path.read_text(encoding="utf-8") if existe else ""

        if atual == content:
            log.info(f"  {name}.md: sem alterações")
            continue

        agent_path.write_text(content, encoding="utf-8")

        if existe:
            log.info(f"  {md.name} -> {name}.md: atualizado")
            atualizados += 1
        else:
            log.info(f"  {md.name} -> {name}.md: criado")
            criados += 1

    log.info(f"=== concluído: {criados} criados, {atualizados} atualizados, {pulados} pulados ===")
    print(f"generate_agents: {criados} criados, {atualizados} atualizados, {pulados} pulados")


if __name__ == "__main__":
    main()
