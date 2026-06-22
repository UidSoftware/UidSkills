#!/usr/bin/env python3
"""
retomar_agente.py
Watchdog: detecta tasks em andamento ha mais de 25 min sem atividade
(indicativo de token limit) e cria task de retomada para o mesmo agente.
Roda a cada 30 min via cron. Idempotente e limitado a 5 retomadas por cadeia.
"""

import json
import sqlite3
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

EMPIRE_URL    = "http://localhost:8005"
EMPIRE_TOKEN  = "fdc77a23bdb2fe287a5d81409d7dd1babe450452b89968ff61f9b8c1477cca51"
EMPIRE_DB     = "/var/lib/docker/volumes/claw-empire_claw_empire_data/_data/claw-empire.sqlite"
LOG_FILE      = "/var/log/uid-retomar-agente.log"

STALE_MS      = 25 * 60 * 1000   # 25 minutos sem atividade → stalled
MAX_RETOMADAS = 5                 # maximo de retomadas na mesma cadeia


def log(msg):
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def api(method, path, body=None):
    url = EMPIRE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {EMPIRE_TOKEN}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def ultima_atividade_ms(task_id):
    """Retorna o timestamp (ms) da ultima entrada em task_logs para essa task."""
    con = sqlite3.connect(EMPIRE_DB)
    cur = con.cursor()
    cur.execute(
        "SELECT MAX(created_at) FROM task_logs WHERE task_id = ?",
        (task_id,)
    )
    row = cur.fetchone()
    con.close()
    return row[0] if row and row[0] else None


def contar_retomadas(task_id):
    """
    Conta quantas retomadas ja existem na cadeia via source_task_id.
    Limita a travessia em MAX_RETOMADAS+2 para evitar loop.
    """
    con = sqlite3.connect(EMPIRE_DB)
    cur = con.cursor()
    depth = 0
    current = task_id
    visited = set()
    while current and depth <= MAX_RETOMADAS + 2:
        if current in visited:
            break
        visited.add(current)
        cur.execute("SELECT source_task_id FROM tasks WHERE id = ?", (current,))
        row = cur.fetchone()
        if not row or not row[0]:
            break
        current = row[0]
        depth += 1
    con.close()
    return depth


def build_retomada_desc(task):
    project_path = task.get("project_path") or f"/var/www/{(task.get('project_name') or '').lower()}"
    return f"""## RETOMADA AUTOMATICA — SESSAO INTERROMPIDA POR LIMITE DE TOKENS

A sessao anterior da task **"{task['title']}"** foi interrompida.
Este e o inicio de uma nova sessao com tokens frescos. Continue exatamente de onde parou.

---

### CONTEXTO ORIGINAL DA TASK
{task['description']}

---

### INSTRUCAO DE RETOMADA
1. **Avalie o estado atual** antes de qualquer acao:
   - Verifique arquivos criados: `ls -la {project_path}/`
   - Verifique git history: `git -C {project_path} log --oneline -20 2>/dev/null || echo 'sem commits'`
   - Cheque status de containers Docker: `docker ps | grep {(task.get('project_name') or '').lower()}`

2. **Determine o que ja foi feito** e o que falta:
   - Backend criado? -> pule o Forge, va direto ao proximo passo
   - Frontend criado? -> pule o Loom, va direto ao proximo passo
   - Ambos criados? -> va para Sentinel -> Pilot

3. **Continue a partir do ponto correto** — NAO refaca o que ja esta pronto.

4. Se encontrar trabalho pela metade (arquivos parciais), complete-os antes de avancar.

> Retomada automatica — task original: `{task['id']}`
"""


def main():
    log("=== uid-retomar-agente iniciado ===")
    agora_ms = int(time.time() * 1000)

    try:
        data = api("GET", "/api/tasks?status=in_progress&limit=50")
    except Exception as e:
        log(f"Erro ao listar tasks: {e}")
        return 1

    tasks = data.get("tasks", [])
    if not tasks:
        log("Nenhuma task em andamento. Nada a verificar.")
        return 0

    log(f"{len(tasks)} task(s) em andamento encontrada(s).")
    retomadas = 0

    for task in tasks:
        task_id    = task["id"]
        title      = task["title"]
        updated_at = task.get("updated_at") or task.get("created_at") or 0

        last_log = ultima_atividade_ms(task_id)
        ultima_atividade = max(updated_at, last_log or 0)
        tempo_parado_ms = agora_ms - ultima_atividade

        if tempo_parado_ms < STALE_MS:
            log(f"Task '{title}' ({task_id[:8]}) ativa ha {tempo_parado_ms//1000}s — OK.")
            continue

        minutos = tempo_parado_ms // 60000
        log(f"Task '{title}' ({task_id[:8]}) PARADA ha {minutos} min -> verificando retomadas...")

        n_retomadas = contar_retomadas(task_id)
        if n_retomadas >= MAX_RETOMADAS:
            log(f"  -> Cadeia ja tem {n_retomadas} retomadas (limite={MAX_RETOMADAS}). Pulando — intervencao manual necessaria.")
            continue

        nova_desc = build_retomada_desc(task)
        try:
            nova_task = api("POST", "/api/tasks", {
                "title":             f"{title} [retomada {n_retomadas + 1}]",
                "description":       nova_desc,
                "priority":          task.get("priority", 3),
                "status":            "inbox",
                "task_type":         task.get("task_type", "general"),
                "project_id":        task.get("project_id"),
                "project_path":      task.get("project_path"),
                "department_id":     task.get("department_id"),
                "assigned_agent_id": task.get("assigned_agent_id"),
                "source_task_id":    task_id,
            })
            nova_id = (nova_task.get("task") or nova_task).get("id")
            log(f"  -> Retomada criada: id={nova_id} (retomada {n_retomadas + 1}/{MAX_RETOMADAS})")

            # Disparar o agente — POST /run inicia o processo, PATCH nao inicia
            try:
                run_result = api("POST", f"/api/tasks/{nova_id}/run", {})
                pid = run_result.get("pid", "?")
                log(f"  -> Agente retomado: pid={pid}")
            except Exception as e_run:
                log(f"  -> AVISO: retomada criada mas /run falhou: {e_run}")

            # Marca task original como done para nao re-detectar na proxima execucao
            api("PATCH", f"/api/tasks/{task_id}", {"status": "done"})
            log(f"  -> Task original {task_id[:8]} marcada como done.")
            retomadas += 1

        except Exception as e:
            log(f"  -> ERRO ao criar retomada para '{title}': {e}")

    if retomadas == 0:
        log("Nenhuma task stalled detectada.")
    else:
        log(f"{retomadas} retomada(s) criada(s).")

    log("=== uid-retomar-agente concluido ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
