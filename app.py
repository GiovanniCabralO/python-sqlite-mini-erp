from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from dotenv import load_dotenv
from api import api_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Rotas de API JSON para integração com Power BI via Web connector
app.register_blueprint(api_bp)

# Rota 1: Dashboard
@app.route('/')
def dashboard():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()
    
    filtro_cliente = request.args.get('cliente')
    filtro_produto = request.args.get('produto')
    filtro_data = request.args.get('data')
    
    query_vendas = "SELECT * FROM vw_relatorio_vendas WHERE 1=1"
    parametros = []
    
    if filtro_cliente:
        query_vendas += " AND nome_cliente = ?"
        parametros.append(filtro_cliente)
        
    if filtro_produto:
        query_vendas += " AND nome_produto = ?"
        parametros.append(filtro_produto)

    if filtro_data:
        query_vendas += " AND data_venda = ?"
        parametros.append(filtro_data)
        
    cursor.execute(query_vendas, parametros)
    dados_vendas = cursor.fetchall()

    cursor.execute("SELECT DISTINCT nome_cliente FROM vw_relatorio_vendas ORDER BY nome_cliente")
    lista_clientes = [linha[0] for linha in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT nome_produto FROM vw_relatorio_vendas ORDER BY nome_produto")
    lista_produtos = [linha[0] for linha in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT data_venda FROM vw_relatorio_vendas ORDER BY data_venda DESC")
    lista_datas = [linha[0] for linha in cursor.fetchall()]

    query_ranking = """
        SELECT c.nome, SUM(ip.quantidade * ip.preco_vendido) as total_comprado
        FROM itens_pedido ip
        JOIN pedidos p ON ip.pedido_id = p.id
        JOIN clientes c ON p.cliente_id = c.id
        GROUP BY c.nome
        ORDER BY total_comprado DESC
        LIMIT 6;
    """
    cursor.execute(query_ranking)
    ranking_clientes = cursor.fetchall()

    cursor.execute("SELECT nome, quantidade_estoque FROM produtos ORDER BY quantidade_estoque ASC")
    resumo_estoque = cursor.fetchall()
    
    conn.close()
    
    return render_template(
        "index.html", 
        relatorio_vendas=dados_vendas, 
        ranking=ranking_clientes, 
        estoque=resumo_estoque,
        lista_clientes=lista_clientes,
        lista_produtos=lista_produtos,
        lista_datas=lista_datas
    )

# Rota 2: Tela de Nova Venda
@app.route('/nova_venda')
def nova_venda():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome FROM clientes ORDER BY nome")
    clientes = cursor.fetchall()
    
    cursor.execute("SELECT id, nome, preco_atual FROM produtos WHERE quantidade_estoque > 0 ORDER BY nome")
    produtos = cursor.fetchall()
    
    conn.close()
    
    carrinho = session.get('carrinho', [])
    total_carrinho = sum(item['preco'] * item['quantidade'] for item in carrinho)
    
    return render_template("nova_venda.html", clientes=clientes, produtos=produtos, carrinho=carrinho, total=total_carrinho)

# Rota 2.1: Adicionar item ao Carrinho
@app.route('/adicionar_carrinho', methods=['POST'])
def adicionar_carrinho():
    cliente_id = request.form.get('cliente_id')
    produto_id = request.form.get('produto_id')
    quantidade = int(request.form.get('quantidade'))
    
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nome, preco_atual FROM produtos WHERE id = ?", (produto_id,))
    produto = cursor.fetchone()
    conn.close()
    
    if produto:
        nome_produto, preco = produto
        item = {
            'produto_id': produto_id,
            'nome_produto': nome_produto,
            'quantidade': quantidade,
            'preco': preco
        }
        
        carrinho = session.get('carrinho', [])
        carrinho.append(item)
        session['carrinho'] = carrinho
        session['cliente_id'] = cliente_id 
        
    return redirect(url_for('nova_venda'))

# Rota 3: Descarregar o Carrinho no Banco de Dados
@app.route('/finalizar_venda', methods=['POST'])
def finalizar_venda():
    carrinho = session.get('carrinho', [])
    cliente_id = session.get('cliente_id')
    if not carrinho or not cliente_id: return redirect(url_for('nova_venda'))

    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO pedidos (cliente_id) VALUES (?)", (cliente_id,))
        pedido_id = cursor.lastrowid

        for item in carrinho:
            cursor.execute("SELECT quantidade_estoque, nome FROM produtos WHERE id = ?", (item['produto_id'],))
            estoque_atual, nome_produto = cursor.fetchone()

            if estoque_atual < item['quantidade']:
                conn.rollback() 
                conn.close()
                flash(f"Venda cancelada! Estoque insuficiente para '{nome_produto}'. Restam apenas {estoque_atual} unidades.")
                return redirect(url_for('nova_venda'))

            cursor.execute("""
                INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_vendido)
                VALUES (?, ?, ?, ?)
            """, (pedido_id, item['produto_id'], item['quantidade'], item['preco']))
        
        conn.commit()
        session.pop('carrinho', None)
        session.pop('cliente_id', None)
        
    except sqlite3.Error as e:
        conn.rollback()
        flash("Ocorreu um erro interno no banco de dados.")
    finally:
        try: conn.close() 
        except: pass

    return redirect(url_for('dashboard'))

# Rota 4: Esvaziar carrinho manualmente
@app.route('/limpar_carrinho')
def limpar_carrinho():
    session.pop('carrinho', None)
    session.pop('cliente_id', None)
    return redirect(url_for('nova_venda'))

# Rota 5: Cadastrar Novo Cliente
@app.route('/novo_cliente', methods=['GET', 'POST'])
def novo_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        conn = sqlite3.connect("mini_erp.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO clientes (nome, email) VALUES (?, ?)", (nome, email))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
        return redirect(url_for('dashboard'))
    return render_template("novo_cliente.html")

# Rota 6: Ver Estoque
@app.route('/estoque')
def estoque():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco_atual, quantidade_estoque FROM produtos")
    produtos = cursor.fetchall()
    conn.close()
    return render_template("estoque.html", produtos=produtos)

# Rota 7: Ver Clientes
@app.route('/clientes')
def clientes():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email FROM clientes")
    lista_clientes = cursor.fetchall()
    conn.close()
    return render_template("clientes.html", clientes=lista_clientes)

# Rota 8: Cadastrar Novo Produto
@app.route('/novo_produto', methods=['GET', 'POST'])
def novo_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco_atual'])
        estoque = int(request.form['quantidade_estoque'])
        
        conn = sqlite3.connect("mini_erp.db")
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO produtos (nome, preco_atual, quantidade_estoque) VALUES (?, ?, ?)", (nome, preco, estoque))
            conn.commit()
            flash(f"Produto '{nome}' cadastrado com sucesso!", "success")
        except sqlite3.Error as e:
            conn.rollback()
            flash("Erro ao cadastrar o produto no banco de dados.", "error")
        finally:
            conn.close()
            
        return redirect(url_for('dashboard'))

    return render_template("novo_produto.html")

# Rota 9: Deletar Produto
@app.route('/deletar_produto/<int:id>')
def deletar_produto(id):
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
        conn.commit()
        flash("Produto deletado com sucesso!", "success")
    except sqlite3.Error:
        flash("Erro: Não é possível deletar um produto que já possui vendas registradas.", "error")
    finally:
        conn.close()
        
    return redirect(url_for('estoque'))

# Rota 10: Editar Produto
@app.route('/editar_produto/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco_atual'])
        estoque = int(request.form['quantidade_estoque'])

        try:
            cursor.execute("UPDATE produtos SET nome = ?, preco_atual = ?, quantidade_estoque = ? WHERE id = ?", (nome, preco, estoque, id))
            conn.commit()
            flash(f"Produto '{nome}' atualizado com sucesso!", "success")
        except sqlite3.Error:
            flash("Erro ao atualizar o produto.", "error")
        finally:
            conn.close()
            
        return redirect(url_for('estoque'))

    cursor.execute("SELECT id, nome, preco_atual, quantidade_estoque FROM produtos WHERE id = ?", (id,))
    produto = cursor.fetchone()
    conn.close()

    return render_template("editar_produto.html", produto=produto)

# Rota 11: Deletar Cliente
@app.route('/deletar_cliente/<int:id>')
def deletar_cliente(id):
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))
        conn.commit()
        flash("Cliente deletado com sucesso!", "success")
    except sqlite3.Error:
        flash("Erro: Não é possível deletar um cliente que já possui pedidos registrados no sistema.", "error")
    finally:
        conn.close()
        
    return redirect(url_for('clientes'))

# Rota 12: Editar Cliente
@app.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']

        try:
            cursor.execute("UPDATE clientes SET nome = ?, email = ? WHERE id = ?", (nome, email, id))
            conn.commit()
            flash(f"Cliente '{nome}' atualizado com sucesso!", "success")
        except sqlite3.IntegrityError:
            flash("Erro: Este e-mail já está em uso por outro cliente.", "error")
        except sqlite3.Error:
            flash("Erro interno ao atualizar o cliente.", "error")
        finally:
            conn.close()
            
        return redirect(url_for('clientes'))

    cursor.execute("SELECT id, nome, email FROM clientes WHERE id = ?", (id,))
    cliente = cursor.fetchone()
    conn.close()

    return render_template("editar_cliente.html", cliente=cliente)

if __name__ == "__main__":
    app.run(debug=True)