from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.db.models import Sum, F, DecimalField

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Produto, MovimentacaoEstoque, Categoria
from .serializers import ProdutoSerializer, MovimentacaoEstoqueSerializer, CategoriaSerializer


# ───────────────────────────── AUTH ──────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/estoque/dashboard')

    erro = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/estoque/dashboard')
        else:
            erro = 'Usuário ou senha inválidos.'

    return render(request, 'login.html', {'erro': erro})


def logout_view(request):
    logout(request)
    return redirect('/login')


# ───────────────────────────── PRODUTO ───────────────────────────

@login_required
def listar_produtos(request):
    produtos = Produto.objects.select_related('categoria').all()
    categorias = Categoria.objects.all()

    termo_busca = request.GET.get('busca')
    if termo_busca:
        produtos = produtos.filter(nome__icontains=termo_busca) | produtos.filter(descricao__icontains=termo_busca)

    categoria_id = request.GET.get('categoria')
    if categoria_id:
        produtos = produtos.filter(categoria_id=categoria_id)

    return render(request, 'listarProdutos.html', {
        'produtos': produtos,
        'categorias': categorias,
        'termo_busca': termo_busca
    })


@login_required
def cadastrar_produto(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        quantidade = int(request.POST.get('quantidade', 0))
        quantidade_minima = int(request.POST.get('quantidade_minima', 0))
        preco_unitario = request.POST.get('preco_unitario', '0')
        categoria_id = request.POST.get('categoria')
        localizacao = request.POST.get('localizacao_deposito')

        produto = Produto(
            nome=nome,
            descricao=descricao,
            quantidade=quantidade,
            quantidade_minima=quantidade_minima,
            preco_unitario=preco_unitario,
            localizacao_deposito=localizacao,
        )
        if categoria_id:
            produto.categoria_id = int(categoria_id)

        produto.save()

        if quantidade > 0:
            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo='ENTRADA',
                quantidade=quantidade,
                observacao='Cadastro inicial do produto',
                usuario=request.user
            )
        return HttpResponseRedirect('/estoque/listar')

    categorias = Categoria.objects.all()
    return render(request, 'cadastroProduto.html', {'categorias': categorias})


@login_required
def editar_produto(request, id):
    produto = get_object_or_404(Produto, id=id)

    if request.method == 'POST':
        produto.nome = request.POST.get('nome')
        produto.descricao = request.POST.get('descricao')
        produto.quantidade_minima = int(request.POST.get('quantidade_minima', 0))
        produto.localizacao_deposito = request.POST.get('localizacao_deposito')

        preco_informado = request.POST.get('preco_unitario')
        produto.preco_unitario = preco_informado if preco_informado and preco_informado.strip() != '' else '0'

        categoria_id = request.POST.get('categoria')
        if categoria_id:
            produto.categoria_id = int(categoria_id)
        else:
            produto.categoria = None

        produto.save()
        return HttpResponseRedirect('/estoque/listar')

    categorias = Categoria.objects.all()
    return render(request, 'editarProduto.html', {'produto': produto, 'categorias': categorias})


@login_required
def excluir_produto(request, id):
    produto = get_object_or_404(Produto, id=id)
    produto.delete()
    return HttpResponseRedirect('/estoque/listar')


# ─────────────────────── MOVIMENTAÇÃO ────────────────────────────

@login_required
def listar_movimentacoes(request):
    movimentacoes = MovimentacaoEstoque.objects.all().order_by('-data')
    return render(request, 'listarMovimentacoes.html', {'movimentacoes': movimentacoes})


@login_required
def registrar_movimentacao(request, id):
    produto = get_object_or_404(Produto, id=id)
    erro = None

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        quantidade = int(request.POST.get('quantidade', 0))
        observacao = request.POST.get('observacao', '')

        if quantidade <= 0:
            erro = 'A quantidade deve ser maior que zero.'
        elif tipo == 'SAIDA' and quantidade > produto.quantidade:
            erro = f'Quantidade insuficiente em estoque. Disponível: {produto.quantidade}'
        else:
            if tipo == 'ENTRADA':
                produto.quantidade += quantidade
            elif tipo == 'SAIDA':
                produto.quantidade -= quantidade
            elif tipo == 'AJUSTE':
                produto.quantidade = quantidade

            produto.save()

            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo=tipo,
                quantidade=quantidade,
                observacao=observacao,
                usuario=request.user
            )

            return HttpResponseRedirect('/estoque/listar')

    return render(request, 'movimentacao.html', {'produto': produto, 'erro': erro})


# ─────────────────────── DASHBOARD ───────────────────────────────

@login_required
def dashboard(request):
    total_produtos = Produto.objects.count()
    total_itens_fisicos = Produto.objects.aggregate(Sum('quantidade'))['quantidade__sum'] or 0

    produtos_baixo_estoque = [p for p in Produto.objects.all() if p.estoque_baixo]
    total_alertas = len(produtos_baixo_estoque)

    valor_total_estoque = Produto.objects.annotate(
        total_item=F('quantidade') * F('preco_unitario')
    ).aggregate(total=Sum('total_item', output_field=DecimalField()))['total'] or 0.00

    ultimas_movimentacoes = MovimentacaoEstoque.objects.select_related('produto').order_by('-data')[:5]

    context = {
        'total_produtos': total_produtos,
        'total_itens_fisicos': total_itens_fisicos,
        'total_alertas': total_alertas,
        'valor_total_estoque': valor_total_estoque,
        'ultimas_movimentacoes': ultimas_movimentacoes,
        'produtos_baixo_estoque': produtos_baixo_estoque,
    }
    return render(request, 'dashboard.html', context)


@login_required
def historico_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    movimentacoes = MovimentacaoEstoque.objects.filter(produto=produto).order_by('-data')
    return render(request, 'historicoProduto.html', {'produto': produto, 'movimentacoes': movimentacoes})


@login_required
def gerenciar_categorias(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            Categoria.objects.create(nome=nome)
        return redirect('/estoque/categorias')

    categorias = Categoria.objects.all()
    return render(request, 'gerenciarCategorias.html', {'categorias': categorias})


@login_required
def excluir_categoria(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    categoria.delete()
    return redirect('/estoque/categorias')


# ══════════════════════════════════════════════════════════════════
#  APIs REST — para comunicação com outros módulos do sistema
# ══════════════════════════════════════════════════════════════════

# ── ViewSets padrão (CRUD completo via /api/) ─────────────────────

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer


class MovimentacaoEstoqueViewSet(viewsets.ModelViewSet):
    queryset = MovimentacaoEstoque.objects.all()
    serializer_class = MovimentacaoEstoqueSerializer


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


# ── Módulo de Vendas / Saída ──────────────────────────────────────
#
#   POST /api/entrada-compra/
#   Usado pelo módulo de Compras (grupo 5) para registrar entrada de mercadoria.
#   Body: { "produto_id": 3, "quantidade": 10, "observacao": "NF-123", "fornecedor_id": 7 }
#
@api_view(['POST'])
@permission_classes([AllowAny])
def api_entrada_compra(request):
    """
    Módulo de Compras chama este endpoint ao registrar uma compra.
    Cria automaticamente uma MovimentacaoEstoque tipo ENTRADA.
    """
    produto_id  = request.data.get('produto_id')
    quantidade  = request.data.get('quantidade')
    observacao  = request.data.get('observacao', 'Entrada via módulo de Compras')
    fornecedor_id = request.data.get('fornecedor_id')

    if not produto_id or not quantidade:
        return Response(
            {'erro': 'produto_id e quantidade são obrigatórios.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        quantidade = int(quantidade)
        if quantidade <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return Response({'erro': 'quantidade deve ser um inteiro positivo.'}, status=status.HTTP_400_BAD_REQUEST)

    produto = get_object_or_404(Produto, id=produto_id)

    # Vincula fornecedor ao produto se informado
    if fornecedor_id:
        produto.fornecedor_id = fornecedor_id

    produto.quantidade += quantidade
    produto.save()

    mov = MovimentacaoEstoque.objects.create(
        produto=produto,
        tipo='ENTRADA',
        quantidade=quantidade,
        observacao=observacao,
    )

    return Response({
        'mensagem': 'Entrada registrada com sucesso.',
        'produto_id': produto.id,
        'produto_nome': produto.nome,
        'quantidade_adicionada': quantidade,
        'quantidade_atual': produto.quantidade,
        'custo_total_financeiro': str(mov.custo_total_financeiro),
        'movimentacao_id': mov.id,
    }, status=status.HTTP_201_CREATED)


# ── Módulo de Vendas / Saída ──────────────────────────────────────
#
#   POST /api/saida-venda/
#   Usado pelo módulo de Vendas para dar baixa no estoque ao confirmar uma venda.
#   Body: { "produto_id": 3, "quantidade": 2, "observacao": "Pedido #99", "cliente_id": 5 }
#
@api_view(['POST'])
@permission_classes([AllowAny])
def api_saida_venda(request):
    """
    Módulo de Vendas chama este endpoint ao fechar uma venda.
    Cria automaticamente uma MovimentacaoEstoque tipo SAIDA.
    Retorna erro se não houver saldo suficiente.
    """
    produto_id = request.data.get('produto_id')
    quantidade = request.data.get('quantidade')
    observacao = request.data.get('observacao', 'Saída via módulo de Vendas')
    cliente_id = request.data.get('cliente_id')

    if not produto_id or not quantidade:
        return Response(
            {'erro': 'produto_id e quantidade são obrigatórios.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        quantidade = int(quantidade)
        if quantidade <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return Response({'erro': 'quantidade deve ser um inteiro positivo.'}, status=status.HTTP_400_BAD_REQUEST)

    produto = get_object_or_404(Produto, id=produto_id)

    if quantidade > produto.quantidade:
        return Response({
            'erro': 'Saldo insuficiente em estoque.',
            'disponivel': produto.quantidade,
            'solicitado': quantidade,
        }, status=status.HTTP_409_CONFLICT)

    # Vincula reserva ao cliente se informado
    if cliente_id:
        produto.cliente_reserva_id = cliente_id

    produto.quantidade -= quantidade
    produto.save()

    mov = MovimentacaoEstoque.objects.create(
        produto=produto,
        tipo='SAIDA',
        quantidade=quantidade,
        observacao=observacao,
    )

    return Response({
        'mensagem': 'Saída registrada com sucesso.',
        'produto_id': produto.id,
        'produto_nome': produto.nome,
        'quantidade_retirada': quantidade,
        'quantidade_atual': produto.quantidade,
        'custo_total_financeiro': str(mov.custo_total_financeiro),
        'movimentacao_id': mov.id,
        'estoque_baixo': produto.estoque_baixo,
    }, status=status.HTTP_201_CREATED)


# ── Módulo Financeiro ─────────────────────────────────────────────
#
#   GET /api/financeiro/resumo/
#   Retorna valor total do estoque e custo de todas as movimentações.
#   O módulo financeiro (grupo 6) consome este endpoint.
#
@api_view(['GET'])
@permission_classes([AllowAny])
def api_resumo_financeiro(request):
    """
    Módulo Financeiro usa este endpoint para calcular o capital em estoque
    e o fluxo de custo das movimentações.
    """
    valor_total_estoque = Produto.objects.annotate(
        total_item=F('quantidade') * F('preco_unitario')
    ).aggregate(total=Sum('total_item', output_field=DecimalField()))['total'] or 0

    total_entradas = MovimentacaoEstoque.objects.filter(tipo='ENTRADA').aggregate(
        total=Sum('custo_total_financeiro', output_field=DecimalField())
    )['total'] or 0

    total_saidas = MovimentacaoEstoque.objects.filter(tipo='SAIDA').aggregate(
        total=Sum('custo_total_financeiro', output_field=DecimalField())
    )['total'] or 0

    movimentacoes = MovimentacaoEstoque.objects.select_related('produto').order_by('-data').values(
        'id', 'tipo', 'quantidade', 'custo_total_financeiro', 'data',
        'produto__id', 'produto__nome', 'produto__preco_unitario'
    )

    return Response({
        'valor_total_estoque': str(valor_total_estoque),
        'total_custo_entradas': str(total_entradas),
        'total_custo_saidas': str(total_saidas),
        'movimentacoes': list(movimentacoes),
    })


# ── Consulta de produto por ID (qualquer módulo) ──────────────────
#
#   GET /api/produto/<id>/
#   Qualquer módulo pode consultar dados de um produto específico.
#   (Já existe via ProdutoViewSet, mas este retorna campos extras formatados)
#
@api_view(['GET'])
@permission_classes([AllowAny])
def api_produto_detalhe(request, produto_id):
    """
    Retorna dados completos de um produto para integração entre módulos.
    Útil para: Vendas consultar preço, Financeiro consultar valor, RH ver localização.
    """
    produto = get_object_or_404(Produto, id=produto_id)
    serializer = ProdutoSerializer(produto)
    return Response(serializer.data)


# ── Consulta de estoque disponível (Vendas antes de fechar pedido) ─
#
#   GET /api/estoque-disponivel/<produto_id>/
#   Vendas chama antes de confirmar pedido para checar saldo.
#
@api_view(['GET'])
@permission_classes([AllowAny])
def api_estoque_disponivel(request, produto_id):
    """
    Retorna a quantidade disponível de um produto.
    Vendas usa para validar se pode concluir o pedido antes de chamar /saida-venda/.
    """
    produto = get_object_or_404(Produto, id=produto_id)
    return Response({
        'produto_id': produto.id,
        'produto_nome': produto.nome,
        'quantidade_disponivel': produto.quantidade,
        'quantidade_minima': produto.quantidade_minima,
        'estoque_baixo': produto.estoque_baixo,
        'preco_unitario': str(produto.preco_unitario),
        'localizacao_deposito': produto.localizacao_deposito,
    })


# ── Reserva de produto para cliente (Módulo Cliente/Vendas) ──────
#
#   POST /api/reservar/
#   Body: { "produto_id": 3, "cliente_id": 12, "reservar": true }
#
@api_view(['POST'])
@permission_classes([AllowAny])
def api_reservar_produto(request):
    """
    Módulo de Clientes/Vendas usa para marcar/desmarcar reserva de um produto.
    Não altera a quantidade — apenas sinaliza que está reservado.
    """
    produto_id = request.data.get('produto_id')
    cliente_id = request.data.get('cliente_id')
    reservar   = request.data.get('reservar', True)

    if not produto_id:
        return Response({'erro': 'produto_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

    produto = get_object_or_404(Produto, id=produto_id)
    produto.status_reserva    = bool(reservar)
    produto.cliente_reserva_id = cliente_id if reservar else None
    produto.save()

    return Response({
        'mensagem': 'Reserva atualizada.',
        'produto_id': produto.id,
        'produto_nome': produto.nome,
        'status_reserva': produto.status_reserva,
        'cliente_reserva_id': produto.cliente_reserva_id,
    })


# ── Histórico de movimentações de um produto (qualquer módulo) ───
#
#   GET /api/historico/<produto_id>/
#
@api_view(['GET'])
@permission_classes([AllowAny])
def api_historico_produto(request, produto_id):
    """
    Retorna o histórico completo de movimentações de um produto.
    Útil para auditoria (RH/Funcionários) e relatórios (Financeiro).
    """
    produto = get_object_or_404(Produto, id=produto_id)
    movimentacoes = MovimentacaoEstoque.objects.filter(produto=produto).order_by('-data')
    serializer = MovimentacaoEstoqueSerializer(movimentacoes, many=True)
    return Response({
        'produto_id': produto.id,
        'produto_nome': produto.nome,
        'quantidade_atual': produto.quantidade,
        'movimentacoes': serializer.data,
    })
