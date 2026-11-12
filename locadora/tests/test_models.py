"""Regras que o PRÓPRIO BANCO garante (constraints) e comportamento dos models.

Rodam em SQLite (local) e em SQLite + PostgreSQL (CI).
"""

from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from locadora.models import Aluguel, Carro, Multa, PerfilCliente

pytestmark = pytest.mark.django_db


def criar_em_transacao(model, **campos):
    """Erros do banco quebram a transação no PostgreSQL: isolamos cada tentativa."""
    with transaction.atomic():
        return model.objects.create(**campos)


# --- Carro ---------------------------------------------------------------


def test_carro_comeca_disponivel(carro):
    assert carro.status == Carro.Status.DISPONIVEL
    assert str(carro) == 'Uno (ABC1D23)'


def test_placa_unica(carro):
    with pytest.raises(IntegrityError):
        criar_em_transacao(Carro, modelo='Gol', placa='ABC1D23', ano=2021)


def test_carros_ordenados_por_modelo_e_placa():
    Carro.objects.create(modelo='Gol', placa='BBB2222', ano=2021)
    Carro.objects.create(modelo='Uno', placa='AAA1111', ano=2020)
    Carro.objects.create(modelo='Gol', placa='AAA0000', ano=2022)
    assert list(Carro.objects.values_list('placa', flat=True)) == ['AAA0000', 'BBB2222', 'AAA1111']


def test_carro_com_aluguel_nao_pode_ser_excluido(carro, aluguel):
    with pytest.raises(ProtectedError):
        carro.delete()


# --- PerfilCliente -------------------------------------------------------


def test_cnh_unica(perfil, django_user_model):
    outro = django_user_model.objects.create_user(username='joao', password='senha-forte-123')
    with pytest.raises(IntegrityError):
        criar_em_transacao(PerfilCliente, user=outro, cnh='12345678901', telefone='1', endereco='x')


def test_um_perfil_por_usuario(perfil, usuario_cliente):
    with pytest.raises(IntegrityError):
        criar_em_transacao(PerfilCliente, user=usuario_cliente, cnh='99999999999', telefone='1', endereco='x')


def test_excluir_usuario_apaga_perfil_cascade(perfil, usuario_cliente):
    usuario_cliente.delete()
    assert not PerfilCliente.objects.filter(pk=perfil.pk).exists()


def test_perfil_str_usa_nome_completo(perfil):
    assert str(perfil) == 'Maria Silva'


def test_carros_do_cliente_via_aluguel_sem_repetir(perfil, carro, aluguel, funcionario):
    """Relação N:N cliente <-> carro usando Aluguel como tabela intermediária."""
    aluguel.status = Aluguel.Status.FINALIZADO
    aluguel.save()
    Aluguel.objects.create(
        perfil_cliente=perfil,
        carro=carro,
        funcionario=funcionario,
        data_inicio=date(2026, 2, 1),
        data_fim=date(2026, 2, 3),
        valor=Decimal('100'),
    )
    assert perfil.alugueis.count() == 2
    assert list(perfil.carros.distinct()) == [carro]


# --- Aluguel -------------------------------------------------------------


def test_valor_volta_como_decimal(aluguel):
    aluguel.refresh_from_db()
    assert aluguel.valor == Decimal('350.00')
    assert isinstance(aluguel.valor, Decimal)
    assert aluguel.data_inicio == date(2026, 1, 10)


def test_check_fim_nao_pode_ser_antes_do_inicio(dados_aluguel, funcionario):
    dados_aluguel['data_fim'] = date(2026, 1, 1)
    with pytest.raises(IntegrityError):
        criar_em_transacao(Aluguel, funcionario=funcionario, **dados_aluguel)


def test_check_valor_do_aluguel_positivo(dados_aluguel, funcionario):
    dados_aluguel['valor'] = Decimal('0')
    with pytest.raises(IntegrityError):
        criar_em_transacao(Aluguel, funcionario=funcionario, **dados_aluguel)


def test_um_aluguel_ativo_por_carro(aluguel, dados_aluguel, funcionario):
    """Mesmo que alguém pule o service, o banco recusa o 2º aluguel ativo do mesmo carro."""
    with pytest.raises(IntegrityError):
        criar_em_transacao(Aluguel, funcionario=funcionario, **dados_aluguel)


def test_carro_pode_ter_varios_alugueis_finalizados(aluguel, dados_aluguel, funcionario):
    aluguel.status = Aluguel.Status.FINALIZADO
    aluguel.save()
    criar_em_transacao(Aluguel, funcionario=funcionario, **dados_aluguel)
    assert Aluguel.objects.filter(carro=dados_aluguel['carro']).count() == 2


def test_alugueis_mais_recentes_primeiro(aluguel, dados_aluguel, funcionario):
    aluguel.status = Aluguel.Status.FINALIZADO
    aluguel.save()
    novo = Aluguel.objects.create(
        funcionario=funcionario, **{**dados_aluguel, 'data_inicio': date(2026, 3, 1), 'data_fim': date(2026, 3, 2)}
    )
    assert list(Aluguel.objects.all()) == [novo, aluguel]


def test_funcionario_com_aluguel_nao_pode_ser_excluido(aluguel, funcionario):
    with pytest.raises(ProtectedError):
        funcionario.delete()


# --- Multa ---------------------------------------------------------------


def nova_multa(aluguel, funcionario, **extra):
    campos = {
        'aluguel': aluguel,
        'funcionario': funcionario,
        'dias_atrasos': 2,
        'valor': Decimal('80.50'),
        'data_infracao': date(2026, 1, 17),
        'motivo': 'Atraso',
    }
    return criar_em_transacao(Multa, **{**campos, **extra})


def test_multa_comeca_pendente(aluguel, funcionario):
    multa = nova_multa(aluguel, funcionario)
    assert multa.status == Multa.Status.PENDENTE
    assert multa.data_pagamento is None


def test_check_valor_da_multa_positivo(aluguel, funcionario):
    with pytest.raises(IntegrityError):
        nova_multa(aluguel, funcionario, valor=Decimal('-1'))


def test_check_dias_de_atraso_minimo(aluguel, funcionario):
    with pytest.raises(IntegrityError):
        nova_multa(aluguel, funcionario, dias_atrasos=0)


def test_aluguel_com_multa_nao_pode_ser_excluido(aluguel, funcionario):
    nova_multa(aluguel, funcionario)
    with pytest.raises(ProtectedError):
        aluguel.delete()
