"""Views da API (controllers). Recebem o pedido, checam o grupo, chamam services e respondem."""
from django.contrib.auth.models import User
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, NotFound
from rest_framework.response import Response

from . import services
from .models import Aluguel, Carro, PerfilCliente, Multa
from .permissions import (
    GRUPO_CLIENTES, GRUPO_FUNCIONARIOS, EhCliente, EhFuncionario, FuncionarioEditaClienteConsulta,
    eh_funcionario,
)
from .serializers import (
    AluguelDetalhadoSerializer, AluguelSerializer, CarroSerializer, FuncionarioSerializer,
    PerfilClienteSerializer, UserSerializer, MultaSerializer
)


class Conflito(APIException):
    status_code = 409
    default_detail = 'A operação conflita com o estado atual dos dados.'
    default_code = 'conflito'


class ListaPaginadaMixin:
    def lista_paginada(self, queryset, serializer_class=AluguelDetalhadoSerializer):
        pagina = self.paginate_queryset(queryset)
        if pagina is not None:
            return self.get_paginated_response(serializer_class(pagina, many=True).data)
        return Response(serializer_class(queryset, many=True).data)


class ExclusaoProtegidaMixin:
    """Responde 409 em vez de erro 500 quando o registro tem aluguéis (on_delete=PROTECT)."""

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise Conflito('Este registro tem aluguéis vinculados e não pode ser excluído.')


def alugueis_completos():
    return Aluguel.objects.select_related('carro', 'perfil_cliente__user', 'funcionario')


# Usuários e perfis (só funcionários)

class UserViewSet(ExclusaoProtegidaMixin, viewsets.ModelViewSet):
    """CRUD de usuários do grupo Clientes. Funcionários são criados só pelo admin."""

    serializer_class = UserSerializer
    permission_classes = [EhFuncionario]
    queryset = User.objects.filter(groups__name=GRUPO_CLIENTES).prefetch_related('groups').order_by('username')


class PerfilClienteViewSet(ListaPaginadaMixin, ExclusaoProtegidaMixin, viewsets.ModelViewSet):
    serializer_class = PerfilClienteSerializer
    permission_classes = [EhFuncionario]
    queryset = PerfilCliente.objects.select_related('user')

    @action(detail=True)
    def alugueis(self, request, pk=None):
        """GET /perfis-clientes/{id}/alugueis/: aluguéis do cliente, com os dados do carro."""
        perfil = self.get_object()
        return self.lista_paginada(alugueis_completos().filter(perfil_cliente=perfil))

    @extend_schema(responses=CarroSerializer(many=True))
    @action(detail=True)
    def carros(self, request, pk=None):
        """GET /perfis-clientes/{id}/carros/: carros que o cliente já alugou (A-B)."""
        perfil = self.get_object()
        return self.lista_paginada(perfil.carros.distinct(), CarroSerializer)

    @action(detail=True, url_path=r'carros/(?P<carro_id>[0-9]+)/alugueis')
    def alugueis_do_carro(self, request, pk=None, carro_id=None):
        """GET /perfis-clientes/{id}/carros/{carro_id}/alugueis/: aluguéis deste cliente com este carro (A-B-C)."""
        perfil = self.get_object()
        carro = get_object_or_404(Carro, pk=carro_id)
        return self.lista_paginada(alugueis_completos().filter(perfil_cliente=perfil, carro=carro))


class FuncionarioViewSet(ListaPaginadaMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = FuncionarioSerializer
    permission_classes = [EhFuncionario]
    queryset = User.objects.filter(groups__name=GRUPO_FUNCIONARIOS).order_by('username')

    @action(detail=True)
    def alugueis(self, request, pk=None):
        """GET /funcionarios/{id}/alugueis/: aluguéis registrados por este funcionário (1:N)."""
        funcionario = self.get_object()
        return self.lista_paginada(alugueis_completos().filter(funcionario=funcionario))


# Carros e aluguéis (funcionário edita, cliente consulta)

class CarroViewSet(ListaPaginadaMixin, ExclusaoProtegidaMixin, viewsets.ModelViewSet):
    serializer_class = CarroSerializer
    permission_classes = [FuncionarioEditaClienteConsulta]

    def get_queryset(self):
        carros = Carro.objects.all()
        status = self.request.query_params.get('status')  # /api/carros/?status=disponivel
        if status:
            carros = carros.filter(status=status)
        return carros

    @action(detail=True, permission_classes=[EhFuncionario])
    def alugueis(self, request, pk=None):
        """GET /carros/{id}/alugueis/: histórico de aluguéis do carro (B-C)."""
        carro = self.get_object()
        return self.lista_paginada(alugueis_completos().filter(carro=carro))


class AluguelViewSet(viewsets.ModelViewSet):
    serializer_class = AluguelSerializer
    permission_classes = [FuncionarioEditaClienteConsulta]

    def get_queryset(self):
        # Ao gerar a documentação não há usuário logado
        if getattr(self, 'swagger_fake_view', False):
            return Aluguel.objects.none()
        alugueis = alugueis_completos()
        if eh_funcionario(self.request.user):
            return alugueis
        # Cliente vê só os seus: o aluguel de outra pessoa responde 404
        return alugueis.filter(perfil_cliente__user=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.instance = services.registrar_aluguel(serializer.validated_data, self.request.user)
        except services.RegraDeNegocio as erro:
            raise Conflito(str(erro))

    def perform_destroy(self, instance):
        services.excluir_aluguel(instance)

    @extend_schema(request=None, responses=AluguelSerializer)
    @action(detail=True, methods=['post'], permission_classes=[EhFuncionario])
    def devolver(self, request, pk=None):
        """POST /alugueis/{id}/devolver/: finaliza o aluguel e libera o carro."""
        aluguel = self.get_object()
        try:
            services.devolver_carro(aluguel)
        except services.RegraDeNegocio as erro:
            raise Conflito(str(erro))
        return Response(AluguelSerializer(aluguel).data)


# Multas (funcionário edita, cliente consulta)
class MultaViewSet(viewsets.ModelViewSet):
    serializer_class = MultaSerializer
    permission_classes = [FuncionarioEditaClienteConsulta]

    def get_queryset(self):
        # Ao gerar a documentação não há usuário logado
        if getattr(self, 'swagger_fake_view', False):
            return Multa.objects.none()
        multas = Multa.objects.select_related('aluguel__perfil_cliente__user', 'aluguel__carro', 'funcionario')
        if eh_funcionario(self.request.user):
            return multas
        # Cliente vê só as suas: a multa de outra pessoa responde 404
        return multas.filter(aluguel__perfil_cliente__user=self.request.user)


# Rotas do cliente logado (/api/me/...)

def perfil_do_usuario(user):
    perfil = getattr(user, 'perfil_cliente', None)
    if perfil is None:
        raise NotFound('Seu usuário ainda não tem perfil de cliente. Procure um funcionário.')
    return perfil


class MeuPerfilView(generics.RetrieveAPIView):
    """GET /me/: o perfil do cliente autenticado."""

    serializer_class = PerfilClienteSerializer
    permission_classes = [EhCliente]

    def get_object(self):
        return perfil_do_usuario(self.request.user)


class MeusAlugueisView(generics.ListAPIView):
    """GET /me/alugueis/: só os aluguéis do cliente autenticado."""

    serializer_class = AluguelDetalhadoSerializer
    permission_classes = [EhCliente]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Aluguel.objects.none()
        return alugueis_completos().filter(perfil_cliente=perfil_do_usuario(self.request.user))


class MeusCarrosView(generics.ListAPIView):
    """GET /me/carros/: carros que o cliente autenticado já alugou."""

    serializer_class = CarroSerializer
    permission_classes = [EhCliente]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Carro.objects.none()
        return perfil_do_usuario(self.request.user).carros.distinct()


class MinhasMultasView(generics.ListAPIView):
    """GET /me/multas/: só as multas do cliente autenticado."""

    serializer_class = MultaSerializer
    permission_classes = [EhCliente]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Multa.objects.none()
        return Multa.objects.select_related('aluguel__perfil_cliente__user', 'aluguel__carro', 'funcionario').filter(
            aluguel__perfil_cliente=perfil_do_usuario(self.request.user)
        )