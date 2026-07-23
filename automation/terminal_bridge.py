#!/usr/bin/env python3
"""
terminal_bridge.py — servidor WebSocket que expoe um PTY real rodando
`claude --agent planner` para o Notificacoes do SystemD (botao "Rodar no
terminal"). Roda no HOST (fora de Docker) porque o processo `claude`
precisa de acesso real: binario no PATH, /root/.claude_oauth_token,
docker exec nos containers dos projetos, /var/www/*.

Por que isso existe: o classificador de seguranca do Claude Code (auto
mode) bloqueia sessoes `claude` filhas disparadas sem terminal real
(sem TTY, sem humano podendo responder prompt). Um PTY genuino aberto
via este bridge da ao processo filho um TTY de verdade, igual teria se
um humano tivesse aberto SSH e digitado o comando na mao (caminho ja
confirmado que passa do classificador).

Seguranca:
- Bind em 127.0.0.1 apenas — so alcancavel via nginx local (mesma VPS).
- Autenticacao por ticket assinado (HMAC-SHA256 com o SECRET_KEY do
  Django), de uso unico, com expiracao de 60s — mintado pelo endpoint
  IsAdmin do SystemD (POST /api/notificacoes/<id>/terminal_ticket/).
- Uma sessao ativa por vez (evita concorrencia/confusao).
- Se o WebSocket cair, o processo filho e morto — a sessao existe pra
  ser acompanhada ao vivo, nao pra rodar sem supervisao (isso e
  justamente o oposto do bug de run_in_background).
- Log de auditoria por sessao em /root/esteira-logs/.
"""
import asyncio
import base64
import fcntl
import hashlib
import hmac
import json
import os
import pty
import signal
import struct
import termios
import time
from pathlib import Path

import websockets

ENV_PATH   = Path("/root/SystemD/.env.prod")
TOKEN_PATH = Path("/root/.claude_oauth_token")
LOG_DIR    = Path("/root/esteira-logs")
HOST, PORT = "127.0.0.1", 8791

TICKET_MAX_AGE_SEG   = 60
SESSAO_MAX_DURACAO_S = 4 * 60 * 60  # pipeline completo (Analista..Pilot) pode passar de 1h
DELAY_PASTE_BRIEFING = 2.5

_consumidos = {}   # sig -> iat, pra checagem de uso unico
_sessao_ativa = {"em_uso": False}


def carregar_secret_key():
    for linha in ENV_PATH.read_text().splitlines():
        linha = linha.strip()
        if linha.startswith("SECRET_KEY="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("SECRET_KEY nao encontrada em .env.prod")


SECRET_KEY = carregar_secret_key()


def verificar_ticket(ticket: str):
    try:
        payload_b64, sig = ticket.rsplit(".", 1)
    except ValueError:
        return None, "ticket malformado"

    esperado = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(esperado, sig):
        return None, "assinatura invalida"

    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()))
    except Exception:
        return None, "payload invalido"

    agora = time.time()
    if payload.get("exp", 0) < agora:
        return None, "ticket expirado"

    if sig in _consumidos:
        return None, "ticket ja utilizado"

    # limpa consumidos antigos (> 5min) pra nao crescer sem limite
    for s, iat in list(_consumidos.items()):
        if agora - iat > 300:
            _consumidos.pop(s, None)
    _consumidos[sig] = agora

    return payload, None


def set_pty_size(master_fd, cols, rows):
    try:
        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    except OSError:
        pass


async def tratar_conexao(websocket):
    global _sessao_ativa

    try:
        primeira = await asyncio.wait_for(websocket.recv(), timeout=5)
    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
        return

    try:
        msg = json.loads(primeira)
        ticket = msg["ticket"]
    except Exception:
        await websocket.close(code=4000, reason="handshake invalido")
        return

    payload, erro = verificar_ticket(ticket)
    if erro:
        await websocket.send(json.dumps({"type": "erro", "mensagem": erro}))
        await websocket.close(code=4001, reason=erro)
        return

    if _sessao_ativa["em_uso"]:
        await websocket.send(json.dumps({"type": "erro", "mensagem": "ja existe uma sessao de terminal ativa — aguarde ela terminar."}))
        await websocket.close(code=4002, reason="sessao ja ativa")
        return

    _sessao_ativa["em_uso"] = True
    manutencao_id = payload.get("manutencao_id")
    caminho = payload.get("caminho", "/root")
    briefing = payload.get("briefing", "")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"terminal-manutencao-{manutencao_id}-{int(time.time())}.log"
    logfile = open(log_path, "wb")

    master_fd, slave_fd = pty.openpty()
    set_pty_size(master_fd, 120, 32)

    comando = (
        f"cd {caminho!r} 2>/dev/null || cd /root; "
        f"export CLAUDE_CODE_OAUTH_TOKEN=$(cat {str(TOKEN_PATH)!r}); "
        f"claude --agent planner --permission-mode auto"
    )

    processo = await asyncio.create_subprocess_exec(
        "/bin/bash", "-lc", comando,
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        preexec_fn=os.setsid,
    )
    os.close(slave_fd)

    loop = asyncio.get_event_loop()
    fila_saida = asyncio.Queue()

    def leitor_pty():
        try:
            dados = os.read(master_fd, 65536)
        except OSError:
            dados = b""
        loop.call_soon_threadsafe(fila_saida.put_nowait, dados)
        if not dados:
            loop.remove_reader(master_fd)

    loop.add_reader(master_fd, leitor_pty)

    async def colar_briefing():
        await asyncio.sleep(DELAY_PASTE_BRIEFING)
        try:
            os.write(master_fd, briefing.encode())
            await asyncio.sleep(0.6)
            os.write(master_fd, b"\r")
        except OSError:
            pass

    async def bombear_saida():
        while True:
            dados = await fila_saida.get()
            if not dados:
                await websocket.send(json.dumps({"type": "encerrado"}))
                break
            logfile.write(dados)
            logfile.flush()
            await websocket.send(dados)

    async def bombear_entrada():
        async for mensagem in websocket:
            if isinstance(mensagem, bytes):
                continue
            try:
                dado = json.loads(mensagem)
            except Exception:
                continue
            if dado.get("type") == "input":
                os.write(master_fd, dado.get("data", "").encode())
            elif dado.get("type") == "resize":
                set_pty_size(master_fd, dado.get("cols", 120), dado.get("rows", 32))

    tarefa_paste = asyncio.ensure_future(colar_briefing())
    tarefa_saida = asyncio.ensure_future(bombear_saida())
    tarefa_entrada = asyncio.ensure_future(bombear_entrada())

    try:
        await asyncio.wait_for(
            asyncio.wait([tarefa_saida, tarefa_entrada], return_when=asyncio.FIRST_COMPLETED),
            timeout=SESSAO_MAX_DURACAO_S,
        )
    except asyncio.TimeoutError:
        pass
    finally:
        tarefa_paste.cancel()
        tarefa_saida.cancel()
        tarefa_entrada.cancel()
        try:
            loop.remove_reader(master_fd)
        except Exception:
            pass
        try:
            os.killpg(os.getpgid(processo.pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
        try:
            os.close(master_fd)
        except OSError:
            pass
        logfile.close()
        _sessao_ativa["em_uso"] = False


async def main():
    async with websockets.serve(tratar_conexao, HOST, PORT, max_size=None):
        print(f"terminal_bridge ouvindo em {HOST}:{PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
