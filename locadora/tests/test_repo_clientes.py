"""Repositório de perfis de cliente."""

import pytest
from django.db import IntegrityError, transaction

from locadora.repositories import clientes

pytestmark = pytest.mark.django_db


def test_criar_e_buscar_com_dados_do_usuario(perfil_id, usuario_cliente):
    perfil = clientes.buscar_por_id(perfil_id)
    assert perfil['username'] == 'maria'
    assert perfil['first_name'] == 'Maria'
    assert perfil['cnh'] == '12345678901'
    assert clientes.buscar_por_user_id(usuario_cliente.id)['id'] == perfil_id
    assert clientes.buscar_por_cnh('12345678901')['id'] == perfil_id


def test_cnh_duplicada_viola_unique(perfil_id, django_user_model):
    outro = django_user_model.objects.create_user(username='joao', password='senha-forte-123')
    with pytest.raises(IntegrityError), transaction.atomic():
        clientes.criar(outro.id, '12345678901', '61988887777', 'Rua B')


def test_um_perfil_por_usuario(perfil_id, usuario_cliente):
    with pytest.raises(IntegrityError), transaction.atomic():
        clientes.criar(usuario_cliente.id, '99999999999', '61988887777', 'Rua B')


def test_listar_ordena_por_username(perfil_id, django_user_model):
    ana = django_user_model.objects.create_user(username='ana', password='senha-forte-123')
    clientes.criar(ana.id, '11111111111', '61900000000', 'Rua C')
    assert [c['username'] for c in clientes.listar()] == ['ana', 'maria']


def test_atualizar(perfil_id):
    assert clientes.atualizar(perfil_id, '61911112222', 'Rua Nova, 1') == 1
    assert clientes.buscar_por_id(perfil_id)['endereco'] == 'Rua Nova, 1'


def test_carros_alugados_sem_repetir(perfil_id, carro, aluguel, funcionario):
    from datetime import date
    from decimal import Decimal

    from locadora.repositories import alugueis

    alugueis.finalizar(aluguel['id'], date(2026, 1, 15))
    alugueis.criar(perfil_id, carro['id'], funcionario.id, date(2026, 2, 1), date(2026, 2, 3), Decimal('100'))
    assert [c['placa'] for c in clientes.carros_alugados(perfil_id)] == ['ABC1D23']
    assert clientes.tem_alugueis(perfil_id) is True
