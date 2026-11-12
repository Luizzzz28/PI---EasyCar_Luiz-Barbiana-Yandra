"""Regras de negócio do aluguel. As views chamam estas funções; não mexem no status sozinhas.

Todas as funções que alteram mais de uma tabela rodam dentro de ``transaction.atomic``
(tudo ou nada) e travam as linhas envolvidas com ``select_for_update`` para que duas
requisições simultâneas não alterem o mesmo carro/aluguel ao mesmo tempo.

Camada de banco desenvolvida com orientação do Prof. Henry (ver docs/banco-de-producao.md).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone

from .models import Aluguel, Carro, Multa


class RegraDeNegocio(Exception):
    """Pedido válido no formato, mas impossível no estado atual dos dados."""


def _travar_aluguel_ativo(aluguel: Aluguel) -> None:
    """Trava a linha do aluguel e confere, com o valor ATUAL do banco, se ainda está ativo."""
    status_atual = Aluguel.objects.select_for_update().values_list('status', flat=True).get(pk=aluguel.pk)
    if status_atual != Aluguel.Status.ATIVO:
        raise RegraDeNegocio('Este aluguel já foi finalizado.')


def _finalizar(aluguel: Aluguel) -> None:
    """Marca o aluguel como finalizado e libera o carro (chamar dentro de transação)."""
    aluguel.status = Aluguel.Status.FINALIZADO
    aluguel.data_devolucao = timezone.localdate()
    aluguel.save(update_fields=['status', 'data_devolucao'])
    aluguel.carro.status = Carro.Status.DISPONIVEL
    aluguel.carro.save(update_fields=['status'])


@transaction.atomic
def registrar_aluguel(dados: dict[str, Any], funcionario: User) -> Aluguel:
    """Cria o aluguel e marca o carro como alugado. O carro precisa estar disponível."""
    carro = Carro.objects.select_for_update().get(pk=dados['carro'].pk)
    if carro.status != Carro.Status.DISPONIVEL:
        raise RegraDeNegocio(f'O carro {carro.placa} não está disponível ({carro.get_status_display()}).')
    aluguel = Aluguel.objects.create(funcionario=funcionario, **{**dados, 'carro': carro})
    carro.status = Carro.Status.ALUGADO
    carro.save(update_fields=['status'])
    return aluguel


@transaction.atomic
def devolver_carro(aluguel: Aluguel) -> Aluguel:
    """Finaliza o aluguel e libera o carro. Duas devoluções simultâneas: só a primeira passa."""
    _travar_aluguel_ativo(aluguel)
    _finalizar(aluguel)
    return aluguel


@transaction.atomic
def excluir_aluguel(aluguel: Aluguel) -> None:
    """Apaga um aluguel registrado por engano. Se estava ativo, o carro volta a ficar disponível."""
    carro = aluguel.carro
    estava_ativo = aluguel.status == Aluguel.Status.ATIVO
    try:
        aluguel.delete()
    except ProtectedError as erro:
        raise RegraDeNegocio('Este aluguel tem multas vinculadas e não pode ser excluído.') from erro
    if estava_ativo:
        carro.status = Carro.Status.DISPONIVEL
        carro.save(update_fields=['status'])


@transaction.atomic
def registrar_multa(
    aluguel: Aluguel,
    funcionario: User,
    *,
    valor: Decimal,
    dias_atrasos: int,
    motivo: str,
    data_infracao: date,
) -> Multa:
    """Cria a multa e finaliza o aluguel (o carro volta a ficar disponível). O aluguel precisa estar ativo."""
    _travar_aluguel_ativo(aluguel)
    multa = Multa.objects.create(
        aluguel=aluguel,
        funcionario=funcionario,
        valor=valor,
        dias_atrasos=dias_atrasos,
        motivo=motivo,
        data_infracao=data_infracao,
    )
    _finalizar(aluguel)
    return multa
