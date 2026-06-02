from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.db.models import Sum, F, DecimalField
from .models import Produto, MovimentacaoEstoque, Categoria

from rest_framework import viewsets
from .serializers import ProdutoSerializer, MovimentacaoEstoqueSerializer, CategoriaSerializer
from rest_framework.permissions import IsAuthenticated

# ───────────────────────────── AUTH ──────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/estoque/listar')

    erro = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/estoque/listar')
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

    # 🔍 NOVO: Filtro de Busca por Nome ou Descrição
    termo_busca = request.GET.get('busca')
    if termo_busca:
        # Busca produtos que contenham o termo no nome OU na descrição (ignore maiúsculas/minúsculas)
        produtos = produtos.filter(nome__icontains=termo_busca) | produtos.filter(descricao__icontains=termo_busca)

    # Filtros de categoria já existentes
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        produtos = produtos.filter(categoria_id=categoria_id)

    # Passamos também o 'termo_busca' para o HTML para manter o texto na caixinha após pesquisar
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
                usuario=request.user  # <-- ATUALIZADO: Grava o utilizador do RH/Funcionário
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
                produto.quantidade = quantity = quantidade

            produto.save()

            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo=tipo,
                quantidade=quantidade,
                observacao=observacao,
                usuario=request.user  # <-- ATUALIZADO: Grava o utilizador do RH/Funcionário
            )

            return HttpResponseRedirect('/estoque/listar')

    return render(request, 'movimentacao.html', {'produto': produto, 'erro': erro})


# ==================== VIEWS TRADICIONAIS (HTML) ====================

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


# ==================== ENDPOINTS DA API (DRF) ====================

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer

class MovimentacaoEstoqueViewSet(viewsets.ModelViewSet):
    queryset = MovimentacaoEstoque.objects.all()
    serializer_class = MovimentacaoEstoqueSerializer

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer