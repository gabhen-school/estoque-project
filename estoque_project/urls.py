from django.contrib import admin
from django.urls import path, include
from estoque import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('estoque/', include('estoque.urls')),
    path('login', auth_views.login_view, name='login'),
    path('logout', auth_views.logout_view, name='logout'),
    path('', auth_views.login_view),  # redireciona raiz para login
]
