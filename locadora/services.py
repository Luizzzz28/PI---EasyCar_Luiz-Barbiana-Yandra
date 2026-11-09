"""Regras de negócio do aluguel. As views chamam estas funções; não mexem no status sozinhas."""
from django.db import transaction
from django.utils import timezone

from .models import Aluguel, Carro, Multa


class RegraDeNegocio(Exception):
    """Pedido válido no formato, mas impossível no estado atual dos dados."""


@transaction.atomic
def registrar_aluguel(dados, funcionario):
    """Cria o aluguel e marca o carro como alugado. O carro precisa estar disponível."""
    carro = Carro.objects.select_for_update().get(pk=dados['carro'].pk)
    if carro.status != Carro.Status.DISPONIVEL:
        raise RegraDeNegocio(f'O carro {carro.placa} não está disponível ({carro.get_status_display()}).')
    aluguel = Aluguel.objects.create(funcionario=funcionario, **dados)
    carro.status = Carro.Status.ALUGADO
    carro.save(update_fields=['status'])
    return aluguel


@transaction.atomic
def devolver_carro(aluguel):
    """Finaliza o aluguel e libera o carro."""
    if aluguel.status != Aluguel.Status.ATIVO:
        raise RegraDeNegocio('Este aluguel já foi finalizado.')
    aluguel.status = Aluguel.Status.FINALIZADO
    aluguel.data_devolucao = timezone.localdate()
    aluguel.save(update_fields=['status', 'data_devolucao'])
    aluguel.carro.status = Carro.Status.DISPONIVEL
    aluguel.carro.save(update_fields=['status'])
    return aluguel


@transaction.atomic
def excluir_aluguel(aluguel):
    """Apaga um aluguel registrado por engano. Se estava ativo, o carro volta a ficar disponível."""
    carro = aluguel.carro
    estava_ativo = aluguel.status == Aluguel.Status.ATIVO
    aluguel.delete()
    if estava_ativo:
        carro.status = Carro.Status.DISPONIVEL
        carro.save(update_fields=['status'])


@transaction.atomic
def registrar_multa(aluguel, funcionario, valor, descricao, data_infracao):
    """Cria a multa e marca o aluguel como finalizado. O aluguel precisa estar ativo."""
    if aluguel.status != Aluguel.Status.ATIVO:
        raise RegraDeNegocio('Este aluguel já foi finalizado.')
    multa = Multa.objects.create(
        aluguel=aluguel,
        funcionario=funcionario,
        valor=valor,
        descricao=descricao,
        data_infracao=data_infracao,
    )
    aluguel.status = Aluguel.Status.FINALIZADO
    aluguel.data_devolucao = timezone.localdate()
    aluguel.save(update_fields=['status', 'data_devolucao'])
    aluguel.carro.status = Carro.Status.DISPONIVEL
    aluguel.carro.save(update_fields=['status'])
    return multa