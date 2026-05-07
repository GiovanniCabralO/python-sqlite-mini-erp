import sqlite3

def registrar_venda():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO pedidos (cliente_id) VALUES (?)", (1,))

        pedido_id = cursor.lastrowid
        print(f"Pedido {pedido_id} aberto com sucesso!")

        item_1 = (pedido_id, 1, 2, 1200.00)

        cursor.execute("""
            INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_vendido)
            VALUES (?, ?, ?, ?)
        """, item_1)
        print("  - 2x Monitores adicionados ao pedido.")

        conn.commit()
        cursor.execute("SELECT nome, quantidade_estoque FROM produtos WHERE id = 1")
        produto = cursor.fetchone()

        print("Resultado do TRIGGER:")
        print(f"  Novo estoque do '{produto[0]}': {produto[1]} unidades restantes.")

    except sqlite3.Error as e:
        print(f"   Ocorreu um erro no banco de dados: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    registrar_venda()
        
