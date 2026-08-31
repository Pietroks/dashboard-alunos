import sqlite3
import hashlib
from typing import Optional

DB_NAME = "usuarios.db"

def hash_senha(senha: str) -> str:
    """Gera um hash SHA-256 seguro da senha."""
    return hashlib.sha256(senha.encode()).hexdigest()

def inicializar_banco():
    """Cria a tabela de usuários e um usuário administrador inicial se não existir."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nome TEXT NOT NULL
        )
    """)
    # Cria usuário padrão caso a tabela esteja vazia
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO usuarios (usuario, senha, nome) VALUES (?, ?, ?)",
            ("admin", hash_senha("admin123"), "Administrador")
        )
    conn.commit()
    conn.close()

def verificar_credenciais(usuario: str, senha: str) -> Optional[str]:
    """Retorna o nome do usuário se as credenciais estiverem corretas, ou None."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nome FROM usuarios WHERE usuario = ? AND senha = ?",
        (usuario.strip(), hash_senha(senha))
    )
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None