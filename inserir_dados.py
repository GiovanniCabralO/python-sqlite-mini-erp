import sqlite3

def inserir_dados_iniciais():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    sql_cliente = "INSERT INTO clientes (nome, email) VALUES (?, ?)"
    dados_cliente = ("Joao Silva", "joao@gmail.com")
    cursor.execute(sql_cliente, dados_cliente)

    sql_produto = "INSERT INTO produtos (nome, preco_atual, quantidade_estoque) VALUES (?, ?, ?)"
    dados_produtos = [
        ("Monitor Gamer 24p", 1200.00, 10),
        ("Teclado Mêcanico", 350.00, 15),
        ("Mouse Sem Fio", 120.00, 20)
    ]
    cursor.executemany(sql_produto, dados_produtos)

    conn.commit()
    conn.close()

    print("Cliente e produtos cadastrados.")

if __name__ == "__main__":
    inserir_dados_iniciais()