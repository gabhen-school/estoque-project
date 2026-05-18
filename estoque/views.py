from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from .models import Produto, MovimentacaoEstoque


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
    produtos = Produto.objects.all()
    return render(request, 'listarProdutos.html', {'produtos': produtos})


@login_required
def cadastrar_produto(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        quantidade = int(request.POST.get('quantidade', 0))
        quantidade_minima = int(request.POST.get('quantidade_minima', 0))
        preco_unitario = request.POST.get('preco_unitario', '0')

        produto = Produto(
            nome=nome,
            descricao=descricao,
            quantidade=quantidade,
            quantidade_minima=quantidade_minima,
            preco_unitario=preco_unitario,
        )
        produto.save()

        # Registra movimentação inicial se houver quantidade
        if quantidade > 0:
            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo='ENTRADA',
                quantidade=quantidade,
                observacao='Cadastro inicial do produto'
            )

        return HttpResponseRedirect('/estoque/listar')

    return render(request, 'cadastroProduto.html')


@login_required
def editar_produto(request, id):
    produto = Produto.objects.get(id=id)

    if request.method == 'POST':
        produto.nome = request.POST.get('nome')
        produto.descricao = request.POST.get('descricao')
        produto.quantidade_minima = int(request.POST.get('quantidade_minima', 0))
        produto.preco_unitario = request.POST.get('preco_unitario', '0')
        produto.save()
        return HttpResponseRedirect('/estoque/listar')

    return render(request, 'editarProduto.html', {'produto': produto})


@login_required
def excluir_produto(request, id):
    produto = Produto.objects.get(id=id)
    produto.delete()
    return HttpResponseRedirect('/estoque/listar')


# ─────────────────────── MOVIMENTAÇÃO ────────────────────────────

@login_required
def listar_movimentacoes(request):
    movimentacoes = MovimentacaoEstoque.objects.all().order_by('-data')
    return render(request, 'listarMovimentacoes.html', {'movimentacoes': movimentacoes})


@login_required
def registrar_movimentacao(request, id):
    produto = Produto.objects.get(id=id)
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
                observacao=observacao
            )

            return HttpResponseRedirect('/estoque/listar')

    return render(request, 'movimentacao.html', {'produto': produto, 'erro': erro})
