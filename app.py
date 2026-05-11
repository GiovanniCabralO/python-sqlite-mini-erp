from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route('/')
def dashboard():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM vw_relatorio_vendas")
    dados_vendas = cursor.fetchall()

    conn.close()
    return render_template("index.html", relatorio_vendas=dados_vendas)

if __name__ == "__main__":
    app.run(debug=True)