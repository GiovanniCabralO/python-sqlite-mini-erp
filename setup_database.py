import sqlite3

def criar_banco_dados():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    script_sql = """
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE
    );

    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco_atual REAL NOT NULL,
        quantidade_estoque INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        data_venda DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cliente_id) REFERENCES clientes (id)
    );

    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        preco_vendido REAL NOT NULL,
        FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
        FOREIGN KEY (produto_id) REFERENCES produtos (id)
    );

    CREATE TRIGGER IF NOT EXISTS atualiza_estoque
    AFTER INSERT ON itens_pedido
    BEGIN
        UPDATE produtos
        SET quantidade_estoque = quantidade_estoque - NEW.quantidade
        WHERE id = NEW.produto_id;
    END;
    """

    cursor.executescript(script_sql)
    conn.commit()
    conn.close()
    print("Banco de dados 'mini_erp.db' e tabelas criados com sucesso!")

if __name__ == "__main__":
    criar_banco_dados()