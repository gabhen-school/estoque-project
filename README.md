# Módulo de Estoque — DOS (Desenvolvimento Orientado a Serviços)

CRUD de Estoque com login, feito em Python + Django.
Segue o mesmo padrão do projeto base (views com funções, templates HTML simples, SQLite).

---

## Estrutura do Projeto

```
estoque_project/
├── manage.py
├── db.sqlite3            (gerado após migrate)
├── estoque_project/      (configurações do projeto)
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── estoque/              (app principal)
    ├── models.py         → Produto, MovimentacaoEstoque
    ├── views.py          → login, logout, CRUD produto, movimentação
    ├── urls.py
    ├── admin.py
    ├── apps.py
    ├── migrations/
    └── templates/
        ├── login.html
        ├── listarProdutos.html
        ├── cadastroProduto.html
        ├── editarProduto.html
        ├── movimentacao.html
        └── listarMovimentacoes.html
```

---

## Como Rodar

### 1. Pré-requisito
Python 3.10+ instalado.

### 2. Criar e ativar ambiente virtual
```bash
cd estoque_project

python3 -m venv venv

# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. Instalar Django
```bash
pip install django
```

### 4. Rodar as migrations (cria o banco)
```bash
python3 manage.py migrate
python3 manage.py makemigrations
python3 manage.py migrate
```

### 5. Criar usuário admin (para fazer login)
```bash
python3 manage.py createsuperuser
```
Vai pedir nome, e-mail (pode deixar em branco) e senha.

### 6. Rodar o servidor
```bash
python3 manage.py runserver
```

### 7. Acessar no navegador
```
http://127.0.0.1:8000/
```


---

## Funcionalidades

### Login / Logout
- Tela de login com usuário e senha (usa o sistema de auth nativo do Django)
- Todas as páginas exigem login (`@login_required`)

### Produtos (CRUD completo)
| Ação | URL |
|------|-----|
| Listar | `/estoque/listar` |
| Cadastrar | `/estoque/cadastrar` |
| Editar | `/estoque/editar/<id>` |
| Excluir | `/estoque/excluir/<id>` |

Campos: Nome, Descrição, Quantidade, Quantidade Mínima, Preço Unitário.
Alerta visual (⚠️) quando estoque ≤ quantidade mínima.

### Movimentações de Estoque
| Tipo | Efeito |
|------|--------|
| Entrada | Aumenta a quantidade |
| Saída | Diminui a quantidade (valida se há saldo) |
| Ajuste | Define um valor exato |

Histórico completo em `/estoque/movimentacoes`.

---

## Modelos (models.py)

### Produto
- `nome` — nome do produto
- `descricao` — descrição
- `quantidade` — quantidade atual em estoque
- `quantidade_minima` — limite de alerta
- `preco_unitario` — preço por unidade

### MovimentacaoEstoque
- `produto` — FK para Produto
- `tipo` — ENTRADA / SAIDA / AJUSTE
- `quantidade` — quantidade movimentada
- `observacao` — texto livre (NF, pedido, etc.)
- `data` — preenchida automaticamente

---

## Integração com outros módulos (futura)

Para conectar com os outros grupos, os campos-chave serão:

| Módulo | Campo esperado |
|--------|---------------|
| Produto (3) | `Produto.id` e `Produto.nome` |
| Entrada/Compras (5) | cria `MovimentacaoEstoque` tipo ENTRADA |
| Venda/Saída | cria `MovimentacaoEstoque` tipo SAIDA |
| Financeiro (6) | `Produto.preco_unitario` |

Quando houver integração, esses módulos poderão importar os models diretamente
(se estiverem no mesmo projeto Django) ou via API REST.


rm -rf venv
chmod +x iniciar.sh
./iniciar.sh