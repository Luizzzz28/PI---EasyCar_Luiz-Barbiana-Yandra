from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api, views

router = DefaultRouter()
router.register("categorias", api.CategoriaViewSet)
router.register("clientes", api.ClienteViewSet)
router.register("alugueis", api.AluguelViewSet)
router.register("taxas-atraso", api.TaxasAtrasoViewSet, basename="taxas-atraso")

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("carros/", views.carros_disponiveis, name="carros-disponiveis"),
    path("clientes/", views.clientes, name="clientes"),
    path("alugueis/novo/", views.novo_aluguel, name="novo-aluguel"),
    path("taxas-atraso/", views.taxas_atraso, name="pagina-taxas-atraso"),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),   # login da API navegável
]
