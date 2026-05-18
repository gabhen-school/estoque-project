from django.urls import path
from . import views

urlpatterns = [
    path('listar', views.listar_produtos, name='listar_produtos'),
    path('cadastrar', views.cadastrar_produto, name='cadastrar_produto'),
    path('editar/<int:id>', views.editar_produto, name='editar_produto'),
    path('excluir/<int:id>', views.excluir_produto, name='excluir_produto'),
    path('movimentacoes', views.listar_movimentacoes, name='listar_movimentacoes'),
    path('movimentar/<int:id>', views.registrar_movimentacao, name='registrar_movimentacao'),
]
