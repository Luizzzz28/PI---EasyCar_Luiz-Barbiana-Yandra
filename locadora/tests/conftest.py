"""Fixtures compartilhadas pelos testes.

Cada teste recebe um banco limpo: o pytest-django abre uma transação antes do
teste e desfaz (ROLLBACK) no final. Nada vaza de um teste para outro.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from locadora import services
from locadora.models import Aluguel, Carro, PerfilCliente


@pytest.fixture
def funcionario(django_user_model) -> User:
    return django_user_model.objects.create_user(username='func', password='senha-forte-123')


@pytest.fixture
def usuario_cliente(django_user_model) -> User:
    return django_user_model.objects.create_user(
        username='maria', password='senha-forte-123', first_name='Maria', last_name='Silva'
    )


@pytest.fixture
def perfil(usuario_cliente) -> PerfilCliente:
    return PerfilCliente.objects.create(
        user=usuario_cliente, cnh='12345678901', telefone='61999990000', endereco='Rua A, 10'
    )


@pytest.fixture
def carro() -> Carro:
    return Carro.objects.create(modelo='Uno', placa='ABC1D23', ano=2020)


@pytest.fixture
def dados_aluguel(perfil, carro) -> dict:
    return {
        'perfil_cliente': perfil,
        'carro': carro,
        'data_inicio': date(2026, 1, 10),
        'data_fim': date(2026, 1, 15),
        'valor': Decimal('350.00'),
    }


@pytest.fixture
def aluguel(dados_aluguel, funcionario) -> Aluguel:
    """Aluguel ATIVO criado pelo service (o carro fica 'alugado')."""
    return services.registrar_aluguel(dados_aluguel, funcionario)
