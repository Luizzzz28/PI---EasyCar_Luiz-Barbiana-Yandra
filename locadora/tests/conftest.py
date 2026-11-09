"""Fixtures compartilhadas pelos testes do banco.

Cada teste recebe um banco limpo: o pytest-django abre uma transação antes do
teste e desfaz (ROLLBACK) no final. Nada vaza de um teste para outro.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from locadora.repositories import alugueis, carros, clientes
from locadora.repositories.alugueis import AluguelLinha
from locadora.repositories.carros import CarroLinha


@pytest.fixture
def funcionario(django_user_model):
    """Usuário que registra aluguéis/multas. (auth_user é do Django: criar por ele é o certo.)"""
    return django_user_model.objects.create_user(username='func', password='senha-forte-123')


@pytest.fixture
def usuario_cliente(django_user_model):
    return django_user_model.objects.create_user(
        username='maria', password='senha-forte-123', first_name='Maria', last_name='Silva'
    )


@pytest.fixture
def perfil_id(usuario_cliente) -> int:
    return clientes.criar(usuario_cliente.id, '12345678901', '61999990000', 'Rua A, 10')


@pytest.fixture
def carro() -> CarroLinha:
    return carros.criar('Fiat', 'Uno', 'ABC1D23', 2020)


@pytest.fixture
def aluguel(perfil_id, carro, funcionario) -> AluguelLinha:
    return alugueis.criar(
        perfil_id, carro['id'], funcionario.id, date(2026, 1, 10), date(2026, 1, 15), Decimal('350.00')
    )
