#!/usr/bin/env python3
"""
sync_skills.py — Sincroniza skills do UidSkills (GitHub) para o Empire.

Fluxo:
  1. git pull em /opt/uid-skills
  2. Para cada *.md em .claude/skills/:
       - deriva o canonical name (frontmatter name: + 'skill')
       - verifica se existe em /app/data/custom-skills/ no container
       - se o conteúdo mudou: docker cp + atualiza meta.json
  3. Loga tudo em /opt/uid-automation/sync_skills.log

Uso:
  python3 sync_skills.py            # só sincroniza se git pull trouxer mudanças
  FORCE=1 python3 sync_skills.py   # força sincronização mesmo sem mudanças no git
"""

import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ─── Configuração ────────────────────────────────────────────────────────────

UID_SKILLS_DIR  = Path("/opt/uid-skills/.claude/skills")
CONTAINER       = "claw-empire"
EMPIRE_SKILLS   = "/app/data/custom-skills"
LOG_FILE        = "/opt/uid-automation/sync_skills.log"

# Mapeamento explícito para arquivos sem frontmatter name: válido
EXPLICIT_MAP = {
    "doc-generator_SKILL.md": "docgeneratorskill",
}

# ─── Logging ─────────────────────────────────────────────────────────────────

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


def canonical_from_frontmatter(md_path: Path) -> str | None:
    """Extrai 'name:' do frontmatter YAML e converte para canonical (lowercase + 'skill')."""
    content = md_path.read_text(encoding="utf-8")
    match = re.search(r"^name:\s*(\S+)", content, re.MULTILINE)
    if not match:
        return None
    name = match.group(1).lower().replace("-", "").replace("_", "")
    return name if name.endswith("skill") else name + "skill"


def empire_skill_dirs() -> set[str]:
    result = subprocess.run(
        ["docker", "exec", CONTAINER, "ls", EMPIRE_SKILLS],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Não foi possível listar skills do Empire: {result.stderr}")
    return set(result.stdout.strip().split("\n"))


def read_empire_skill(canonical: str) -> str:
    result = subprocess.run(
        ["docker", "exec", CONTAINER, "cat", f"{EMPIRE_SKILLS}/{canonical}/skills.md"],
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else ""


def sync_skill(md_path: Path, canonical: str) -> bool:
    """Copia skill para o Empire se o conteúdo mudou. Retorna True se atualizou."""
    new_content = md_path.read_text(encoding="utf-8")
    current    = read_empire_skill(canonical)

    if new_content == current:
        log.info(f"  {canonical}: sem alterações")
        return False

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(new_content)
        tmp_path = tmp.name

    try:
        # Copiar skills.md
        dest = f"{CONTAINER}:{EMPIRE_SKILLS}/{canonical}/skills.md"
        r = subprocess.run(["docker", "cp", tmp_path, dest], capture_output=True)
        if r.returncode != 0:
            log.error(f"  {canonical}: docker cp falhou — {r.stderr.decode()}")
            return False

        # Atualizar meta.json
        meta_raw = subprocess.run(
            ["docker", "exec", CONTAINER, "cat", f"{EMPIRE_SKILLS}/{canonical}/meta.json"],
            capture_output=True, text=True,
        )
        if meta_raw.returncode == 0:
            meta = json.loads(meta_raw.stdout)
            meta["contentLength"] = len(new_content)
            meta["updatedAt"]     = int(time.time() * 1000)

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as m:
                json.dump(meta, m, indent=2)
                meta_tmp = m.name

            subprocess.run(
                ["docker", "cp", meta_tmp,
                 f"{CONTAINER}:{EMPIRE_SKILLS}/{canonical}/meta.json"],
                capture_output=True,
            )
            os.unlink(meta_tmp)

        log.info(f"  {canonical}: atualizado ({len(new_content)} chars)")
        return True

    finally:
        os.unlink(tmp_path)


def main():
    log.info("=== sync_skills iniciado ===")
    force = os.environ.get("FORCE") == "1"

    # 1. Git pull
    try:
        pull_out = git_pull()
        log.info(f"git pull: {pull_out}")
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)

    if "Already up to date" in pull_out and not force:
        log.info("Nada a sincronizar (use FORCE=1 para forçar)")
        print("sync_skills: nada a sincronizar")
        return

    # 2. Listar dirs do Empire
    try:
        dirs = empire_skill_dirs()
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)

    # 3. Iterar skills
    updated = skipped = errors = 0

    for md in sorted(UID_SKILLS_DIR.glob("*.md")):
        filename = md.name

        # Derivar canonical
        canonical = EXPLICIT_MAP.get(filename) or canonical_from_frontmatter(md)

        if not canonical:
            log.warning(f"  {filename}: sem name no frontmatter e sem mapeamento explícito — skip")
            skipped += 1
            continue

        if canonical not in dirs:
            log.info(f"  {filename} -> {canonical}: não existe no Empire — skip")
            skipped += 1
            continue

        try:
            if sync_skill(md, canonical):
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            log.error(f"  {canonical}: erro — {e}")
            errors += 1

    log.info(f"=== concluído: {updated} atualizados, {skipped} sem alteração/skip, {errors} erros ===")
    print(f"sync_skills: {updated} atualizados, {skipped} sem alteração, {errors} erros")


if __name__ == "__main__":
    main()
