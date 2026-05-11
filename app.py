from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

# Rota 1: Dashboard
@app.route('/')
def dashboard():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vw_relatorio_vendas")
    dados_vendas = cursor.fetchall()
    conn.close()
    return render_template("index.html", relatorio_vendas=dados_vendas)

# Rota 2: Tela de Vendas 
@app.route('/nova_venda', methods=['GET', 'POST'])
def nova_venda():
    if 'carrinho' not in session:
        session['carrinho'] = []
        session['cliente_id'] = None 

    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        produto_id = request.form.get('produto_id')
        quantidade = int(request.form.get('quantidade'))

        session['cliente_id'] = cliente_id

        cursor.execute("SELECT nome, preco_atual FROM produtos WHERE id = ?", (produto_id,))
        produto = cursor.fetchone()

        if produto:
            item = {
                'produto_id': produto_id,
                'nome': produto[0],
                'preco': produto[1],
                'quantidade': quantidade,
                'subtotal': produto[1] * quantidade
            }
            carrinho = session['carrinho']
            carrinho.append(item)
            session['carrinho'] = carrinho

        conn.close()
        return redirect(url_for('nova_venda'))

    # 3. MODO GET 
    cursor.execute("SELECT id, nome FROM clientes")
    clientes = cursor.fetchall()

    cursor.execute("SELECT id, nome, preco_atual, quantidade_estoque FROM produtos")
    produtos = cursor.fetchall()
    conn.close()

    return render_template("nova_venda.html", clientes=clientes, produtos=produtos, carrinho=session['carrinho'], cliente_selecionado=str(session['cliente_id']))

# Rota 3: Descarregar o Carrinho no Banco de Dados
@app.route('/finalizar_venda', methods=['POST'])
def finalizar_venda():
    carrinho = session.get('carrinho', [])
    cliente_id = session.get('cliente_id')

    if not carrinho or not cliente_id:
        return redirect(url_for('nova_venda'))

    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO pedidos (cliente_id) VALUES (?)", (cliente_id,))
        pedido_id = cursor.lastrowid 

        for item in carrinho:
            cursor.execute("""
                INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_vendido)
                VALUES (?, ?, ?, ?)
            """, (pedido_id, item['produto_id'], item['quantidade'], item['preco']))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro no banco: {e}")
        conn.rollback()
    finally:
        conn.close()

    session.pop('carrinho', None)
    session.pop('cliente_id', None)

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

if __name__ == "__main__":
    app.run(debug=True)