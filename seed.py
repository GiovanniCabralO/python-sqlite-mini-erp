import sqlite3
import random
from datetime import datetime, timedelta

def popular_banco():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    print("Iniciando o plantio de dados (Seed)...")

    # 1. Criar Clientes Fictícios
    nomes = ["Ana Costa", "Carlos Dias", "Beatriz Souza", "Daniela Lima", "Eduardo Alves", 
             "Fernanda Silva", "Gabriel Santos", "Helena Oliveira", "Igor Pereira", "Julia Rodrigues"]
    clientes_ids = []
    
    for nome in nomes:
        # Gera um e-mail único com um número aleatório para evitar o erro do UNIQUE
        email = f"{nome.split()[0].lower()}_{random.randint(1000, 9999)}@email.com"
        try:
            cursor.execute("INSERT INTO clientes (nome, email) VALUES (?, ?)", (nome, email))
            clientes_ids.append(cursor.lastrowid)
        except sqlite3.IntegrityError:
            pass

    print(f"{len(clientes_ids)} Clientes criados.")

    # 2. Criar Produtos de Informática
    produtos = [
        ("Cadeira Gamer Ergonômica", 850.00, 150),
        ("Teclado Mecânico RGB", 320.00, 200),
        ("Mouse Gamer 10000 DPI", 150.00, 300),
        ("Monitor Ultrawide 29", 1200.00, 80),
        ("Headset 7.1 Surround", 250.00, 120),
        ("Webcam Full HD", 199.90, 90),
        ("Mousepad Gigante", 50.00, 400),
        ("Suporte Articulado para Monitor", 180.00, 60),
        ("SSD NVMe 1TB", 450.00, 100),
        ("Placa de Vídeo RTX 4060", 2100.00, 30)
    ]
    produtos_ids = []

    for nome, preco, estoque in produtos:
        cursor.execute("INSERT INTO produtos (nome, preco_atual, quantidade_estoque) VALUES (?, ?, ?)", (nome, preco, estoque))
        # Salvamos o ID e o Preço para usar nas vendas abaixo
        produtos_ids.append({"id": cursor.lastrowid, "preco": preco})

    print(f"{len(produtos)} Produtos criados.")

    # 3. Criar Vendas Aleatórias
    qtd_pedidos = 40
    itens_criados = 0

    for _ in range(qtd_pedidos):
        # Escolhe um cliente aleatório
        cliente_id = random.choice(clientes_ids)
        dias_atras = random.randint(0, 180)
        data_venda = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO pedidos (cliente_id, data_venda) VALUES (?, ?)", (cliente_id, data_venda))
        pedido_id = cursor.lastrowid

        # Decide comprar de 1 a 3 produtos diferentes neste pedido
        qtd_produtos_diferentes = random.randint(1, 3)
        produtos_comprados = random.sample(produtos_ids, qtd_produtos_diferentes)

        for prod in produtos_comprados:
            qtd_comprada = random.randint(1, 4) # Compra de 1 a 4 unidades de cada
            cursor.execute("""
                INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_vendido)
                VALUES (?, ?, ?, ?)
            """, (pedido_id, prod["id"], qtd_comprada, prod["preco"]))
            itens_criados += 1

    print(f"{qtd_pedidos} Pedidos gerados (com um total de {itens_criados} itens).")

    conn.commit()
    conn.close()
    print("Banco de dados populado com sucesso!")

if __name__ == "__main__":
    popular_banco()