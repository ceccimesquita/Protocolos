import socket
import sqlite3

HOST = "0.0.0.0"   # escuta em todas as interfaces
PORT = 50000         # porta de serviço
DB_PATH = "usuarios.db"

# --------------------------- BANCO DE DADOS ---------------------------

def inicializar_banco():
    """Cria a tabela `usuarios` se não existir."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def contar_usuarios():
    """Retorna o total de usuários."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM usuarios")
    total = cur.fetchone()[0]
    conn.close()
    return total


def listar_usuarios():
    """Retorna lista com todos os nomes."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT nome FROM usuarios ORDER BY id")
    nomes = [linha[0] for linha in cur.fetchall()]
    conn.close()
    return nomes


def escrever_usuario(nome):
    """Insere um novo nome na tabela."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO usuarios (nome) VALUES (?)", (nome,))
    conn.commit()
    conn.close()

# --------------------------- PROTOCOLO ---------------------------

def executar_comando(cmd):
    """Processa texto recebido do mestre e devolve resposta."""
    partes = cmd.strip().split(maxsplit=2)
    if not partes:
        return "Comando vazio."

    op = partes[0].lower()

    # READ
    if op == "read":
        if len(partes) < 2:
            return "Uso: read count | read all"
        sub = partes[1].lower()
        if sub == "count":
            return f"Total de usuários: {contar_usuarios()}"
        if sub == "all":
            nomes = listar_usuarios()
            return "Usuários:\n" + "\n".join(nomes) if nomes else "Nenhum usuário cadastrado."
        return "Subcomando READ desconhecido (use count ou all)."

    # WRITE
    if op == "write":
        if len(partes) < 2:
            return "Nome de usuário não especificado."
        nome = partes[1]
        escrever_usuario(nome)
        return f'Usuário "{nome}" cadastrado com sucesso!'

    # HELP
    if op == "help":
        return (
            "Comandos disponíveis:\n"
            "  read count         → quantidade de registros\n"
            "  read all           → lista todos os nomes\n"
            "  write <nome>       → cadastra novo usuário\n"
            "  help               → esta ajuda"
        )

    return "Comando desconhecido. Use 'help' para ver as opções."

# --------------------------- SERVIDOR ---------------------------

def iniciar_servidor(host, port):
    """Fica ouvindo para sempre, atendendo conexões sequenciais do mestre."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen()
        print(f"Slave ouvindo em {host}:{port} …")

        while True:  # mantém o servidor vivo mesmo após desconexões
            conn, addr = srv.accept()
            print("Conectado a:", addr)
            with conn:
                while True:
                    dados = conn.recv(1024)
                    if not dados:
                        print("Cliente desconectou.")
                        break

                    cmd = dados.decode()
                    print("Recebido:", cmd)

                    resposta = executar_comando(cmd)
                    conn.sendall(resposta.encode())

# --------------------------- MAIN ---------------------------

inicializar_banco()
iniciar_servidor(HOST, PORT)
