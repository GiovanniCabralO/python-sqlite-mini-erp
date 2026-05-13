# 🛒 Mini ERP — Sistema de Gestão de Vendas

Aplicação web full-stack que simula um sistema ERP para pequenas empresas, desenvolvida para demonstrar habilidades práticas com SQL e backend Python. Conta com um fluxo completo de vendas, controle de estoque e dashboard analítico — tudo sustentado por um banco de dados SQLite construído à mão, sem ORM.

🔗 **Deploy:** [giovannicabral.pythonanywhere.com](https://giovannicabral.pythonanywhere.com)

---

## 📸 Screenshots

> Dashboard com relatório de vendas filtrável, ranking de clientes e resumo de estoque.

![Dashboard](screenshots/dashboard.png)

---

## ✨ Funcionalidades

- **Fluxo de vendas** — carrinho por sessão, pedidos com múltiplos itens, validação de estoque antes de finalizar
- **Gestão de clientes** — cadastro, edição e exclusão com proteção por integridade referencial
- **Gestão de produtos** — cadastro, edição e exclusão com atualização automática de estoque
- **Dashboard** — relatório filtrável (por cliente, produto e data), ranking dos top 6 clientes e alertas de estoque baixo
- **Script de seed** — gera dados realistas para teste (10 clientes, 10 produtos, 40 pedidos aleatórios)

---

## 🗄️ Conceitos SQL Demonstrados

O projeto foi construído para ir além de um CRUD básico e demonstrar domínio real de banco de dados relacional:

| Conceito | Onde |
|---|---|
| Schema relacional com Foreign Keys | `setup_database.py` — 4 tabelas normalizadas |
| `TRIGGER` (atualização automática de estoque) | Dispara `AFTER INSERT ON itens_pedido`, atualiza `produtos.quantidade_estoque` |
| `VIEW` (relatório de vendas) | `vw_relatorio_vendas` — JOIN de 3 tabelas encapsulado como view reutilizável |
| Agregação (`SUM`, `GROUP BY`, `ORDER BY`) | Query de ranking de clientes por total gasto |
| Filtragem dinâmica parametrizada | Padrão `WHERE 1=1` com filtros opcionais encadeados no dashboard |
| Controle de transação (`COMMIT` / `ROLLBACK`) | Validação de estoque no meio da transação com rollback total em caso de falha |
| `executemany` para inserções em lote | `inserir_dados.py` |

---

## 🛠️ Tecnologias

- **Backend:** Python 3, Flask
- **Banco de dados:** SQLite3 (SQL puro, sem ORM)
- **Frontend:** Jinja2, HTML/CSS
- **Deploy:** PythonAnywhere

---

## 🚀 Rodando Localmente

```bash
# 1. Clone o repositório
git clone https://github.com/GiovanniCabralO/mini-erp
cd mini-erp

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Crie o arquivo .env
echo "SECRET_KEY=sua-chave-secreta" > .env

# 5. Configure o banco de dados
python setup_database.py

# 6. (Opcional) Popule com dados de exemplo
python seed.py

# 7. Inicie o servidor
python app.py
```

Acesse [http://localhost:5000](http://localhost:5000).

---

## 📁 Estrutura do Projeto

```
mini-erp/
├── app.py                 # Rotas Flask (12 endpoints)
├── setup_database.py      # Schema: tabelas, trigger, constraints FK
├── seed.py                # Gerador de dados de teste realistas
├── gerar_relatorio.py     # Relatório de vendas via CLI + criação da view
├── requirements.txt
├── .env                   # SECRET_KEY (não commitado)
├── .gitignore
└── templates/
    ├── index.html         # Dashboard com filtros
    ├── nova_venda.html    # Carrinho e checkout
    ├── estoque.html       # CRUD de produtos
    ├── clientes.html      # CRUD de clientes
    └── ...
```

---

## 📌 Autor

**Giovanni Cabral** — Estudante de Engenharia da Computação na Facens | Estagiário de Python & Automação na Huawei Technologies

[GitHub](https://github.com/GiovanniCabralO) · [LinkedIn](www.linkedin.com/in/giovannicabraldeoliveira)