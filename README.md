# Módulo de Estoque — DOS (Desenvolvimento Orientado a Serviços)

CRUD de Estoque com login, feito em Python + Django + Django REST Framework.
Segue o padrão MVT do Django (views com funções, templates HTML, SQLite).

---

## Estrutura do Projeto

```
estoque-project/
├── manage.py
├── db.sqlite3                  (gerado após migrate)
├── iniciar.sh                  (script de inicialização — Linux/Mac)
├── iniciar.bat                 (script de inicialização — Windows)
├── seed_dados.py               (popula o banco com dados fictícios)
├── estoque_project/            (configurações do projeto)
│   ├── settings.py
│   ├── urls.py                 → rotas do projeto + registro das APIs
│   └── wsgi.py
└── estoque/                    (app principal)
    ├── models.py               → Categoria, Produto, MovimentacaoEstoque
    ├── views.py                → login, logout, CRUD, dashboard, APIs REST
    ├── serializers.py          → serialização dos models para a API
    ├── urls.py                 → rotas internas do app
    ├── admin.py
    ├── apps.py
    ├── migrations/
    └── templates/
        ├── login.html
        ├── dashboard.html
        ├── listarProdutos.html
        ├── cadastroProduto.html
        ├── editarProduto.html
        ├── movimentacao.html
        ├── listarMovimentacoes.html
        ├── historicoProduto.html
        └── gerenciarCategorias.html
```

---

## Como Rodar

### Opção 1 — Script automático (recomendado)

Coloque `iniciar.sh` (Linux/Mac) ou `iniciar.bat` (Windows) dentro da pasta `estoque-project/` e execute:

```bash
# Linux/Mac
chmod +x iniciar.sh
./iniciar.sh

# Windows
iniciar.bat
```

O script faz tudo automaticamente: cria o venv, instala dependências, roda as migrations, cria o usuário `admin / admin123` e sobe o servidor.

> Se o venv estiver corrompido (erro de "arquivo não encontrado"), apague-o antes: `rm -rf venv`

---

### Opção 2 — Manual

#### 1. Pré-requisito
Python 3.10+ instalado.

#### 2. Criar ambiente virtual
```bash
cd estoque-project
python3 -m venv venv
```

#### 3. Instalar dependências
```bash
# Linux/Mac — use o pip do venv diretamente (evita conflito com o Python do sistema)
venv/bin/pip install django djangorestframework

# Windows
venv\Scripts\pip install django djangorestframework
```

#### 4. Rodar as migrations
```bash
venv/bin/python manage.py makemigrations
venv/bin/python manage.py migrate
```

#### 5. Criar usuário admin
```bash
venv/bin/python manage.py createsuperuser
```

#### 6. (Opcional) Popular banco com dados fictícios
```bash
venv/bin/python manage.py shell < seed_dados.py
```
Cria 8 categorias, 35 produtos e 36 movimentações de exemplo.

#### 7. Rodar o servidor
```bash
venv/bin/python manage.py runserver
```

#### 8. Acessar no navegador
```
http://127.0.0.1:8000/
```

---

## Funcionalidades

### Login / Logout
- Tela de login com usuário e senha (auth nativo do Django)
- Todas as páginas exigem login (`@login_required`)
- Redireciona automaticamente para o Dashboard após login

### Dashboard
Página inicial após o login com resumo do estoque:
- Total de produtos cadastrados
- Total de itens físicos em estoque
- Valor total do estoque (quantidade × preço unitário)
- Produtos com estoque abaixo do mínimo (⚠️ alertas)
- Últimas 5 movimentações registradas

### Categorias
| Ação | URL |
|------|-----|
| Gerenciar | `/estoque/categorias` |
| Excluir | `/estoque/categorias/excluir/<id>` |

### Produtos (CRUD completo)
| Ação | URL |
|------|-----|
| Listar | `/estoque/listar` |
| Cadastrar | `/estoque/cadastrar` |
| Editar | `/estoque/editar/<id>` |
| Excluir | `/estoque/excluir/<id>` |
| Histórico | `/estoque/produto/<id>/historico` |

Campos: Nome, Descrição, Categoria, Quantidade, Quantidade Mínima, Preço Unitário, Localização no Depósito.
Alerta visual (⚠️) quando estoque ≤ quantidade mínima.
Filtro por categoria e busca por nome/descrição na listagem.

### Movimentações de Estoque
| Tipo | Efeito |
|------|--------|
| Entrada | Aumenta a quantidade |
| Saída | Diminui a quantidade (valida se há saldo) |
| Ajuste | Define um valor exato (correção de inventário) |

Histórico completo em `/estoque/movimentacoes`.
Histórico por produto em `/estoque/produto/<id>/historico`.

---

## Modelos (models.py)

### Categoria
- `nome` — nome da categoria (único)

### Produto
- `nome` — nome do produto
- `descricao` — descrição
- `categoria` — FK para Categoria
- `quantidade` — quantidade atual em estoque
- `quantidade_minima` — limite de alerta (dispara ⚠️)
- `preco_unitario` — preço por unidade (DecimalField — sem imprecisão de float)
- `localizacao_deposito` — ex: "Corredor A, Prateleira 3"
- `fornecedor_id` — ID do fornecedor (Módulo 3)
- `cliente_reserva_id` — ID do cliente com reserva (Módulo 2)
- `status_reserva` — booleano de reserva

### MovimentacaoEstoque
- `produto` — FK para Produto
- `tipo` — ENTRADA / SAIDA / AJUSTE
- `quantidade` — quantidade movimentada
- `observacao` — texto livre (NF, pedido, etc.)
- `data` — preenchida automaticamente
- `usuario` — FK para User (quem realizou)
- `custo_total_financeiro` — calculado automaticamente (quantidade × preço unitário)

---

## API REST

O módulo expõe endpoints REST para comunicação com os outros módulos do sistema.
Base URL: `http://<host>:8000/api/`

### CRUD automático (Django REST Framework)

| Recurso | Endpoint | Métodos |
|---------|----------|---------|
| Produtos | `/api/produtos/` | GET, POST, PUT, PATCH, DELETE |
| Movimentações | `/api/movimentacoes/` | GET, POST, PUT, PATCH, DELETE |
| Categorias | `/api/categorias/` | GET, POST, PUT, PATCH, DELETE |

Exemplo de produto retornado:
```json
{
  "id": 1,
  "nome": "Notebook Dell Inspiron",
  "descricao": "i5 12ª gen, 8GB RAM, 256GB SSD",
  "categoria": 5,
  "quantidade": 8,
  "quantidade_minima": 3,
  "preco_unitario": "3200.00",
  "localizacao_deposito": "Sala TI - Armário B1",
  "fornecedor_id": 13,
  "status_reserva": false,
  "estoque_baixo": false
}
```

---

### Endpoints de integração entre módulos

#### `POST /api/entrada-compra/`
**Quem usa: Módulo 5 (Entrada/Compras)**
Registra entrada de mercadoria no estoque ao confirmar uma compra.

```json
// Request
{
  "produto_id": 3,
  "quantidade": 10,
  "observacao": "NF-001 — Compra mensal",
  "fornecedor_id": 7
}

// Response 201
{
  "mensagem": "Entrada registrada com sucesso.",
  "produto_id": 3,
  "produto_nome": "Resma de Papel A4",
  "quantidade_adicionada": 10,
  "quantidade_atual": 60,
  "custo_total_financeiro": "280.00",
  "movimentacao_id": 42
}
```

---

#### `POST /api/saida-venda/`
**Quem usa: Módulo 6 (Venda/Saída)**
Dá baixa no estoque ao confirmar uma venda. Retorna erro `409` se não houver saldo.

```json
// Request
{
  "produto_id": 3,
  "quantidade": 2,
  "observacao": "Pedido #99",
  "cliente_id": 5
}

// Response 201
{
  "mensagem": "Saída registrada com sucesso.",
  "produto_id": 3,
  "produto_nome": "Resma de Papel A4",
  "quantidade_retirada": 2,
  "quantidade_atual": 58,
  "custo_total_financeiro": "56.00",
  "movimentacao_id": 43,
  "estoque_baixo": false
}

// Response 409 — sem saldo
{
  "erro": "Saldo insuficiente em estoque.",
  "disponivel": 1,
  "solicitado": 2
}
```

---

#### `GET /api/estoque-disponivel/<produto_id>/`
**Quem usa: Módulo 6 (Venda) — antes de fechar o pedido**
Consulta saldo disponível de um produto sem registrar movimentação.

```json
// Response 200
{
  "produto_id": 3,
  "produto_nome": "Resma de Papel A4",
  "quantidade_disponivel": 58,
  "quantidade_minima": 10,
  "estoque_baixo": false,
  "preco_unitario": "28.00",
  "localizacao_deposito": "Corredor D, Prateleira 1"
}
```

---

#### `GET /api/financeiro/resumo/`
**Quem usa: Módulo 9 (Financeiro)**
Retorna valor total do estoque e custo de todas as movimentações para consolidação financeira.

```json
// Response 200
{
  "valor_total_estoque": "127430.00",
  "total_custo_entradas": "98500.00",
  "total_custo_saidas": "12300.00",
  "movimentacoes": [ ... ]
}
```

---

#### `GET /api/produto/<produto_id>/`
**Quem usa: qualquer módulo**
Retorna dados completos de um produto. Útil para Módulo 1 (Produto) e Módulo 3 (Fornecedor) consultarem informações.

---

#### `POST /api/reservar/`
**Quem usa: Módulo 2 (Cliente) ou Módulo 6 (Venda)**
Marca ou desmarca um produto como reservado para um cliente. Não altera a quantidade.

```json
// Request
{ "produto_id": 3, "cliente_id": 12, "reservar": true }

// Response 200
{
  "mensagem": "Reserva atualizada.",
  "produto_id": 3,
  "produto_nome": "Resma de Papel A4",
  "status_reserva": true,
  "cliente_reserva_id": 12
}
```

---

#### `GET /api/historico/<produto_id>/`
**Quem usa: Módulo 7 (Funcionário), Módulo 8 (RH), Módulo 9 (Financeiro)**
Retorna o histórico completo de movimentações de um produto, incluindo quem realizou cada operação.

```json
// Response 200
{
  "produto_id": 3,
  "produto_nome": "Resma de Papel A4",
  "quantidade_atual": 58,
  "movimentacoes": [ ... ]
}
```

---

## Mapa de integração com os outros módulos

| Módulo | Tipo | Endpoint / Campo | Como conecta |
|--------|------|-----------------|--------------|
| 1 — Produto | Consulta | `GET /api/produtos/` | Consulta catálogo de produtos do estoque |
| 2 — Cliente | Escrita | `POST /api/reservar/` | Reserva produto para um cliente específico |
| 3 — Fornecedor | Leitura/Escrita | `fornecedor_id` no Produto | Vincula fornecedor ao produto; Compras informa na entrada |
| 5 — Entrada | Escrita | `POST /api/entrada-compra/` | Toda compra aprovada gera MovimentacaoEstoque tipo ENTRADA |
| 6 — Venda | Leitura + Escrita | `GET /api/estoque-disponivel/` → `POST /api/saida-venda/` | Consulta saldo antes de vender; registra SAIDA ao confirmar |
| 7 — Funcionário | Leitura | `GET /api/historico/<id>/` | Auditoria de quem fez cada movimentação (`usuario` na movimentação) |
| 8 — RH | Leitura | `GET /api/historico/<id>/` | Relatório de atividade dos funcionários no estoque |
| 9 — Financeiro | Leitura | `GET /api/financeiro/resumo/` | Capital imobilizado em estoque + custo de todas as movimentações |

> Módulo 4 é este próprio módulo (Estoque).

---

## Observações técnicas

- Todas as APIs estão com `AllowAny` (sem autenticação obrigatória) para facilitar a integração durante o desenvolvimento. Quando o sistema estiver consolidado, trocar para `IsAuthenticated`.
- O campo `custo_total_financeiro` em `MovimentacaoEstoque` é calculado automaticamente no `save()` do model (`quantidade × preco_unitario`), garantindo consistência mesmo quando chamado via API.
- `DecimalField` é usado para preços (em vez de `FloatField`) para evitar imprecisão de ponto flutuante em valores monetários.
- O padrão de movimentação segue o modelo **ledger (livro-razão)**: o estoque atual fica em `Produto.quantidade`, e o histórico completo de como se chegou a esse número fica em `MovimentacaoEstoque`.