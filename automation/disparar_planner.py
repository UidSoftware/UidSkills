#!/usr/bin/env python3
"""
Le notificacoes PRONTO_PARA_PLANNER pendentes no SystemD e cria a task
correspondente para o Planner no Claw Empire. Idempotente (cron-safe):
em caso de erro o item fica pendente e sera tentado de novo na proxima execucao.
"""
import json
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR          = Path(__file__).resolve().parent
SYSTEMD_CONTAINER = "sytemd-backend-1"
EMPIRE_CONTAINER  = "claw-empire"
EMPIRE_DB         = "/var/lib/docker/volumes/claw-empire_claw_empire_data/_data/claw-empire.sqlite"


def load_env(path):
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def listar_pendentes():
    resultado = subprocess.run(
        ["docker", "exec", SYSTEMD_CONTAINER, "python", "manage.py", "disparar_planner", "--list"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(resultado.stdout)


def marcar_resolvido(notificacao_id):
    subprocess.run(
        ["docker", "exec", SYSTEMD_CONTAINER, "python", "manage.py", "disparar_planner",
         "--mark-done", str(notificacao_id)],
        capture_output=True, text=True, check=True,
    )


def get_or_create_project(env, nome):
    """Retorna (project_id, project_path) do Claw Empire, criando o projeto se necessario."""
    project_path = f"/var/www/{nome.lower()}"

    con = sqlite3.connect(EMPIRE_DB)
    cur = con.cursor()
    cur.execute("SELECT id FROM projects WHERE project_path = ?", (project_path,))
    row = cur.fetchone()
    con.close()

    if row:
        return row[0], project_path

    payload = {
        "name": nome,
        "project_path": project_path,
        "github_repo": f"UidSoftware/{nome}",
    }
    req = urllib.request.Request(
        f"{env['CLAW_EMPIRE_URL']}/api/projects",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {env['CLAW_EMPIRE_API_TOKEN']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    project_id = (data.get("project") or data).get("id")
    print(f"projeto '{nome}' criado no Empire: id={project_id}")
    return project_id, project_path


def garantir_repo(project_path, nome):
    """Garante que project_path e um git repo. Clona do GitHub via container se necessario."""
    Path(project_path).mkdir(parents=True, exist_ok=True)

    check = subprocess.run(
        ["docker", "exec", EMPIRE_CONTAINER, "git", "-C", project_path, "rev-parse", "--git-dir"],
        capture_output=True,
    )
    if check.returncode == 0:
        return  # ja e repo

    tmp = f"/tmp/uid_clone_{nome.lower()}_{int(time.time())}"
    subprocess.run(
        ["docker", "exec", EMPIRE_CONTAINER, "git", "clone",
         f"git@github.com:UidSoftware/{nome}.git", tmp],
        check=True,
    )
    subprocess.run(
        ["docker", "exec", EMPIRE_CONTAINER, "bash", "-c",
         f"cp -r {tmp}/. {project_path}/ && rm -rf {tmp}"],
        check=True,
    )
    # Container roda como uid=10001 — corrigir dono no host para evitar permission denied
    subprocess.run(["chown", "-R", "10001:10001", project_path], check=True)
    print(f"repo UidSoftware/{nome} clonado para {project_path}")


def criar_task(env, item, project_id, project_path):
    """Cria a task no Empire e retorna o task_id."""
    descricao = (
        f"Arquitetura Tecnica #{item['arquitetura_id']} registrada "
        f"(Entrevista: {item['entrevista_sistema']}, Prospecto: {item['prospecto_nome']}). "
        "Stack validada (sem divergencia pendente do padrao Uid). "
        "Antes de agir: aplicar a checagem 'Pre-voo: uso do Claude' do PlannerSKILL. "
        "Se uso = 0%, ler ordens_arquiteturatecnica "
        f"id={item['arquitetura_id']} via MCP PostgreSQL e iniciar o Fluxo 1 (Etapa 1 em diante)."
    )
    payload = {
        "title":             f"Fluxo 1 — {item['projeto']}",
        "description":       descricao,
        "department_id":     "planning",
        "assigned_agent_id": env["PLANNER_AGENT_ID"],
        "project_id":        project_id,
        "project_path":      project_path,
    }
    req = urllib.request.Request(
        f"{env['CLAW_EMPIRE_URL']}/api/tasks",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {env['CLAW_EMPIRE_API_TOKEN']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    task = data.get("task") or data
    return task["id"]


def executar_task(env, task_id):
    """Dispara o agente via POST /api/tasks/{id}/run. PATCH nao inicia processo."""
    req = urllib.request.Request(
        f"{env['CLAW_EMPIRE_URL']}/api/tasks/{task_id}/run",
        data=b"{}",
        method="POST",
        headers={
            "Authorization": f"Bearer {env['CLAW_EMPIRE_API_TOKEN']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main():
    env = load_env(BASE_DIR / ".env")

    try:
        pendentes = listar_pendentes()
    except Exception as exc:
        print(f"erro ao listar pendentes: {exc}", file=sys.stderr)
        return 1

    for item in pendentes:
        nome = item["projeto"]
        try:
            # 1. Garantir projeto no Empire e git repo no project_path
            project_id, project_path = get_or_create_project(env, nome)
            garantir_repo(project_path, nome)

            # 2. Criar task com project_id e project_path
            task_id = criar_task(env, item, project_id, project_path)
            print(f"task {task_id[:8]} criada para {nome} (arquitetura #{item['arquitetura_id']})")

            # 3. Disparar o agente — POST /run inicia o processo, PATCH nao inicia
            resultado = executar_task(env, task_id)
            pid = resultado.get("pid", "?")
            print(f"agente iniciado: pid={pid}")

            # 4. So marcar como resolvido apos task criada E agente iniciado
            marcar_resolvido(item["notificacao_id"])

        except urllib.error.URLError as exc:
            print(f"erro de rede para {nome} (notificacao {item['notificacao_id']}): {exc}", file=sys.stderr)
        except Exception as exc:
            print(f"erro ao processar {nome} (notificacao {item['notificacao_id']}): {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
