from rest_framework import filters, viewsets
from rest_framework.response import Response

from .models import Aluguel, Categoria, Cliente, FAIXAS_ATRASO
from .serializers import AluguelSerializer, CategoriaSerializer, ClienteSerializer


class TaxasAtrasoViewSet(viewsets.ViewSet):
    def list(self, request):
        categorias = Categoria.objects.all()
        return Response({
            "faixas": FAIXAS_ATRASO,
            "por_categoria": [
                {
                    "categoria": categoria.nome,
                    "diaria": categoria.diaria,
                    "taxa_hora": categoria.taxa_hora,
                    "multa_dia": categoria.multa_dia,
                }
                for categoria in categorias
            ],
        })


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nome", "cpf"]          # ex.: /api/clientes/?search=maria


class AluguelViewSet(viewsets.ModelViewSet):
    queryset = Aluguel.objects.select_related("cliente", "categoria")
    serializer_class = AluguelSerializer
