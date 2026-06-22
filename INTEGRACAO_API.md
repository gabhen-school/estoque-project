# Guia de Integração — Consumindo APIs Externas dos Outros Módulos

Este documento explica como o **Módulo de Estoque** pode consumir as APIs dos outros módulos do sistema (Fornecedores, Clientes, Vendas, Compras, RH, Financeiro), e como esses módulos consomem as APIs do Estoque.

> **Base URL no PythonAnywhere:**
> Cada módulo terá sua própria URL no formato:
> `https://<usuario-do-modulo>.pythonanywhere.com/`

---

## Sumário

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Configuração Inicial (requests)](#2-configuração-inicial)
3. [Criando o Serviço de Integração](#3-criando-o-serviço-de-integração)
4. [Integração com Módulo 1 — Produtos](#4-integração-com-módulo-1--produtos)
5. [Integração com Módulo 2 — Clientes](#5-integração-com-módulo-2--clientes)
6. [Integração com Módulo 3 — Fornecedores](#6-integração-com-módulo-3--fornecedores)
7. [Integração com Módulo 5 — Compras/Entradas](#7-integração-com-módulo-5--comprasentradas)
8. [Integração com Módulo 6 — Vendas/Saídas](#8-integração-com-módulo-6--vendassaídas)
9. [Integração com Módulo 9 — Financeiro](#9-integração-com-módulo-9--financeiro)
10. [Como Outros Módulos Consomem NOSSAS APIs](#10-como-outros-módulos-consomem-nossas-apis)
11. [Testando as Integrações](#11-testando-as-integrações)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Visão Geral da Arquitetura

```
┌─────────────┐     HTTP/JSON      ┌──────────────────┐
│  Módulo 3   │◄──────────────────►│                  │
│ Fornecedores│                    │                  │
└─────────────┘                    │                  │
                                   │    MÓDULO 4      │
┌─────────────┐     HTTP/JSON      │    ESTOQUE       │
│  Módulo 5   │◄──────────────────►│                  │
│  Compras    │                    │  (este projeto)  │
└─────────────┘                    │                  │
                                   │                  │
┌─────────────┐     HTTP/JSON      │                  │
│  Módulo 6   │◄──────────────────►│                  │
│  Vendas     │                    └──────────────────┘
└─────────────┘

Cada módulo roda em seu próprio servidor PythonAnywhere.
A comunicação é feita via requisições HTTP (REST API) usando JSON.
```

---

## 2. Configuração Inicial

### Passo 1 — Instalar a biblioteca `requests`

```bash
pip install requests
```

Atualize o `requirements.txt`:

```
django
djangorestframework
requests
```

### Passo 2 — Configurar as URLs dos módulos externos

No arquivo `estoque_project/settings.py`, adicione no final:

```python
# ── URLs dos módulos externos (PythonAnywhere) ──────────────────
# Substitua pelos usernames reais de cada grupo no PythonAnywhere

MODULOS_EXTERNOS = {
    'PRODUTOS':     'https://<usuario-modulo1>.pythonanywhere.com',
    'CLIENTES':     'https://<usuario-modulo2>.pythonanywhere.com',
    'FORNECEDORES': 'https://<usuario-modulo3>.pythonanywhere.com',
    'COMPRAS':      'https://<usuario-modulo5>.pythonanywhere.com',
    'VENDAS':       'https://<usuario-modulo6>.pythonanywhere.com',
    'FUNCIONARIOS': 'https://<usuario-modulo7>.pythonanywhere.com',
    'RH':           'https://<usuario-modulo8>.pythonanywhere.com',
    'FINANCEIRO':   'https://<usuario-modulo9>.pythonanywhere.com',
}
```

> **Importante:** Quando os colegas fizerem o deploy, basta trocar `<usuario-moduloX>` pelo username real deles no PythonAnywhere.

---

## 3. Criando o Serviço de Integração

Crie um novo arquivo `estoque/integracao.py` para centralizar todas as chamadas externas:

```python
# estoque/integracao.py

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Timeout padrão para chamadas externas (segundos)
TIMEOUT = 10


def _get_base_url(modulo):
    """Retorna a base URL de um módulo externo configurado no settings."""
    urls = getattr(settings, 'MODULOS_EXTERNOS', {})
    url = urls.get(modulo)
    if not url:
        raise ValueError(f"Módulo '{modulo}' não configurado em MODULOS_EXTERNOS.")
    return url.rstrip('/')


def _fazer_get(modulo, endpoint, params=None):
    """
    Faz uma requisição GET para um módulo externo.
    Retorna o JSON da resposta ou None em caso de erro.
    """
    url = f"{_get_base_url(modulo)}/{endpoint.lstrip('/')}"
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        logger.error(f"[INTEGRAÇÃO] Não foi possível conectar ao módulo {modulo}: {url}")
        return None
    except requests.exceptions.Timeout:
        logger.error(f"[INTEGRAÇÃO] Timeout ao acessar {modulo}: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"[INTEGRAÇÃO] Erro HTTP {resp.status_code} de {modulo}: {e}")
        return None
    except Exception as e:
        logger.error(f"[INTEGRAÇÃO] Erro inesperado com {modulo}: {e}")
        return None


def _fazer_post(modulo, endpoint, dados):
    """
    Faz uma requisição POST para um módulo externo.
    Retorna (status_code, json_da_resposta) ou (None, None) em caso de erro.
    """
    url = f"{_get_base_url(modulo)}/{endpoint.lstrip('/')}"
    try:
        resp = requests.post(url, json=dados, timeout=TIMEOUT)
        return resp.status_code, resp.json()
    except requests.exceptions.ConnectionError:
        logger.error(f"[INTEGRAÇÃO] Não foi possível conectar ao módulo {modulo}: {url}")
        return None, None
    except requests.exceptions.Timeout:
        logger.error(f"[INTEGRAÇÃO] Timeout ao enviar para {modulo}: {url}")
        return None, None
    except Exception as e:
        logger.error(f"[INTEGRAÇÃO] Erro inesperado com {modulo}: {e}")
        return None, None
```

---

## 4. Integração com Módulo 1 — Produtos

> **Cenário:** Consultar catálogo de produtos do módulo de Produtos (se existir separado do Estoque).

Adicione ao `estoque/integracao.py`:

```python
# ── MÓDULO 1: PRODUTOS ─────────────────────────────────────────

def buscar_produto_externo(produto_id):
    """Busca dados de um produto no Módulo de Produtos."""
    return _fazer_get('PRODUTOS', f'/api/produtos/{produto_id}/')


def listar_produtos_externos():
    """Lista todos os produtos do Módulo de Produtos."""
    return _fazer_get('PRODUTOS', '/api/produtos/')
```

### Como usar nas views:

```python
from estoque.integracao import buscar_produto_externo

def alguma_view(request):
    produto_externo = buscar_produto_externo(3)
    if produto_externo:
        nome = produto_externo['nome']
        preco = produto_externo['preco_unitario']
    # ...
```

---

## 5. Integração com Módulo 2 — Clientes

> **Cenário:** Ao reservar um produto, buscar o nome do cliente para exibir na tela.

```python
# ── MÓDULO 2: CLIENTES ─────────────────────────────────────────

def buscar_cliente(cliente_id):
    """Busca dados de um cliente no Módulo de Clientes."""
    return _fazer_get('CLIENTES', f'/api/clientes/{cliente_id}/')


def listar_clientes():
    """Lista todos os clientes disponíveis."""
    return _fazer_get('CLIENTES', '/api/clientes/')
```

### Uso prático — Mostrar nome do cliente na reserva:

```python
from estoque.integracao import buscar_cliente

@login_required
def detalhe_produto_com_reserva(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    nome_cliente = None
    if produto.status_reserva and produto.cliente_reserva_id:
        cliente = buscar_cliente(produto.cliente_reserva_id)
        if cliente:
            nome_cliente = cliente.get('nome', 'Cliente desconhecido')

    return render(request, 'detalhe.html', {
        'produto': produto,
        'nome_cliente': nome_cliente,
    })
```

---

## 6. Integração com Módulo 3 — Fornecedores

> **Cenário:** Ao cadastrar ou editar um produto, buscar a lista de fornecedores para o usuário selecionar.

```python
# ── MÓDULO 3: FORNECEDORES ─────────────────────────────────────

def buscar_fornecedor(fornecedor_id):
    """Busca dados de um fornecedor específico."""
    return _fazer_get('FORNECEDORES', f'/api/fornecedores/{fornecedor_id}/')


def listar_fornecedores():
    """Lista todos os fornecedores disponíveis."""
    return _fazer_get('FORNECEDORES', '/api/fornecedores/')
```

### Uso prático — Exibir nome do fornecedor na listagem de produtos:

```python
from estoque.integracao import buscar_fornecedor

@login_required
def listar_produtos_com_fornecedor(request):
    produtos = Produto.objects.all()

    # Enriquecer com nome do fornecedor
    for produto in produtos:
        if produto.fornecedor_id:
            fornecedor = buscar_fornecedor(produto.fornecedor_id)
            produto.nome_fornecedor = fornecedor.get('nome', '—') if fornecedor else '—'
        else:
            produto.nome_fornecedor = '—'

    return render(request, 'listarProdutos.html', {'produtos': produtos})
```

### Uso prático — Dropdown de fornecedores no cadastro:

```python
@login_required
def cadastrar_produto(request):
    if request.method == 'POST':
        # ... lógica existente de cadastro ...
        fornecedor_id = request.POST.get('fornecedor_id')
        if fornecedor_id:
            produto.fornecedor_id = int(fornecedor_id)
        produto.save()
        return redirect('/estoque/listar')

    categorias = Categoria.objects.all()
    fornecedores = listar_fornecedores() or []  # Lista da API externa

    return render(request, 'cadastroProduto.html', {
        'categorias': categorias,
        'fornecedores': fornecedores,
    })
```

---

## 7. Integração com Módulo 5 — Compras/Entradas

> **Cenário:** O módulo de Compras chama NOSSA API para registrar entrada.
> Mas podemos também consultar compras pendentes do módulo deles.

```python
# ── MÓDULO 5: COMPRAS ──────────────────────────────────────────

def listar_compras_pendentes():
    """Consulta compras pendentes no Módulo de Compras."""
    return _fazer_get('COMPRAS', '/api/compras/', params={'status': 'pendente'})


def buscar_compra(compra_id):
    """Busca detalhes de uma compra específica."""
    return _fazer_get('COMPRAS', f'/api/compras/{compra_id}/')


def confirmar_recebimento_compra(compra_id):
    """
    Notifica o Módulo de Compras que o estoque recebeu a mercadoria.
    (Caso o módulo de Compras tenha um endpoint para isso)
    """
    status_code, resposta = _fazer_post('COMPRAS', f'/api/compras/{compra_id}/recebido/', {
        'recebido': True,
        'modulo_origem': 'estoque',
    })
    return resposta if status_code and status_code < 300 else None
```

### Fluxo completo — Compra gerando entrada no estoque:

```
Módulo 5 (Compras)                    Módulo 4 (Estoque — nós)
        │                                      │
        │  POST /api/entrada-compra/           │
        │  { produto_id, quantidade,           │
        │    observacao, fornecedor_id }        │
        │─────────────────────────────────────►│
        │                                      │ 1. Valida dados
        │                                      │ 2. Atualiza Produto.quantidade
        │                                      │ 3. Cria MovimentacaoEstoque
        │                                      │ 4. Vincula fornecedor_id
        │  Response 201                        │
        │  { mensagem, quantidade_atual,       │
        │    custo_total_financeiro }           │
        │◄─────────────────────────────────────│
```

---

## 8. Integração com Módulo 6 — Vendas/Saídas

> **Cenário:** O módulo de Vendas consulta nosso estoque antes de fechar o pedido, depois registra a saída.

```python
# ── MÓDULO 6: VENDAS ───────────────────────────────────────────

def buscar_venda(venda_id):
    """Busca detalhes de uma venda no Módulo de Vendas."""
    return _fazer_get('VENDAS', f'/api/vendas/{venda_id}/')


def listar_vendas_recentes():
    """Lista vendas recentes para exibir no dashboard do estoque."""
    return _fazer_get('VENDAS', '/api/vendas/', params={'limit': 10})


def notificar_estoque_baixo(produto_id, produto_nome, quantidade_atual):
    """
    Notifica o Módulo de Vendas que um produto está com estoque baixo.
    (Caso queiram implementar um alerta no módulo deles)
    """
    status_code, resposta = _fazer_post('VENDAS', '/api/alertas/estoque-baixo/', {
        'produto_id': produto_id,
        'produto_nome': produto_nome,
        'quantidade_atual': quantidade_atual,
        'modulo_origem': 'estoque',
    })
    return resposta if status_code and status_code < 300 else None
```

### Fluxo completo — Venda gerando saída no estoque:

```
Módulo 6 (Vendas)                     Módulo 4 (Estoque — nós)
        │                                      │
        │  1. GET /api/estoque-disponivel/3/   │
        │─────────────────────────────────────►│
        │  { quantidade_disponivel: 58 }       │
        │◄─────────────────────────────────────│
        │                                      │
        │  2. POST /api/saida-venda/           │
        │  { produto_id: 3, quantidade: 2 }    │
        │─────────────────────────────────────►│
        │                                      │ Valida saldo
        │                                      │ Atualiza quantidade
        │  Response 201 ou 409                 │ Cria movimentação
        │◄─────────────────────────────────────│
```

---

## 9. Integração com Módulo 9 — Financeiro

> **Cenário:** O módulo Financeiro consome NOSSA API. Mas podemos também consultar dados financeiros deles.

```python
# ── MÓDULO 9: FINANCEIRO ───────────────────────────────────────

def enviar_resumo_financeiro():
    """
    Envia o resumo financeiro do estoque para o Módulo Financeiro.
    Alternativa ativa: ao invés de esperar o Financeiro consultar,
    nós enviamos os dados proativamente.
    """
    from django.db.models import Sum, F, DecimalField
    from .models import Produto, MovimentacaoEstoque

    valor_total = Produto.objects.annotate(
        total_item=F('quantidade') * F('preco_unitario')
    ).aggregate(total=Sum('total_item', output_field=DecimalField()))['total'] or 0

    status_code, resposta = _fazer_post('FINANCEIRO', '/api/receber-dados-estoque/', {
        'valor_total_estoque': str(valor_total),
        'modulo_origem': 'estoque',
    })
    return resposta if status_code and status_code < 300 else None


def buscar_relatorio_financeiro():
    """Consulta relatórios financeiros consolidados do Módulo Financeiro."""
    return _fazer_get('FINANCEIRO', '/api/relatorios/')
```

---

## 10. Como Outros Módulos Consomem NOSSAS APIs

Este é o código que os **outros grupos** devem usar para consumir as APIs do nosso módulo de Estoque.

### URL base (PythonAnywhere)

```python
# No settings.py do módulo deles:
ESTOQUE_API_URL = 'https://<nosso-usuario>.pythonanywhere.com'
```

### Exemplos prontos para os outros grupos copiarem:

#### Módulo 5 (Compras) → Registrar entrada no estoque

```python
import requests

ESTOQUE_URL = 'https://<nosso-usuario>.pythonanywhere.com'

def registrar_entrada_estoque(produto_id, quantidade, observacao, fornecedor_id):
    resp = requests.post(f'{ESTOQUE_URL}/api/entrada-compra/', json={
        'produto_id': produto_id,
        'quantidade': quantidade,
        'observacao': observacao,
        'fornecedor_id': fornecedor_id,
    })

    if resp.status_code == 201:
        dados = resp.json()
        print(f"Entrada registrada! Estoque atual: {dados['quantidade_atual']}")
        return dados
    else:
        print(f"Erro: {resp.json()}")
        return None
```

#### Módulo 6 (Vendas) → Verificar estoque e registrar saída

```python
import requests

ESTOQUE_URL = 'https://<nosso-usuario>.pythonanywhere.com'

def verificar_e_vender(produto_id, quantidade, observacao, cliente_id):
    # 1. Verifica se há estoque
    check = requests.get(f'{ESTOQUE_URL}/api/estoque-disponivel/{produto_id}/')
    if check.status_code != 200:
        print("Produto não encontrado.")
        return None

    disponivel = check.json()['quantidade_disponivel']
    if disponivel < quantidade:
        print(f"Estoque insuficiente. Disponível: {disponivel}")
        return None

    # 2. Registra a saída
    resp = requests.post(f'{ESTOQUE_URL}/api/saida-venda/', json={
        'produto_id': produto_id,
        'quantidade': quantidade,
        'observacao': observacao,
        'cliente_id': cliente_id,
    })

    if resp.status_code == 201:
        return resp.json()
    else:
        print(f"Erro na saída: {resp.json()}")
        return None
```

#### Módulo 2 (Clientes) → Reservar produto

```python
import requests

ESTOQUE_URL = 'https://<nosso-usuario>.pythonanywhere.com'

def reservar_produto(produto_id, cliente_id):
    resp = requests.post(f'{ESTOQUE_URL}/api/reservar/', json={
        'produto_id': produto_id,
        'cliente_id': cliente_id,
        'reservar': True,
    })
    return resp.json() if resp.status_code == 200 else None
```

#### Módulo 9 (Financeiro) → Consultar resumo financeiro

```python
import requests

ESTOQUE_URL = 'https://<nosso-usuario>.pythonanywhere.com'

def obter_resumo_estoque():
    resp = requests.get(f'{ESTOQUE_URL}/api/financeiro/resumo/')
    if resp.status_code == 200:
        dados = resp.json()
        print(f"Valor total em estoque: R$ {dados['valor_total_estoque']}")
        print(f"Custo total de entradas: R$ {dados['total_custo_entradas']}")
        print(f"Custo total de saídas: R$ {dados['total_custo_saidas']}")
        return dados
    return None
```

---

## 11. Testando as Integrações

### Testar com curl (localmente)

```bash
# Listar produtos
curl http://127.0.0.1:8000/api/produtos/

# Registrar entrada
curl -X POST http://127.0.0.1:8000/api/entrada-compra/ \
     -H "Content-Type: application/json" \
     -d '{"produto_id": 1, "quantidade": 10, "observacao": "Teste", "fornecedor_id": 1}'

# Verificar estoque
curl http://127.0.0.1:8000/api/estoque-disponivel/1/

# Registrar saída
curl -X POST http://127.0.0.1:8000/api/saida-venda/ \
     -H "Content-Type: application/json" \
     -d '{"produto_id": 1, "quantidade": 2, "observacao": "Teste venda", "cliente_id": 1}'

# Resumo financeiro
curl http://127.0.0.1:8000/api/financeiro/resumo/
```

### Testar no PythonAnywhere

Basta trocar `http://127.0.0.1:8000` por `https://<seu-usuario>.pythonanywhere.com`:

```bash
curl https://<seu-usuario>.pythonanywhere.com/api/produtos/
```

### Testar via Python (shell do Django)

```bash
python3 manage.py shell
```

```python
import requests

# Testar chamada local
resp = requests.get('http://127.0.0.1:8000/api/produtos/')
print(resp.json())

# Testar chamada ao módulo de Fornecedores (quando estiver online)
resp = requests.get('https://<usuario-modulo3>.pythonanywhere.com/api/fornecedores/')
print(resp.json())
```

### Testar via navegador

O Django REST Framework possui uma interface web automática. Acesse no navegador:

```
http://127.0.0.1:8000/api/
```

Você verá uma página interativa onde pode testar todos os endpoints com formulários.

---

## 12. Troubleshooting

### Erro: "ConnectionError" ou "Timeout"

- Verifique se o módulo externo está online no PythonAnywhere
- Confira a URL no `settings.MODULOS_EXTERNOS`
- Teste manualmente com `curl` ou o navegador

### Erro: "CSRF verification failed"

Nas APIs entre módulos, use `@permission_classes([AllowAny])` e `@csrf_exempt` para endpoints que recebem POST de outros servidores.

Se usar `requests.post()`, o CSRF não se aplica (é proteção para formulários HTML do navegador). Mas certifique-se de estar usando `@api_view` do DRF, que desabilita CSRF automaticamente.

### Erro: "DisallowedHost"

No `settings.py` do PythonAnywhere, adicione o hostname:

```python
ALLOWED_HOSTS = ['<seu-usuario>.pythonanywhere.com']
```

### Os dados estão desatualizados

As chamadas via `requests` são síncronas — cada chamada busca o dado mais recente do outro módulo. Se parecer desatualizado, verifique:
- Cache do navegador
- Se o outro módulo aplicou `migrate` após mudanças nos models

### Módulo externo retorna HTML ao invés de JSON

O módulo externo pode não ter uma API REST. Confirme com o grupo responsável que eles têm endpoints retornando JSON (usando DRF ou `JsonResponse`).

---

## Resumo — Tabela de Endpoints para Integração

### 📤 APIs que NÓS oferecemos (outros módulos consomem)

| Endpoint | Método | Quem consome |
|----------|--------|-------------|
| `/api/produtos/` | GET | Qualquer módulo |
| `/api/categorias/` | GET | Qualquer módulo |
| `/api/produto/<id>/` | GET | Qualquer módulo |
| `/api/estoque-disponivel/<id>/` | GET | Módulo 6 (Vendas) |
| `/api/entrada-compra/` | POST | Módulo 5 (Compras) |
| `/api/saida-venda/` | POST | Módulo 6 (Vendas) |
| `/api/reservar/` | POST | Módulo 2 (Clientes) |
| `/api/historico/<id>/` | GET | Módulos 7, 8, 9 |
| `/api/financeiro/resumo/` | GET | Módulo 9 (Financeiro) |

### 📥 APIs que NÓS consumimos (de outros módulos)

| Módulo | Endpoint esperado | Para que usamos |
|--------|-------------------|-----------------|
| 2 — Clientes | `GET /api/clientes/<id>/` | Buscar nome do cliente na reserva |
| 3 — Fornecedores | `GET /api/fornecedores/` | Listar fornecedores no cadastro de produto |
| 3 — Fornecedores | `GET /api/fornecedores/<id>/` | Exibir nome do fornecedor na listagem |
| 5 — Compras | `GET /api/compras/` | Consultar compras pendentes |
| 6 — Vendas | `GET /api/vendas/` | Listar vendas recentes no dashboard |
| 9 — Financeiro | `GET /api/relatorios/` | Consultar relatórios financeiros |

> **Nota:** Os endpoints listados na tabela "APIs que NÓS consumimos" dependem da implementação dos outros grupos. Combine com cada grupo os endpoints exatos e o formato do JSON.
