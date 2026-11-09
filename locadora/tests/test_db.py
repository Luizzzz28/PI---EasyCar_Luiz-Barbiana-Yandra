"""Testa as funções base de locadora/db.py."""

from decimal import Decimal

import pytest
from django.db import connection

from locadora import db

pytestmark = pytest.mark.django_db


def test_buscar_um_sem_resultado_devolve_none():
    assert db.buscar_um('SELECT id FROM locadora_carro WHERE id = %s', [999999]) is None


def test_buscar_valor():
    assert db.buscar_valor('SELECT COUNT(*) FROM locadora_carro') == 0


def test_for_update_depende_do_banco():
    esperado = ' FOR UPDATE' if connection.vendor == 'postgresql' else ''
    assert db.for_update() == esperado


@pytest.mark.parametrize(
    ('entrada', 'esperado'),
    [(150, Decimal('150.00')), (99.9, Decimal('99.90')), (Decimal('10.5'), Decimal('10.50')), (None, None)],
)
def test_para_decimal_normaliza_dinheiro(entrada, esperado):
    assert db.para_decimal(entrada) == esperado


def test_parametros_impedem_sql_injection():
    """Um valor malicioso é tratado como TEXTO, não como SQL."""
    malicioso = "x' OR '1'='1"
    assert db.buscar_todos('SELECT id FROM locadora_carro WHERE placa = %s', [malicioso]) == []
