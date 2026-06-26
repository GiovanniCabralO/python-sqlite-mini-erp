import sqlite3


def criar_banco_dados():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    # ─────────────────────────────────────────────
    # TABELAS
    # ─────────────────────────────────────────────
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS clientes (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        nome  TEXT NOT NULL,
        email TEXT UNIQUE
    );

    CREATE TABLE IF NOT EXISTS produtos (
        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        nome               TEXT NOT NULL,
        preco_atual        REAL NOT NULL,
        quantidade_estoque INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS pedidos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id  INTEGER NOT NULL,
        data_venda  DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cliente_id) REFERENCES clientes (id)
    );

    CREATE TABLE IF NOT EXISTS itens_pedido (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id     INTEGER NOT NULL,
        produto_id    INTEGER NOT NULL,
        quantidade    INTEGER NOT NULL,
        preco_vendido REAL NOT NULL,
        FOREIGN KEY (pedido_id)  REFERENCES pedidos  (id),
        FOREIGN KEY (produto_id) REFERENCES produtos (id)
    );

    -- ─────────────────────────────────────────────
    -- TRIGGER
    -- Desconta o estoque automaticamente após cada
    -- item inserido em itens_pedido.
    -- ─────────────────────────────────────────────
    CREATE TRIGGER IF NOT EXISTS atualiza_estoque
    AFTER INSERT ON itens_pedido
    BEGIN
        UPDATE produtos
        SET quantidade_estoque = quantidade_estoque - NEW.quantidade
        WHERE id = NEW.produto_id;
    END;

    -- ─────────────────────────────────────────────
    -- VIEW 1: vw_relatorio_vendas
    -- Linha por item vendido com dados desnormalizados.
    -- Usada no dashboard Flask e na exportação Excel.
    -- ─────────────────────────────────────────────
    CREATE VIEW IF NOT EXISTS vw_relatorio_vendas AS
    SELECT
        p.id                                       AS pedido_id,
        c.nome                                     AS nome_cliente,
        c.email                                    AS email_cliente,
        pr.nome                                    AS nome_produto,
        ip.quantidade,
        ip.preco_vendido,
        ROUND(ip.quantidade * ip.preco_vendido, 2) AS valor_total_item,
        DATE(p.data_venda)                         AS data_venda
    FROM itens_pedido ip
    JOIN pedidos  p  ON ip.pedido_id  = p.id
    JOIN clientes c  ON p.cliente_id  = c.id
    JOIN produtos pr ON ip.produto_id = pr.id;

    -- ─────────────────────────────────────────────
    -- VIEW 2: vw_vendas_mensais
    -- Faturamento e volume agregados por mês.
    -- Usada para série temporal no Power BI.
    -- ─────────────────────────────────────────────
    CREATE VIEW IF NOT EXISTS vw_vendas_mensais AS
    SELECT
        strftime('%Y-%m', p.data_venda)            AS mes,
        COUNT(DISTINCT p.id)                       AS total_pedidos,
        SUM(ip.quantidade * ip.preco_vendido)      AS faturamento,
        ROUND(
            SUM(ip.quantidade * ip.preco_vendido) /
            COUNT(DISTINCT p.id), 2
        )                                          AS ticket_medio
    FROM pedidos p
    JOIN itens_pedido ip ON ip.pedido_id = p.id
    GROUP BY mes
    ORDER BY mes;

    -- ─────────────────────────────────────────────
    -- VIEW 3: vw_kpis_gerenciais
    -- Métricas consolidadas para cartões do Power BI.
    -- Combina CTEs em uma única linha de resultado.
    -- ─────────────────────────────────────────────
    CREATE VIEW IF NOT EXISTS vw_kpis_gerenciais AS
    WITH base AS (
        SELECT
            ip.pedido_id,
            ip.quantidade * ip.preco_vendido AS valor_item
        FROM itens_pedido ip
    ),
    totais AS (
        SELECT
            COUNT(DISTINCT pedido_id)                       AS total_pedidos,
            ROUND(SUM(valor_item), 2)                       AS faturamento_total,
            ROUND(SUM(valor_item) / COUNT(DISTINCT pedido_id), 2) AS ticket_medio
        FROM base
    ),
    clientes_ativos AS (
        SELECT COUNT(DISTINCT cliente_id) AS total_clientes_ativos
        FROM pedidos
    ),
    top_produto AS (
        SELECT pr.nome AS produto_mais_vendido
        FROM itens_pedido ip
        JOIN produtos pr ON ip.produto_id = pr.id
        GROUP BY ip.produto_id
        ORDER BY SUM(ip.quantidade) DESC
        LIMIT 1
    ),
    itens_criticos AS (
        SELECT COUNT(*) AS produtos_estoque_critico
        FROM produtos
        WHERE quantidade_estoque < 5
    )
    SELECT
        t.faturamento_total,
        t.total_pedidos,
        t.ticket_medio,
        ca.total_clientes_ativos,
        tp.produto_mais_vendido,
        ic.produtos_estoque_critico
    FROM totais t, clientes_ativos ca, top_produto tp, itens_criticos ic;

    -- ─────────────────────────────────────────────
    -- VIEW 4: vw_ranking_produtos
    -- Produtos ranqueados por receita com status de estoque.
    -- CASE WHEN categoriza criticidade do estoque.
    -- ─────────────────────────────────────────────
    CREATE VIEW IF NOT EXISTS vw_ranking_produtos AS
    SELECT
        pr.nome                                         AS produto,
        SUM(ip.quantidade)                              AS unidades_vendidas,
        ROUND(SUM(ip.quantidade * ip.preco_vendido), 2) AS receita_total,
        pr.quantidade_estoque                           AS estoque_atual,
        CASE
            WHEN pr.quantidade_estoque = 0  THEN 'Sem estoque'
            WHEN pr.quantidade_estoque < 5  THEN 'Crítico'
            WHEN pr.quantidade_estoque < 15 THEN 'Baixo'
            ELSE 'Normal'
        END                                             AS status_estoque
    FROM itens_pedido ip
    JOIN produtos pr ON ip.produto_id = pr.id
    GROUP BY pr.id
    ORDER BY receita_total DESC;
    """)

    conn.commit()
    conn.close()
    print("Banco criado: 4 tabelas, 1 trigger, 4 views.")


if __name__ == "__main__":
    criar_banco_dados()
