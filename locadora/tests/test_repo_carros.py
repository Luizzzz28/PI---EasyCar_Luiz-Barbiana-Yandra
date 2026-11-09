"""Repositório de carros, nos dois bancos (SQLite local, SQLite + PostgreSQL no CI)."""

import pytest
from django.db import IntegrityError, transaction

from locadora.repositories import carros

pytestmark = pytest.mark.django_db


def test_criar_devolve_linha_completa(carro):
    assert carro['id'] > 0
    assert carro['status'] == 'disponivel'
    assert carros.buscar_por_id(carro['id']) == carro


def test_buscar_por_placa(carro):
    assert carros.buscar_por_placa('ABC1D23')['id'] == carro['id']
    assert carros.buscar_por_placa('ZZZ9999') is None


def test_listar_ordena_e_filtra_por_status():
    carros.criar('VW', 'Gol', 'BBB2222', 2021)
    uno = carros.criar('Fiat', 'Uno', 'AAA1111', 2020)
    carros.atualizar_status(uno['id'], 'manutencao')
    assert [c['modelo'] for c in carros.listar()] == ['Gol', 'Uno']
    assert [c['placa'] for c in carros.listar(status='manutencao')] == ['AAA1111']
    assert carros.contar() == 2
    assert carros.contar(status='manutencao') == 1


def test_listar_pagina():
    for i in range(5):
        carros.criar('Fiat', 'Uno', f'AAA111{i}', 2020)
    assert len(carros.listar(limite=2, offset=0)) == 2
    assert len(carros.listar(limite=2, offset=4)) == 1


def test_atualizar_dados(carro):
    assert carros.atualizar(carro['id'], 'Fiat', 'Uno Way', 2021) == 1
    assert carros.buscar_por_id(carro['id'])['modelo'] == 'Uno Way'


def test_placa_duplicada_viola_unique(carro):
    with pytest.raises(IntegrityError), transaction.atomic():
        carros.criar('Fiat', 'Uno', 'ABC1D23', 2020)


def test_bloquear_funciona_nos_dois_bancos(carro):
    with transaction.atomic():
        assert carros.buscar_por_id(carro['id'], bloquear=True) is not None


def test_tem_alugueis(carro, aluguel):
    assert carros.tem_alugueis(carro['id']) is True
    outro = carros.criar('VW', 'Gol', 'BBB2222', 2021)
    assert carros.tem_alugueis(outro['id']) is False


def test_excluir(carro):
    assert carros.excluir(carro['id']) == 1
    assert carros.buscar_por_id(carro['id']) is None
