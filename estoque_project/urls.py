from django.contrib import admin
from django.urls import path, include
from estoque import views as auth_views
from rest_framework.routers import DefaultRouter

# CONFIGURAÇÃO DA API: Criamos o router aqui para a linha 'path(api/)' funcionar
router = DefaultRouter()
router.register(r'produtos', auth_views.ProdutoViewSet)
router.register(r'movimentacoes', auth_views.MovimentacaoEstoqueViewSet)
router.register(r'categorias', auth_views.CategoriaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Isso aqui inclui as rotas internas que já existem no seu app estoque
    path('estoque/', include('estoque.urls')),
    
    # Rotas de Autenticação na raiz
    path('login', auth_views.login_view, name='login'),
    path('logout', auth_views.logout_view, name='logout'),
    path('', auth_views.login_view),  # redireciona raiz para login
    
    # Endpoints da API REST para os outros grupos
    path('api/', include(router.urls)),
]