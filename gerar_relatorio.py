import sqlite3

def emitir_relatorio():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    sql_view = """
    CREATE VIEW vw_relatorio_vendas AS
    SELECT
        pedidos.id AS numero_pedido,
        clientes.nome AS nome_cliente,
        produtos.nome AS nome_produto,
        itens_pedido.quantidade,
        itens_pedido.preco_vendido,
        (itens_pedido.quantidade * itens_pedido.preco_vendido) AS valor_total_item,
        pedidos.data_venda
    FROM itens_pedido
    JOIN pedidos ON itens_pedido.pedido_id = pedidos.id
    JOIN clientes ON pedidos.cliente_id = clientes.id
    JOIN produtos ON itens_pedido.produto_id = produtos.id;
    """
    
    cursor.execute(sql_view)
    
    cursor.execute("SELECT * FROM vw_relatorio_vendas")
    vendas = cursor.fetchall()

    print("📊 --- RELATÓRIO GERAL DE VENDAS --- 📊\n")
    
    for venda in vendas:
        print(f"🛍️  Pedido #{venda[0]} | Data: {venda[6]}")
        print(f"👤 Cliente: {venda[1]}")
        print(f"📦 Produto: {venda[2]} (Qtd: {venda[3]})")
        print(f"💰 Valor Unitário: R$ {venda[4]:.2f}")
        print(f"💵 Total deste item: R$ {venda[5]:.2f}")
        print("-" * 40)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    emitir_relatorio()