"""Repositório de multas."""

from datetime import date
from decimal import Decimal

import pytest

from locadora.repositories import alugueis, multas

pytestmark = pytest.mark.django_db


@pytest.fixture
def multa(aluguel, funcionario):
    return multas.criar(aluguel['id'], funcionario.id, 2, Decimal('80.50'), date(2026, 1, 17), 'Atraso na devolução')


def test_criar_comeca_pendente(multa, aluguel):
    assert multa['status'] == 'pendente'
    assert multa['valor'] == Decimal('80.50')
    assert multa['data_pagamento'] is None
    assert alugueis.tem_multas(aluguel['id']) is True


def test_pagar_so_se_pendente(multa):
    assert multas.registrar_pagamento(multa['id'], date(2026, 1, 20)) == 1
    assert multas.registrar_pagamento(multa['id'], date(2026, 1, 21)) == 0
    assert multas.abonar(multa['id']) == 0
    lida = multas.buscar_por_id(multa['id'])
    assert lida['status'] == 'pago'
    assert lida['data_pagamento'] == date(2026, 1, 20)


def test_abonar(multa):
    assert multas.abonar(multa['id']) == 1
    assert multas.buscar_por_id(multa['id'])['status'] == 'abonado'


def test_listar_por_cliente_e_status(multa, perfil_id):
    assert [m['id'] for m in multas.listar(perfil_cliente_id=perfil_id)] == [multa['id']]
    assert multas.listar(perfil_cliente_id=perfil_id + 1000) == []
    assert len(multas.listar(status='pendente')) == 1


def test_excluir(multa):
    assert multas.excluir(multa['id']) == 1
    assert multas.buscar_por_id(multa['id']) is None
