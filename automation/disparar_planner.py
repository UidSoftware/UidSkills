#!/usr/bin/env python3
"""
disparar_planner.py — dispara o Planner diretamente via Claude Code CLI
(`--agent planner`), sem depender do Claw Empire.

Le notificacoes PRONTO_PARA_PLANNER pendentes no SystemD (via management
command `disparar_planner`) e roda uma sessao `claude --agent planner` em
background por processo, rastreando PID localmente em
planner_processos.json. Mesma logica de reconciliacao e retentativa do
disparar_hotfix.py — ver esse arquivo para o raciocinio completo.

Diferenca principal: Fluxo 1 e para projeto NOVO, entao antes de disparar
o agente garante que o repo existe em /var/www/{nome}. Nao depende mais do
container do Claw Empire para o git clone — a chave SSH propria do root
para o GitHub (/root/.ssh/id_ed25519_github) ja funciona direto no host,
entao nao ha mais o problema de dono de arquivo (uid 10001 do container)
que causava corrupcao de permissao em /var/www/*.
"""
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR          = Path(__file__).resolve().parent
ESTADO_PATH       = BASE_DIR / "planner_processos.json"
SYSTEMD_CONTAINER = "sytemd-backend-1"
TOKEN_PATH        = Path("/root/.claude_oauth_token")
LOG_DIR           = Path("/root/esteira-logs")

MAX_TENTATIVAS  = 3
TIMEOUT_MINUTOS = 180  # Fluxo 1 e maior que hotfix (projeto inteiro do zero)
MAX_BUDGET_USD  = 20


def carregar_estado():
    if not ESTADO_PATH.exists():
        return {}
    try:
        return json.loads(ESTADO_PATH.read_text())
    except json.JSONDecodeError:
        print(f"aviso: {ESTADO_PATH} corrompido, recomecando do zero.", file=sys.stderr)
        return {}


def salvar_estado(estado):
    ESTADO_PATH.write_text(json.dumps(estado, indent=2, ensure_ascii=False))


def processo_vivo(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def matar_processo(pid):
    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except OSError:
        pass


def status_notificacao(notificacao_id):
    resultado = subprocess.run(
        ["docker", "exec", SYSTEMD_CONTAINER, "python", "manage.py",
         "disparar_planner", "--status", str(notificacao_id)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(resultado.stdout)


def marcar_resolvido(notificacao_id):
    subprocess.run(
        ["docker", "exec", SYSTEMD_CONTAINER, "python", "manage.py",
         "disparar_planner", "--mark-done", str(notificacao_id)],
        capture_output=True, text=True, check=True,
    )


def listar_pendentes():
    resultado = subprocess.run(
        ["docker", "exec", SYSTEMD_CONTAINER, "python", "manage.py",
         "disparar_planner", "--list"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(resultado.stdout)


def reconciliar(estado):
    remover = []
    for notificacao_id, info in estado.items():
        pid = info["pid"]

        if processo_vivo(pid):
            iniciado = datetime.fromisoformat(info["iniciado_em"])
            elapsed_min = (datetime.now(timezone.utc) - iniciado).total_seconds() / 60
            if elapsed_min < TIMEOUT_MINUTOS:
                print(f"[RECONCILIA] notificacao #{notificacao_id} ainda rodando (pid={pid}, {elapsed_min:.0f}min).")
                continue
            print(f"[RECONCILIA] notificacao #{notificacao_id} passou do timeout ({TIMEOUT_MINUTOS}min) — encerrando pid={pid}.")
            matar_processo(pid)

        else:
            try:
                status = status_notificacao(notificacao_id)
            except Exception as exc:
                print(f"[RECONCILIA] erro ao checar status da notificacao #{notificacao_id}: {exc} — mantendo em andamento.", file=sys.stderr)
                continue

            if not status.get("encontrada"):
                print(f"[RECONCILIA] notificacao #{notificacao_id} nao encontrada — removendo do rastreamento.")
                remover.append(notificacao_id)
                continue

            if status.get("resolvida"):
                print(f"[RECONCILIA] notificacao #{notificacao_id} concluida com sucesso (pid={pid} encerrado).")
                remover.append(notificacao_id)
                continue

        info["tentativas"] = info.get("tentativas", 0) + 1
        if info["tentativas"] < MAX_TENTATIVAS:
            print(f"[RECONCILIA] notificacao #{notificacao_id} nao concluiu — sera tentada de novo ({info['tentativas']}/{MAX_TENTATIVAS}). Log: {info.get('log')}")
        else:
            print(f"[RECONCILIA] notificacao #{notificacao_id} excedeu {MAX_TENTATIVAS} tentativas — intervencao manual necessaria. Log: {info.get('log')}")
        remover.append(notificacao_id)

    for notificacao_id in remover:
        estado.pop(notificacao_id, None)

    return estado


def garantir_repo(project_path, nome):
    """Garante que project_path e um git repo no host. Clona via SSH proprio do root se necessario."""
    Path(project_path).mkdir(parents=True, exist_ok=True)

    check = subprocess.run(
        ["git", "-C", project_path, "rev-parse", "--git-dir"],
        capture_output=True,
    )
    if check.returncode == 0:
        return True, "ja existia"

    tmp = f"/tmp/uid_clone_{nome.lower()}_{int(time.time())}"
    clone = subprocess.run(
        ["git", "clone", f"git@github.com:UidSoftware/{nome}.git", tmp],
        capture_output=True, text=True,
    )
    if clone.returncode != 0:
        return False, clone.stderr.strip()

    subprocess.run(["bash", "-c", f"cp -r {tmp}/. {project_path}/ && rm -rf {tmp}"], check=True)
    return True, "clonado agora"


def montar_prompt(item, project_path):
    return f"""MODO NOVO PROJETO — FLUXO 1
NOTIFICACAO_ID: {item['notificacao_id']}
Projeto: {item['projeto']}
Caminho: {project_path}
Prospecto: {item['prospecto_nome']}
Sistema (Entrevista): {item['entrevista_sistema']}

Contexto do projeto (resumo da Entrevista):
{item['core_goal']}

Arquitetura Tecnica #{item['arquitetura_id']} ja registrada e validada (sem
divergencia pendente do padrao Uid) — consultar via MCP PostgreSQL
(mcp__systemd__query) na tabela ordens_arquiteturatecnica, id={item['arquitetura_id']},
para os detalhes completos (stack, models, endpoints planejados).

CLAUDE.md: {project_path}/CLAUDE.md (ler antes de agir)

Siga o Fluxo 1 a partir da Etapa 1: Analista -> Blueprint/Brush -> Forge/Loom
-> Sentinel -> Pilot. Nao pular etapas.

INSTRUCAO FINAL (somente apos Sentinel validar de verdade e Pilot confirmar
deploy real em producao):
Marcar notificacao como resolvida via Bash:
  docker exec sytemd-backend-1 python manage.py disparar_planner --mark-done {item['notificacao_id']}
"""


def disparar(item):
    nome = item["projeto"]
    project_path = f"/var/www/{nome.lower()}"

    ok, detalhe = garantir_repo(project_path, nome)
    if not ok:
        print(f"[SKIP] notificacao #{item['notificacao_id']} ({nome}) — falha ao garantir repo: {detalhe}", file=sys.stderr)
        return None
    print(f"repo de {nome} em {project_path}: {detalhe}")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"planner-notificacao-{item['notificacao_id']}-{int(time.time())}.log"
    prompt = montar_prompt(item, project_path)
    token = TOKEN_PATH.read_text().strip()

    env = os.environ.copy()
    env["CLAUDE_CODE_OAUTH_TOKEN"] = token

    with open(log_path, "wb") as logfile:
        proc = subprocess.Popen(
            ["claude", "--agent", "planner", "-p", prompt,
             "--permission-mode", "auto",
             "--output-format", "stream-json", "--verbose",
             "--max-budget-usd", str(MAX_BUDGET_USD)],
            cwd=project_path,
            stdout=logfile, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            env=env, start_new_session=True,
        )
    return proc.pid, str(log_path)


def main():
    estado = carregar_estado()
    estado = reconciliar(estado)
    salvar_estado(estado)

    try:
        pendentes = listar_pendentes()
    except Exception as exc:
        print(f"erro ao listar pendentes: {exc}", file=sys.stderr)
        return 1

    if not pendentes:
        print("nenhuma notificacao pendente.")
        return 0

    for item in pendentes:
        notificacao_id = str(item["notificacao_id"])
        if notificacao_id in estado:
            print(f"[SKIP] notificacao #{item['notificacao_id']} ({item['projeto']}) ja tem processo em andamento (pid={estado[notificacao_id]['pid']}).")
            continue

        resultado = disparar(item)
        if resultado is None:
            continue
        pid, log_path = resultado

        estado[notificacao_id] = {
            "pid": pid,
            "log": log_path,
            "iniciado_em": datetime.now(timezone.utc).isoformat(),
            "tentativas": estado.get(notificacao_id, {}).get("tentativas", 0),
        }
        salvar_estado(estado)
        print(f"processo iniciado para notificacao #{item['notificacao_id']} ({item['projeto']}, pid={pid}), log={log_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
