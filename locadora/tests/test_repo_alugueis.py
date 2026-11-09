"""Repositório de aluguéis, incluindo as CHECK constraints do banco."""

from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from locadora.repositories import alugueis

pytestmark = pytest.mark.django_db


def test_criar_comeca_ativo_e_valor_e_decimal(aluguel):
    assert aluguel['status'] == 'ativo'
    assert aluguel['data_devolucao'] is None
    assert aluguel['valor'] == Decimal('350.00')
    assert isinstance(aluguel['valor'], Decimal)


def test_datas_voltam_como_date(aluguel):
    lido = alugueis.buscar_por_id(aluguel['id'])
    assert lido['data_inicio'] == date(2026, 1, 10)
    assert isinstance(lido['data_fim'], date)


def test_check_fim_antes_do_inicio(perfil_id, carro, funcionario):
    with pytest.raises(IntegrityError), transaction.atomic():
        alugueis.criar(perfil_id, carro['id'], funcionario.id, date(2026, 1, 10), date(2026, 1, 5), Decimal('10'))


def test_check_valor_positivo(perfil_id, carro, funcionario):
    with pytest.raises(IntegrityError), transaction.atomic():
        alugueis.criar(perfil_id, carro['id'], funcionario.id, date(2026, 1, 10), date(2026, 1, 12), Decimal('0'))


def test_finalizar_so_uma_vez(aluguel):
    assert alugueis.finalizar(aluguel['id'], date(2026, 1, 15)) == 1
    assert alugueis.finalizar(aluguel['id'], date(2026, 1, 16)) == 0  # 2ª devolução não passa
    lido = alugueis.buscar_por_id(aluguel['id'])
    assert lido['status'] == 'finalizado'
    assert lido['data_devolucao'] == date(2026, 1, 15)


def test_listar_com_filtros(aluguel, perfil_id, carro):
    assert len(alugueis.listar(perfil_cliente_id=perfil_id)) == 1
    assert len(alugueis.listar(carro_id=carro['id'], status='ativo')) == 1
    assert alugueis.listar(status='finalizado') == []


def test_bloquear_e_excluir(aluguel):
    with transaction.atomic():
        assert alugueis.buscar_por_id(aluguel['id'], bloquear=True) is not None
    assert alugueis.tem_multas(aluguel['id']) is False
    assert alugueis.excluir(aluguel['id']) == 1
    assert alugueis.buscar_por_id(aluguel['id']) is None
