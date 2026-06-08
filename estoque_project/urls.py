from django.contrib import admin
from django.urls import path, include
from estoque import views as auth_views
from rest_framework.routers import DefaultRouter

# ── Router DRF: CRUD completo automático ─────────────────────────
router = DefaultRouter()
router.register(r'produtos',      auth_views.ProdutoViewSet)
router.register(r'movimentacoes', auth_views.MovimentacaoEstoqueViewSet)
router.register(r'categorias',    auth_views.CategoriaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Interface HTML
    path('estoque/', include('estoque.urls')),
    path('login',   auth_views.login_view,  name='login'),
    path('logout',  auth_views.logout_view, name='logout'),
    path('',        auth_views.login_view),

    # ── API REST ─────────────────────────────────────────────────
    # CRUD automático (DRF Router):
    #   GET/POST   /api/produtos/
    #   GET/PUT/DELETE /api/produtos/<id>/
    #   (mesmo para /api/movimentacoes/ e /api/categorias/)
    path('api/', include(router.urls)),

    # Endpoints de integração entre módulos:
    path('api/entrada-compra/',               auth_views.api_entrada_compra,     name='api_entrada_compra'),
    path('api/saida-venda/',                  auth_views.api_saida_venda,        name='api_saida_venda'),
    path('api/financeiro/resumo/',            auth_views.api_resumo_financeiro,  name='api_resumo_financeiro'),
    path('api/estoque-disponivel/<int:produto_id>/', auth_views.api_estoque_disponivel, name='api_estoque_disponivel'),
    path('api/produto/<int:produto_id>/',     auth_views.api_produto_detalhe,    name='api_produto_detalhe'),
    path('api/reservar/',                     auth_views.api_reservar_produto,   name='api_reservar_produto'),
    path('api/historico/<int:produto_id>/',   auth_views.api_historico_produto,  name='api_historico_produto'),
]
