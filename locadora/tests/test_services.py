"""Regras de negócio (services.py): transações e mudanças de status."""

from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone

from locadora import services
from locadora.models import Aluguel, Carro, Multa

pytestmark = pytest.mark.django_db


def dados_multa():
    return {'valor': Decimal('80.00'), 'dias_atrasos': 2, 'motivo': 'Atraso', 'data_infracao': date(2026, 1, 17)}


# --- registrar_aluguel ---------------------------------------------------


def test_registrar_aluguel_marca_carro_alugado(aluguel, carro, funcionario):
    carro.refresh_from_db()
    assert carro.status == Carro.Status.ALUGADO
    assert aluguel.status == Aluguel.Status.ATIVO
    assert aluguel.funcionario == funcionario


@pytest.mark.parametrize('status', [Carro.Status.ALUGADO, Carro.Status.MANUTENCAO])
def test_nao_aluga_carro_indisponivel(dados_aluguel, funcionario, carro, status):
    carro.status = status
    carro.save()
    with pytest.raises(services.RegraDeNegocio, match='não está disponível'):
        services.registrar_aluguel(dados_aluguel, funcionario)
    assert Aluguel.objects.count() == 0


def test_nao_aluga_o_mesmo_carro_duas_vezes(aluguel, dados_aluguel, funcionario):
    with pytest.raises(services.RegraDeNegocio):
        services.registrar_aluguel(dados_aluguel, funcionario)


# --- devolver_carro ------------------------------------------------------


def test_devolver_finaliza_e_libera_carro(aluguel, carro):
    services.devolver_carro(aluguel)
    aluguel.refresh_from_db()
    carro.refresh_from_db()
    assert aluguel.status == Aluguel.Status.FINALIZADO
    assert aluguel.data_devolucao == timezone.localdate()
    assert carro.status == Carro.Status.DISPONIVEL


def test_nao_devolve_duas_vezes(aluguel):
    services.devolver_carro(aluguel)
    with pytest.raises(services.RegraDeNegocio, match='já foi finalizado'):
        services.devolver_carro(aluguel)


def test_devolver_confere_o_banco_e_nao_o_objeto_em_memoria(aluguel):
    """Outra requisição já finalizou: o objeto antigo em memória ainda diz 'ativo'."""
    Aluguel.objects.filter(pk=aluguel.pk).update(status=Aluguel.Status.FINALIZADO)
    assert aluguel.status == Aluguel.Status.ATIVO
    with pytest.raises(services.RegraDeNegocio):
        services.devolver_carro(aluguel)


def test_depois_de_devolver_o_carro_pode_ser_alugado_de_novo(aluguel, dados_aluguel, funcionario):
    services.devolver_carro(aluguel)
    novo = services.registrar_aluguel(dados_aluguel, funcionario)
    assert novo.status == Aluguel.Status.ATIVO


# --- excluir_aluguel -----------------------------------------------------


def test_excluir_aluguel_ativo_libera_carro(aluguel, carro):
    services.excluir_aluguel(aluguel)
    carro.refresh_from_db()
    assert carro.status == Carro.Status.DISPONIVEL
    assert Aluguel.objects.count() == 0


def test_excluir_aluguel_finalizado_nao_mexe_no_carro(aluguel, carro):
    services.devolver_carro(aluguel)
    carro.status = Carro.Status.MANUTENCAO
    carro.save()
    aluguel.refresh_from_db()
    services.excluir_aluguel(aluguel)
    carro.refresh_from_db()
    assert carro.status == Carro.Status.MANUTENCAO


def test_nao_exclui_aluguel_com_multa(aluguel, funcionario):
    services.registrar_multa(aluguel, funcionario, **dados_multa())
    aluguel.refresh_from_db()
    with pytest.raises(services.RegraDeNegocio, match='multas'):
        services.excluir_aluguel(aluguel)
    assert Aluguel.objects.filter(pk=aluguel.pk).exists()


# --- registrar_multa -----------------------------------------------------


def test_registrar_multa_finaliza_aluguel_e_libera_carro(aluguel, carro, funcionario):
    multa = services.registrar_multa(aluguel, funcionario, **dados_multa())
    aluguel.refresh_from_db()
    carro.refresh_from_db()
    assert multa.status == Multa.Status.PENDENTE
    assert multa.dias_atrasos == 2
    assert multa.motivo == 'Atraso'
    assert aluguel.status == Aluguel.Status.FINALIZADO
    assert carro.status == Carro.Status.DISPONIVEL


def test_nao_multa_aluguel_finalizado(aluguel, funcionario):
    services.devolver_carro(aluguel)
    with pytest.raises(services.RegraDeNegocio):
        services.registrar_multa(aluguel, funcionario, **dados_multa())
    assert Multa.objects.count() == 0


def test_erro_no_meio_desfaz_tudo(aluguel, carro, funcionario):
    """transaction.atomic: se a multa é inválida, o aluguel NÃO fica finalizado."""
    with pytest.raises(Exception):
        services.registrar_multa(aluguel, funcionario, **{**dados_multa(), 'dias_atrasos': 0})
    aluguel.refresh_from_db()
    carro.refresh_from_db()
    assert aluguel.status == Aluguel.Status.ATIVO
    assert carro.status == Carro.Status.ALUGADO
    assert Multa.objects.count() == 0
