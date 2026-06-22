#!/usr/bin/env python3
"""
Le manutencoes pendentes no SystemD e cria tasks para o Hotfix agent no Claw Empire.
Idempotente (cron-safe): em caso de erro o item fica pendente para a proxima execucao.
"""
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR          = Path(__file__).resolve().parent
SYSTEMD_CONTAINER = "sytemd-backend-1"
HOTFIX_AGENT_ID   = "690df50c-9839-4519-9f55-92b18a394247"

# Mapeamento: caminho no host -> projeto registrado no Empire
CAMINHO_PARA_PROJETO = {
    "/root/SystemD": {
        "project_id":   "7d37906f-9d30-4789-8b7a-f67115951148",
        "project_path": "/home/app/projects/SytemD",
        "name":         "SystemD",
    },
    "/var/www/studio-fluir": {
        "project_id":   "6e8e4126-4dc1-4ccd-bed9-c23b2653d2bb",
        "project_path": "/var/www/studio-fluir",
        "name":         "Nos Studio Fluir",
    },
    "/var/www/contratid": {
        "project_id":   "d01ee4f5-a74d-4aa2-8a2c-4fb40c54fdec",
        "project_path": "/var/www/contratid",
        "name":         "ContratId",
    },
    "/opt/claw-empire": {
        "project_id":   "73e11f87-111b-4038-b112-ebcb924b8055",
        "project_path": "/opt/claw-empire",
        "name":         "Claw Empire",
    },
    "/opt/uid-skills": {
        "project_id":   "260f012c-28cc-4fb3-a7a5-b42d464a84d7",
        "project_path": "/opt/uid-skills",
        "name":         "UidSkills",
    },
    "/opt/uidmail": {
        "project_id":   "091c723e-409f-4be6-a835-8b0adf46e983",
        "project_path": "/opt/uidmail",
        "name":         "UidMail",
    },
}


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
        ["docker", "exec", SYSTEMD_CONTAINER,
         "python", "manage.py", "disparar_hotfix", "--list"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(resultado.stdout)


def marcar_disparada(manutencao_id):
    subprocess.run(
        ["docker", "exec", SYSTEMD_CONTAINER,
         "python", "manage.py", "disparar_hotfix",
         "--mark-dispatched", str(manutencao_id)],
        capture_output=True, text=True, check=True,
    )


def criar_task(env, item, projeto):
    caminho = item["caminho"] or projeto["project_path"]
    titulo_curto = item["descricao"][:60].rstrip()
    if len(item["descricao"]) > 60:
        titulo_curto += "..."

    descricao = (
        f"MODO MANUTENCAO BANCO\n"
        f"MANUTENCAO_ID: {item['id']}\n"
        f"Sistema: {item['os_titulo']} (OS #{item['os_id']})\n"
        f"Cliente: {item['os_cliente']}\n"
        f"Caminho: {caminho}\n\n"
        f"Tarefa:\n{item['descricao']}\n\n"
        f"CLAUDE.md: {caminho}/CLAUDE.md\n\n"
        f"INSTRUCAO FINAL (apos Pilot confirmar CI/CD success):\n"
        f"Marcar manutencao como concluida via MCP PostgreSQL:\n"
        f"  UPDATE ordens_manutencao SET feito=true, atualizado_em=NOW() WHERE id={item['id']};"
    )

    payload = {
        "title":             f"Hotfix — {item['os_titulo']}: {titulo_curto}",
        "description":       descricao,
        "department_id":     "operations",
        "assigned_agent_id": HOTFIX_AGENT_ID,
        "project_id":        projeto["project_id"],
        "project_path":      projeto["project_path"],
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

    if not pendentes:
        print("nenhuma manutencao pendente.")
        return 0

    for item in pendentes:
        caminho = (item.get("caminho") or "").strip()
        projeto = CAMINHO_PARA_PROJETO.get(caminho)

        if not projeto:
            print(
                f"[SKIP] manutencao #{item['id']} — caminho desconhecido: '{caminho}'. "
                f"Adicione ao CAMINHO_PARA_PROJETO em {__file__}.",
                file=sys.stderr,
            )
            continue

        try:
            task_id = criar_task(env, item, projeto)
            print(f"task {task_id[:8]}... criada para manutencao #{item['id']} ({item['os_titulo']})")

            resultado = executar_task(env, task_id)
            pid = resultado.get("pid", "?")
            print(f"agente iniciado: pid={pid}")

            marcar_disparada(item["id"])
            print(f"manutencao #{item['id']} marcada como disparada.")

        except urllib.error.URLError as exc:
            print(f"erro de rede para manutencao #{item['id']}: {exc}", file=sys.stderr)
        except Exception as exc:
            print(f"erro ao processar manutencao #{item['id']}: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
