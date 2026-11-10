from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from locadora import services
from locadora.models import Carro, PerfilCliente
from locadora.permissions import GRUPO_CLIENTES, GRUPO_FUNCIONARIOS


class BaseApiTestCase(APITestCase):
    """Cenário comum: 1 funcionário, 2 clientes, 2 carros e 1 aluguel ativo do Bruno."""

    @classmethod
    def setUpTestData(cls):
        funcionarios = Group.objects.create(name=GRUPO_FUNCIONARIOS)
        clientes = Group.objects.create(name=GRUPO_CLIENTES)

        cls.ana = User.objects.create_user('ana', password='senha-forte-123')
        cls.ana.groups.add(funcionarios)
        cls.bruno = User.objects.create_user('bruno', password='senha-forte-123')
        cls.bruno.groups.add(clientes)
        cls.carla = User.objects.create_user('carla', password='senha-forte-123')
        cls.carla.groups.add(clientes)
        cls.sem_grupo = User.objects.create_user('visitante', password='senha-forte-123')

        cls.perfil_bruno = PerfilCliente.objects.create(
            user=cls.bruno, cnh='12345678901', telefone='(61) 99999-0001', endereco='QNA 10'
        )
        cls.perfil_carla = PerfilCliente.objects.create(
            user=cls.carla, cnh='98765432100', telefone='(61) 99999-0002', endereco='Rua 20'
        )
        cls.argo = Carro.objects.create(modelo='Fiat Argo', placa='BRA2E19', ano=2023)
        cls.onix = Carro.objects.create(modelo='Chevrolet Onix', placa='QWE1234', ano=2022)

        cls.aluguel_bruno = services.registrar_aluguel({
            'perfil_cliente': cls.perfil_bruno, 'carro': cls.argo, 'valor': Decimal('450.00'),
            'data_inicio': date(2026, 11, 1), 'data_fim': date(2026, 11, 4),
        }, cls.ana)

    def entrar(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def novo_aluguel(self, **extra):
        return {
            'perfil_cliente': self.perfil_carla.pk, 'carro': self.onix.pk, 'valor': '300.00',
            'data_inicio': '2026-11-10', 'data_fim': '2026-11-12', **extra,
        }