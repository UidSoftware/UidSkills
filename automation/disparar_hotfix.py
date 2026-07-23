#!/usr/bin/env python3
"""
disparar_hotfix.py — dispara o Hotfix diretamente via Claude Code CLI
(`--agent hotfix`), sem depender do Claw Empire.

Le Manutencao pendentes no SystemD (via management command
`disparar_hotfix`) e roda uma sessao `claude --agent hotfix` em background
por processo, rastreando PID localmente em hotfix_processos.json.

A propria Manutencao (campos disparada_em/feito) e a fonte de verdade do
estado do "task" — nao existe quadro de tasks separado. O unico dado que
precisa viver fora do banco e efemero por natureza: o PID do processo em
execucao agora, guardado em hotfix_processos.json.

Idempotente e cron-safe. Duas fases a cada execucao:

  1. Reconciliacao: para cada manutencao com processo rastreado
     localmente, confere se o PID ainda esta vivo.
       - vivo e dentro do timeout        -> deixa rodando, nada a fazer.
       - vivo e passou do timeout        -> mata o processo (trava/loop
                                             infinito), conta como falha.
       - morto e Manutencao.feito=True   -> sucesso confirmado (a propria
                                             sessao rodou o --concluir no
                                             final), remove do rastreamento.
       - morto e Manutencao.feito=False  -> sessao terminou sem concluir;
                                             incrementa tentativas; se <
                                             MAX_TENTATIVAS, libera
                                             (--liberar) para nova tentativa
                                             no proximo ciclo; se nao,
                                             deixa travado e loga
                                             intervencao manual necessaria.

  2. Disparo: para cada Manutencao pendente (--list) que ainda nao tem
     processo rastreado, monta o prompt (mesmo envelope MODO MANUTENCAO
     BANCO que o Claw Empire usava) e dispara
     `claude --agent hotfix -p "..." --permission-mode auto`
     em background (setsid, log proprio, stdin fechado), marca
     disparada_em=now() via `--mark-dispatched`, e registra
     {pid, log, tentativas, iniciado_em} localmente.
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
ESTADO_PATH       = BASE_DIR / "hotfix_processos.json"
TENTATIVAS_PATH   = BASE_DIR / "hotfix_tentativas.json"
SYSTEMD_CONTAINER = "sytemd-backend-1"
TOKEN_PATH        = Path("/root/.claude_oauth_token")
LOG_DIR           = Path("/root/esteira-logs")

MAX_TENTATIVAS  = 3
TIMEOUT_MINUTOS = 120
MAX_BUDGET_USD  = 15


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


def carregar_tentativas():
    if not TENTATIVAS_PATH.exists():
        return {}
    try:
        return json.loads(TENTATIVAS_PATH.read_text())
    except json.JSONDecodeError:
        print(f"aviso: {TENTATIVAS_PATH} corrompido, recomecando do zero.", file=sys.stderr)
        return {}


def salvar_tentativas(tentativas):
    TENTATIVAS_PATH.write_text(json.dumps(tentativas, indent=2, ensure_ascii=False))


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


def status_manutencao(manutencao_id):
    resultado = subprocess.run(
        ["docker", "exec", SYSTEMD_CONTAINER, "python", "manage.py",
         "disparar_hotfix", "--status", str(manutencao_id)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(resultado.stdout)


def marcar_disparada(manutencao_id):
    subprocess.run(
        ["docker", "exec", SYSTEMD_CONTAINER, "python", "manage.py",
         "disparar_hotfix", "--mark-dispatched", str(manutencao_id)],
        capture_output=True, text=True, check=True,
    )


def liberar_manutencao(manutencao_id):
    subprocess.run(
        ["docker", "exec", SYSTEMD_CONTAINER, "python", "manage.py",
         "disparar_hotfix", "--liberar", str(manutencao_id)],
        capture_output=True, text=True, check=True,
    )


def listar_pendentes():
    resultado = subprocess.run(
        ["docker", "exec", SYSTEMD_CONTAINER, "python", "manage.py",
         "disparar_hotfix", "--list"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(resultado.stdout)


def reconciliar(estado, tentativas):
    """Duas contagens com ciclo de vida diferente: `estado` e efemero (um
    registro por PROCESSO em execucao agora — nasce ao disparar, morre ao
    reconciliar) enquanto `tentativas` e persistente por MANUTENCAO (teria
    que sobreviver a exatamente esse pop de `estado` pra o MAX_TENTATIVAS
    ter efeito — bug real ja confirmado em producao: 12 disparos automaticos
    em 24h pra mesma manutencao sem nunca desistir, porque o contador vivia
    dentro do dict que e sempre esvaziado aqui embaixo)."""
    remover_estado = []
    for manutencao_id, info in estado.items():
        pid = info["pid"]

        if processo_vivo(pid):
            iniciado = datetime.fromisoformat(info["iniciado_em"])
            elapsed_min = (datetime.now(timezone.utc) - iniciado).total_seconds() / 60
            if elapsed_min < TIMEOUT_MINUTOS:
                print(f"[RECONCILIA] manutencao #{manutencao_id} ainda rodando (pid={pid}, {elapsed_min:.0f}min).")
                continue
            print(f"[RECONCILIA] manutencao #{manutencao_id} passou do timeout ({TIMEOUT_MINUTOS}min) — encerrando pid={pid}.")
            matar_processo(pid)
            # cai direto no tratamento de falha abaixo, sem esperar o proximo ciclo

        else:
            try:
                status = status_manutencao(manutencao_id)
            except Exception as exc:
                print(f"[RECONCILIA] erro ao checar status da manutencao #{manutencao_id}: {exc} — mantendo em andamento.", file=sys.stderr)
                continue

            if not status.get("encontrada"):
                print(f"[RECONCILIA] manutencao #{manutencao_id} nao encontrada no banco — removendo do rastreamento.")
                remover_estado.append(manutencao_id)
                tentativas.pop(manutencao_id, None)
                continue

            if status.get("feito"):
                print(f"[RECONCILIA] manutencao #{manutencao_id} concluida com sucesso (pid={pid} encerrado).")
                remover_estado.append(manutencao_id)
                tentativas.pop(manutencao_id, None)
                continue

        tentativas[manutencao_id] = tentativas.get(manutencao_id, 0) + 1
        if tentativas[manutencao_id] < MAX_TENTATIVAS:
            liberar_manutencao(manutencao_id)
            print(f"[RECONCILIA] manutencao #{manutencao_id} nao concluiu — liberada para nova tentativa ({tentativas[manutencao_id]}/{MAX_TENTATIVAS}). Log: {info.get('log')}")
        else:
            print(f"[RECONCILIA] manutencao #{manutencao_id} excedeu {MAX_TENTATIVAS} tentativas — NAO liberada, intervencao manual necessaria (use Liberar/Rodar no terminal em Notificacoes). Log: {info.get('log')}")
            tentativas.pop(manutencao_id, None)
        remover_estado.append(manutencao_id)

    for manutencao_id in remover_estado:
        estado.pop(manutencao_id, None)

    return estado, tentativas


def montar_prompt(item):
    return f"""MODO MANUTENCAO BANCO
MANUTENCAO_ID: {item['id']}
Sistema: {item['os_titulo']} (OS #{item['os_id']})
Cliente: {item['os_cliente']}
Caminho: {item['caminho']}

Tarefa:
{item['descricao']}

CLAUDE.md: {item['caminho']}/CLAUDE.md

INSTRUCAO FINAL (somente apos Sentinel validar de verdade — subir containers,
rodar migrate, testar endpoints reais — e Pilot confirmar deploy real em
producao):
Marcar manutencao como concluida via Bash:
  docker exec sytemd-backend-1 python manage.py disparar_hotfix --concluir {item['id']}
"""


def disparar(item):
    caminho = item["caminho"]
    if not os.path.isdir(caminho):
        print(f"[SKIP] manutencao #{item['id']} — caminho nao existe: {caminho}", file=sys.stderr)
        return None

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"hotfix-manutencao-{item['id']}-{int(time.time())}.log"
    prompt = montar_prompt(item)
    token = TOKEN_PATH.read_text().strip()

    env = os.environ.copy()
    env["CLAUDE_CODE_OAUTH_TOKEN"] = token

    with open(log_path, "wb") as logfile:
        proc = subprocess.Popen(
            ["claude", "--agent", "hotfix", "-p", prompt,
             "--permission-mode", "auto",
             "--output-format", "stream-json", "--verbose",
             "--max-budget-usd", str(MAX_BUDGET_USD)],
            cwd=caminho,
            stdout=logfile, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            env=env, start_new_session=True,
        )
    return proc.pid, str(log_path)


def main():
    estado = carregar_estado()
    tentativas = carregar_tentativas()
    estado, tentativas = reconciliar(estado, tentativas)
    salvar_estado(estado)
    salvar_tentativas(tentativas)

    try:
        pendentes = listar_pendentes()
    except Exception as exc:
        print(f"erro ao listar pendentes: {exc}", file=sys.stderr)
        return 1

    if not pendentes:
        print("nenhuma manutencao pendente.")
        return 0

    for item in pendentes:
        manutencao_id = str(item["id"])
        if manutencao_id in estado:
            print(f"[SKIP] manutencao #{item['id']} ja tem processo em andamento (pid={estado[manutencao_id]['pid']}).")
            continue

        resultado = disparar(item)
        if resultado is None:
            continue
        pid, log_path = resultado

        try:
            marcar_disparada(item["id"])
        except Exception as exc:
            print(f"[AVISO] processo pid={pid} iniciado para manutencao #{item['id']} mas falhou ao marcar disparada: {exc}", file=sys.stderr)

        estado[manutencao_id] = {
            "pid": pid,
            "log": log_path,
            "iniciado_em": datetime.now(timezone.utc).isoformat(),
        }
        salvar_estado(estado)
        print(f"processo iniciado para manutencao #{item['id']} (pid={pid}), log={log_path}, tentativa={tentativas.get(manutencao_id, 0) + 1}/{MAX_TENTATIVAS}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
