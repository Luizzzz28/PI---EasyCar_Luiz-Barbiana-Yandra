#URLs da API e do Django Admin para login
from django.contrib import admin
from django.urls import include, path

from locadora import frontend

urlpatterns = [
    path('', frontend.dashboard, name='dashboard'),
    path('carros/', frontend.carros_disponiveis, name='carros-disponiveis'),
    path('carros/novo/', frontend.novo_carro, name='novo-carro'),
    path('clientes/', frontend.clientes, name='clientes'),
    path('alugueis/novo/', frontend.novo_aluguel, name='novo-aluguel'),
    path('taxas-atraso/', frontend.taxas_atraso, name='pagina-taxas-atraso'),
    path('admin/', admin.site.urls),
    path('api/', include('locadora.urls')),
    # Login e logout pela web (Django Auth), com link na API navegável
    path('api-auth/', include('rest_framework.urls')),
]