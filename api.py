import sqlite3
from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__, url_prefix="/api")


def get_db():
    conn = sqlite3.connect("mini_erp.db")
    conn.row_factory = sqlite3.Row
    return conn


# /api/kpis
# KPIs gerenciais consolidados em uma única chamada.
# Usado no Power BI como cartões (Card visuals).

@api_bp.route("/kpis")
def kpis():
    conn = get_db()

    resultado = conn.execute("""
        WITH base AS (
            SELECT
                ip.pedido_id,
                ip.quantidade * ip.preco_vendido AS valor_item
            FROM itens_pedido ip
        ),
        totais AS (
            SELECT
                COUNT(DISTINCT pedido_id)          AS total_pedidos,
                SUM(valor_item)                    AS faturamento_total,
                ROUND(SUM(valor_item) /
                      COUNT(DISTINCT pedido_id), 2) AS ticket_medio
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
            t.total_pedidos,
            ROUND(t.faturamento_total, 2) AS faturamento_total,
            t.ticket_medio,
            ca.total_clientes_ativos,
            tp.produto_mais_vendido,
            ic.produtos_estoque_critico
        FROM totais t, clientes_ativos ca, top_produto tp, itens_criticos ic
    """).fetchone()

    conn.close()
    return jsonify(dict(resultado))


# /api/vendas_por_mes
# Faturamento mensal agregado para série temporal.
# Usado no Power BI como gráfico de linha ou barras.

@api_bp.route("/vendas_por_mes")
def vendas_por_mes():
    conn = get_db()

    linhas = conn.execute("""
        SELECT
            strftime('%Y-%m', p.data_venda)        AS mes,
            COUNT(DISTINCT p.id)                   AS total_pedidos,
            SUM(ip.quantidade * ip.preco_vendido)  AS faturamento,
            ROUND(
                SUM(ip.quantidade * ip.preco_vendido) /
                COUNT(DISTINCT p.id), 2
            )                                      AS ticket_medio
        FROM pedidos p
        JOIN itens_pedido ip ON ip.pedido_id = p.id
        GROUP BY mes
        ORDER BY mes
    """).fetchall()

    conn.close()
    return jsonify([dict(r) for r in linhas])


# /api/ranking_produtos
# Produtos ordenados por receita total gerada.
# Usado no Power BI como gráfico de barras horizontal.

@api_bp.route("/ranking_produtos")
def ranking_produtos():
    conn = get_db()

    linhas = conn.execute("""
        SELECT
            pr.nome                                        AS produto,
            SUM(ip.quantidade)                             AS unidades_vendidas,
            ROUND(SUM(ip.quantidade * ip.preco_vendido), 2) AS receita_total,
            pr.quantidade_estoque                          AS estoque_atual,
            CASE
                WHEN pr.quantidade_estoque = 0  THEN 'Sem estoque'
                WHEN pr.quantidade_estoque < 5  THEN 'Crítico'
                WHEN pr.quantidade_estoque < 15 THEN 'Baixo'
                ELSE 'Normal'
            END                                            AS status_estoque
        FROM itens_pedido ip
        JOIN produtos pr ON ip.produto_id = pr.id
        GROUP BY pr.id
        ORDER BY receita_total DESC
    """).fetchall()

    conn.close()
    return jsonify([dict(r) for r in linhas])


# /api/ranking_clientes
# Clientes ordenados por valor total gasto.
# Usado no Power BI como tabela ou gráfico de barras.

@api_bp.route("/ranking_clientes")
def ranking_clientes():
    conn = get_db()

    linhas = conn.execute("""
        SELECT
            ROW_NUMBER() OVER (ORDER BY SUM(ip.quantidade * ip.preco_vendido) DESC)
                                                           AS posicao,
            c.nome                                         AS cliente,
            c.email,
            COUNT(DISTINCT p.id)                           AS total_pedidos,
            SUM(ip.quantidade)                             AS total_itens,
            ROUND(SUM(ip.quantidade * ip.preco_vendido), 2) AS total_gasto,
            ROUND(
                SUM(ip.quantidade * ip.preco_vendido) /
                COUNT(DISTINCT p.id), 2
            )                                              AS ticket_medio
        FROM itens_pedido ip
        JOIN pedidos p      ON ip.pedido_id  = p.id
        JOIN clientes c     ON p.cliente_id  = c.id
        GROUP BY c.id
        ORDER BY total_gasto DESC
    """).fetchall()

    conn.close()
    return jsonify([dict(r) for r in linhas])


# /api/estoque
# Posição atual do estoque com classificação de status.
# Usado no Power BI como tabela com formatação condicional.

@api_bp.route("/estoque")
def estoque():
    conn = get_db()

    linhas = conn.execute("""
        SELECT
            pr.nome                                        AS produto,
            pr.preco_atual,
            pr.quantidade_estoque,
            COALESCE(SUM(ip.quantidade), 0)                AS total_vendido,
            CASE
                WHEN pr.quantidade_estoque = 0  THEN 'Sem estoque'
                WHEN pr.quantidade_estoque < 5  THEN 'Crítico'
                WHEN pr.quantidade_estoque < 15 THEN 'Baixo'
                ELSE 'Normal'
            END                                            AS status_estoque
        FROM produtos pr
        LEFT JOIN itens_pedido ip ON ip.produto_id = pr.id
        GROUP BY pr.id
        ORDER BY pr.quantidade_estoque ASC
    """).fetchall()

    conn.close()
    return jsonify([dict(r) for r in linhas])
