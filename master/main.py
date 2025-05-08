#!/usr/bin/env python3

import json
import socket
import sys
import time
from pathlib import Path

CONFIG_ARQUIVO = "config.json"

def carregar_config():
    """Lê o arquivo config.json e devolve um dicionário."""
    caminho = Path(__file__).with_name(CONFIG_ARQUIVO)
    if not caminho.exists():
        print(f"Erro: {CONFIG_ARQUIVO} não encontrado.")
        sys.exit(1)
    try:
        with open(caminho, "r", encoding="utf‑8") as f:
            return json.load(f)
    except Exception as e:
        print("Erro ao ler config:", e)
        sys.exit(1)


def obter_slave(config, slave_id):
    """Retorna (ip, porta) para o id desejado."""
    if slave_id not in config:
        print(f"Erro: slave '{slave_id}' não cadastrado.")
        sys.exit(1)
    dados = config[slave_id]
    return dados["ip"], dados["porta"]


def conectar(ip, porta):
    """Abre um socket TCP para o IP/porta e devolve o objeto socket."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, porta))
        return s
    except Exception as e:
        print(f"Erro ao conectar em {ip}:{porta} ->", e)
        sys.exit(1)


def executar_comando(sock, mensagem):
    """Envia mensagem e devolve resposta (já decodificada)."""
    try:
        sock.sendall((mensagem + "\n").encode())
        resposta = sock.recv(4096).decode().strip()
        return resposta
    except Exception as e:
        print("Erro na comunicação:", e)
        sys.exit(1)

# ---------------- Implementação dos comandos ----------------

def cmd_write(sock, argumentos):
    if not argumentos:
        print("Uso: write <pares>")
        return
    msg = "WRITE " + " ".join(argumentos)
    resposta = executar_comando(sock, msg)
    print(resposta)


def cmd_read(sock, argumentos):
    if len(argumentos) != 1:
        print("Uso: read <chave>")
        return
    msg = f"READ {argumentos[0]}"
    resposta = executar_comando(sock, msg)
    print(resposta)


def cmd_readloop(sock, argumentos):
    if len(argumentos) != 3:
        print("Uso: readloop <chave> <n> <intervalo_em_segundos>")
        return
    chave, n_str, intervalo_str = argumentos
    try:
        n = int(n_str)
        intervalo = float(intervalo_str)
    except ValueError:
        print("n e intervalo devem ser números.")
        return
    for i in range(n):
        resposta = executar_comando(sock, f"READ {chave}")
        print(f"{i+1}/{n}: {resposta}")
        if i != n - 1:
            time.sleep(intervalo)

def cmd_help(sock, _):
    resposta = executar_comando(sock, "HELP")
    print(resposta)

def main():
    if len(sys.argv) < 3:
        print("Uso: conductor.py <id_slave> <comando> [argumentos]")
        sys.exit(1)

    slave_id = sys.argv[1]
    comando = sys.argv[2].lower()
    argumentos = sys.argv[3:]

    config = carregar_config()
    ip, porta = obter_slave(config, slave_id)

    with conectar(ip, porta) as sock:
        if comando == "write":
            cmd_write(sock, argumentos)
        elif comando == "read":
            cmd_read(sock, argumentos)
        elif comando == "readloop":
            cmd_readloop(sock, argumentos)
        elif comando == "help":
            cmd_help(sock, argumentos)
        else:
            print(f"Comando desconhecido: {comando}")

if __name__ == "__main__":
    main()