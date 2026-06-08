"""
seed_dados.py — Popula o banco com dados fictícios realistas
Uso: python manage.py shell < seed_dados.py
     (rodar dentro da pasta estoque-project/, com o venv ativo)
"""

import random
from decimal import Decimal
from django.contrib.auth.models import User
from estoque.models import Categoria, Produto, MovimentacaoEstoque

# ── Limpa dados anteriores (ordem importa por FK) ─────────
print("🗑️  Limpando dados anteriores...")
MovimentacaoEstoque.objects.all().delete()
Produto.objects.all().delete()
Categoria.objects.all().delete()
print("   Feito.\n")

# ── Usuário admin (para vincular movimentações) ────────────
admin, _ = User.objects.get_or_create(username="admin")

# ══════════════════════════════════════════════════════════
# 1. CATEGORIAS
# ══════════════════════════════════════════════════════════
print("📂 Criando categorias...")

categorias_nomes = [
    "Eletrônicos",
    "Ferramentas",
    "Papelaria",
    "Limpeza",
    "Informática",
    "Móveis e Escritório",
    "Segurança",
    "Elétrica",
]

categorias = {}
for nome in categorias_nomes:
    c = Categoria.objects.create(nome=nome)
    categorias[nome] = c
    print(f"   ✔ {nome}")

# ══════════════════════════════════════════════════════════
# 2. PRODUTOS
# ══════════════════════════════════════════════════════════
print("\n📦 Criando produtos...")

# (nome, descricao, categoria, qtd, qtd_minima, preco, localizacao, fornecedor_id)
produtos_data = [
    # Eletrônicos
    ("Projetor Epson X41+",    "Projetor 3600 lumens, HDMI/VGA",         "Eletrônicos",        4,  2,  2890.00, "Sala TI - Armário A1", 10),
    ("TV 55\" Samsung 4K",     "Smart TV QLED, WiFi, 3x HDMI",           "Eletrônicos",        2,  1,  3499.00, "Depósito B, Prateleira 1", 10),
    ("Ar-condicionado 12000BTU","Split inverter, instalação inclusa",     "Eletrônicos",        3,  1,  1750.00, "Depósito B, Prateleira 2", 11),
    ("Estabilizador 1500VA",   "Bivolt automático, 8 tomadas",           "Eletrônicos",        6,  2,   320.00, "Sala TI - Armário A2", 10),
    ("Extensão 5m 3 pinos",    "Cabo reforçado, proteção contra surto",  "Elétrica",           15, 5,    45.00, "Corredor C, Prateleira 3", 12),

    # Informática
    ("Notebook Dell Inspiron",  "i5 12ª gen, 8GB RAM, 256GB SSD",        "Informática",        8,  3,  3200.00, "Sala TI - Armário B1", 13),
    ("Mouse sem fio Logitech",  "Receptor nano USB, pilha inclusa",       "Informática",       20,  5,    89.00, "Sala TI - Gaveta 2",   13),
    ("Teclado ABNT2 USB",       "Membrana, layout PT-BR",                 "Informática",       18,  5,    65.00, "Sala TI - Gaveta 2",   13),
    ("Monitor 24\" Full HD",    "IPS, 75Hz, HDMI + VGA",                  "Informática",       10,  3,   879.00, "Sala TI - Armário B2", 13),
    ("Switch 8 portas TP-Link", "Gigabit, plug-and-play",                "Informática",        5,  2,   189.00, "Sala TI - Rack",       13),
    ("Cabo HDMI 2m",            "Alta velocidade, 4K compatível",         "Informática",       30, 10,    22.00, "Sala TI - Gaveta 3",   13),
    ("Pen Drive 64GB",          "USB 3.0, Kingston",                      "Informática",       25,  8,    39.00, "Sala TI - Gaveta 1",   13),

    # Ferramentas
    ("Furadeira de Impacto",    "Bosch 650W, reversível, 220V",           "Ferramentas",        3,  1,   389.00, "Depósito A, Prateleira 4", 14),
    ("Parafusadeira Elétrica",  "Bateria 20V, 2 velocidades",             "Ferramentas",        4,  1,   290.00, "Depósito A, Prateleira 4", 14),
    ("Martelo 500g",            "Cabo de madeira reforçado",              "Ferramentas",        8,  2,    35.00, "Depósito A, Prateleira 2", 14),
    ("Trena 5m Stanley",        "Trava automática, gancho magnético",     "Ferramentas",        6,  2,    28.00, "Depósito A, Prateleira 2", 14),
    ("Nível de bolha 60cm",     "Alumínio, 3 bolhas de vidro",            "Ferramentas",        5,  2,    42.00, "Depósito A, Prateleira 3", 14),

    # Papelaria
    ("Resma de Papel A4",       "75g/m², 500 folhas, Chamex",             "Papelaria",         50, 10,    28.00, "Corredor D, Prateleira 1", 15),
    ("Caneta Azul BIC",         "Ponta média, caixa com 50un",            "Papelaria",        120, 30,    32.00, "Corredor D, Prateleira 2", 15),
    ("Grampeador de Mesa",      "Capacidade 25 folhas, staples incluso",  "Papelaria",         10,  3,    24.00, "Corredor D, Prateleira 3", 15),
    ("Pasta AZ Larga",          "Lombada 8cm, mecanismo reforçado",       "Papelaria",         35, 10,    18.00, "Corredor D, Prateleira 4", 15),
    ("Papel Sulfite Color 75g", "100 folhas coloridas sortidas",          "Papelaria",         20,  5,    15.00, "Corredor D, Prateleira 2", 15),
    ("Post-it 76x76mm",         "Bloco 100 folhas, amarelo",              "Papelaria",         40, 10,     9.50, "Corredor D, Prateleira 2", 15),

    # Limpeza
    ("Detergente 500ml",        "Neutro, concentrado, caixa 12un",        "Limpeza",           24,  6,    48.00, "Depósito C, Prateleira 1", 16),
    ("Álcool 70% 1L",           "Etílico hidratado, galão",               "Limpeza",           30,  8,    18.00, "Depósito C, Prateleira 1", 16),
    ("Papel Toalha Industrial", "Rolo 60m, 2 folhas, fardo 6un",          "Limpeza",           18,  4,    62.00, "Depósito C, Prateleira 2", 16),
    ("Saco de Lixo 100L",       "Preto, reforçado, pacote 10un",          "Limpeza",           40, 10,    12.00, "Depósito C, Prateleira 3", 16),
    ("Rodo cabo 1,20m",         "Borracha dupla face",                    "Limpeza",            6,  2,    22.00, "Depósito C, Prateleira 4", 16),
    ("Vassoura Nylon",          "Cabo longo 1,40m, cerdas macias",        "Limpeza",            6,  2,    18.00, "Depósito C, Prateleira 4", 16),

    # Móveis e Escritório
    ("Cadeira Escritório",      "Ergonômica, rodízio, regulagem altura",  "Móveis e Escritório", 12, 3,   650.00, "Depósito B, Fundo",    17),
    ("Mesa Escrivaninha 1,5m",  "MDP, 2 gavetas, pés metálicos",          "Móveis e Escritório",  6, 2,   490.00, "Depósito B, Fundo",    17),
    ("Armário de Aço 2 portas", "Chave dupla, 4 prateleiras",             "Móveis e Escritório",  3, 1,   980.00, "Depósito B, Lateral",  17),
    ("Quadro Branco 120x90cm",  "Moldura alumínio, apagador incluso",     "Móveis e Escritório",  4, 1,   185.00, "Depósito B, Lateral",  17),

    # Segurança
    ("Câmera IP Externa",       "Full HD, infravermelho 30m, IP66",       "Segurança",           8, 2,   320.00, "Sala TI - Armário C",  18),
    ("Extintor CO2 6kg",        "Válvula latão, carga nova",              "Segurança",           5, 2,   280.00, "Corredor A, Parede",   18),
    ("Cadeado Aço 40mm",        "Alta resistência, 2 chaves",             "Segurança",          10, 3,    38.00, "Sala TI - Gaveta 4",   18),
]

produtos_criados = []
for nome, desc, cat_nome, qtd, qtd_min, preco, local, forn in produtos_data:
    p = Produto.objects.create(
        nome=nome,
        descricao=desc,
        categoria=categorias[cat_nome],
        quantidade=qtd,
        quantidade_minima=qtd_min,
        preco_unitario=Decimal(str(preco)),
        localizacao_deposito=local,
        fornecedor_id=forn,
        status_reserva=False,
    )
    produtos_criados.append(p)
    alerta = " ⚠️  ESTOQUE BAIXO" if p.estoque_baixo else ""
    print(f"   ✔ {nome} (qtd: {qtd}){alerta}")

# ══════════════════════════════════════════════════════════
# 3. MOVIMENTAÇÕES
# ══════════════════════════════════════════════════════════
print("\n🔄 Criando histórico de movimentações...")

movimentacoes_data = [
    # (produto_nome, tipo, qtd, observacao)
    ("Resma de Papel A4",        "ENTRADA", 100, "NF-001 — Compra mensal papelaria"),
    ("Resma de Papel A4",        "SAIDA",    30, "Solicitação setor administrativo"),
    ("Resma de Papel A4",        "SAIDA",    20, "Solicitação sala de aula 03"),
    ("Caneta Azul BIC",          "ENTRADA", 200, "NF-002 — Reposição trimestral"),
    ("Caneta Azul BIC",          "SAIDA",    80, "Distribuição geral setores"),
    ("Notebook Dell Inspiron",   "ENTRADA",  10, "NF-003 — Compra licitação 2024"),
    ("Notebook Dell Inspiron",   "SAIDA",     2, "Emprestado ao setor financeiro"),
    ("Mouse sem fio Logitech",   "ENTRADA",  30, "NF-003 — Acompanha notebooks"),
    ("Mouse sem fio Logitech",   "SAIDA",    10, "Reposição laboratório infra"),
    ("Álcool 70% 1L",            "ENTRADA",  50, "NF-004 — Compra limpeza"),
    ("Álcool 70% 1L",            "SAIDA",    20, "Distribuição para setores"),
    ("Extintor CO2 6kg",         "ENTRADA",   6, "NF-005 — Renovação anual CIPA"),
    ("Extintor CO2 6kg",         "SAIDA",     1, "Substituição corredor B — vencido"),
    ("Cadeira Escritório",       "ENTRADA",  15, "NF-006 — Compra mobiliário"),
    ("Cadeira Escritório",       "SAIDA",     3, "Instalação sala de reunião"),
    ("Cabo HDMI 2m",             "ENTRADA",  50, "NF-007 — Reposição TI"),
    ("Cabo HDMI 2m",             "SAIDA",    20, "Distribuição salas de aula"),
    ("Saco de Lixo 100L",        "ENTRADA",  80, "NF-008 — Suprimentos limpeza"),
    ("Saco de Lixo 100L",        "SAIDA",    40, "Uso mensal zeladoria"),
    ("Projetor Epson X41+",      "ENTRADA",   5, "NF-009 — Compra licitação AV"),
    ("Projetor Epson X41+",      "SAIDA",     1, "Empréstimo auditório externo"),
    ("Furadeira de Impacto",     "ENTRADA",   4, "NF-010 — Manutenção predial"),
    ("Furadeira de Impacto",     "AJUSTE",    3, "Ajuste após inventário físico"),
    ("Pen Drive 64GB",           "ENTRADA",  40, "NF-011 — TI"),
    ("Pen Drive 64GB",           "SAIDA",    15, "Distribuição professores"),
    ("Detergente 500ml",         "ENTRADA",  36, "NF-012 — Limpeza"),
    ("Detergente 500ml",         "SAIDA",    12, "Uso mensal"),
    ("Monitor 24\" Full HD",     "ENTRADA",  12, "NF-013 — TI"),
    ("Monitor 24\" Full HD",     "SAIDA",     2, "Instalação diretoria"),
    ("Papel Toalha Industrial",  "ENTRADA",  24, "NF-014 — Limpeza"),
    ("Papel Toalha Industrial",  "SAIDA",     6, "Distribuição banheiros"),
    ("Switch 8 portas TP-Link",  "ENTRADA",   6, "NF-015 — Infraestrutura"),
    ("Switch 8 portas TP-Link",  "SAIDA",     1, "Instalação bloco B"),
    ("Grampeador de Mesa",       "AJUSTE",   10, "Ajuste inventário — 2 unidades extraviadas"),
    ("Câmera IP Externa",        "ENTRADA",  10, "NF-016 — Segurança"),
    ("Câmera IP Externa",        "SAIDA",     2, "Instalação portaria principal"),
]

for prod_nome, tipo, qtd, obs in movimentacoes_data:
    try:
        produto = Produto.objects.get(nome=prod_nome)
        m = MovimentacaoEstoque(
            produto=produto,
            tipo=tipo,
            quantidade=qtd,
            observacao=obs,
            usuario=admin,
        )
        m.save()
        print(f"   ✔ [{tipo:7}] {prod_nome} — {qtd}un")
    except Produto.DoesNotExist:
        print(f"   ✖ Produto não encontrado: {prod_nome}")

# ══════════════════════════════════════════════════════════
# RESUMO
# ══════════════════════════════════════════════════════════
print("\n" + "="*54)
print("  SEED CONCLUÍDO")
print("="*54)
print(f"  Categorias:     {Categoria.objects.count()}")
print(f"  Produtos:       {Produto.objects.count()}")
print(f"  Movimentações:  {MovimentacaoEstoque.objects.count()}")
em_alerta = Produto.objects.filter
baixos = [p for p in Produto.objects.all() if p.estoque_baixo]
print(f"  Estoque baixo:  {len(baixos)} produto(s)")
for p in baixos:
    print(f"    ⚠️  {p.nome} (qtd: {p.quantidade} / mín: {p.quantidade_minima})")
print("="*54)
print("  Acesse: http://127.0.0.1:8000/")
print("="*54 + "\n")
