"""Repositório de aluguéis (tabela ``locadora_aluguel``)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, TypedDict

from locadora import db

TABELA = 'locadora_aluguel'
COLUNAS = 'id, perfil_cliente_id, carro_id, funcionario_id, data_inicio, data_fim, valor, status, data_devolucao'

StatusAluguel = Literal['ativo', 'finalizado']


class AluguelLinha(TypedDict):
    id: int
    perfil_cliente_id: int
    carro_id: int
    funcionario_id: int
    data_inicio: date
    data_fim: date
    valor: Decimal
    status: StatusAluguel
    data_devolucao: date | None


def _normalizar(linha: db.Linha) -> AluguelLinha:
    linha['valor'] = db.para_decimal(linha['valor'])
    return linha  # type: ignore[return-value]


def criar(
    perfil_cliente_id: int,
    carro_id: int,
    funcionario_id: int,
    data_inicio: date,
    data_fim: date,
    valor: Decimal,
) -> AluguelLinha:
    """Insere o aluguel como 'ativo'. Regras (carro disponível etc.) ficam no service."""
    linha = db.buscar_um(
        f"""INSERT INTO {TABELA}
                (perfil_cliente_id, carro_id, funcionario_id, data_inicio, data_fim, valor, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'ativo')
            RETURNING {COLUNAS}""",
        [perfil_cliente_id, carro_id, funcionario_id, data_inicio, data_fim, valor],
    )
    assert linha is not None
    return _normalizar(linha)


def buscar_por_id(aluguel_id: int, bloquear: bool = False) -> AluguelLinha | None:
    sql = f'SELECT {COLUNAS} FROM {TABELA} WHERE id = %s' + (db.for_update() if bloquear else '')
    linha = db.buscar_um(sql, [aluguel_id])
    return None if linha is None else _normalizar(linha)


def listar(
    perfil_cliente_id: int | None = None,
    carro_id: int | None = None,
    funcionario_id: int | None = None,
    status: StatusAluguel | None = None,
    limite: int = 20,
    offset: int = 0,
) -> list[AluguelLinha]:
    """Lista com filtros opcionais. Mais recentes primeiro."""
    filtros: list[str] = []
    params: list[object] = []
    for coluna, valor in (
        ('perfil_cliente_id', perfil_cliente_id),
        ('carro_id', carro_id),
        ('funcionario_id', funcionario_id),
        ('status', status),
    ):
        if valor is not None:
            filtros.append(f'{coluna} = %s')  # coluna vem desta lista fixa, nunca do usuário
            params.append(valor)
    sql = f'SELECT {COLUNAS} FROM {TABELA}'
    if filtros:
        sql += ' WHERE ' + ' AND '.join(filtros)
    sql += ' ORDER BY data_inicio DESC, id DESC LIMIT %s OFFSET %s'
    params += [limite, offset]
    return [_normalizar(linha) for linha in db.buscar_todos(sql, params)]


def finalizar(aluguel_id: int, data_devolucao: date) -> int:
    """Marca como finalizado SÓ se ainda estiver ativo.

    Devolve 1 se finalizou e 0 se já estava finalizado: o próprio UPDATE evita
    que duas devoluções simultâneas passem.
    """
    return db.executar(
        f"UPDATE {TABELA} SET status = 'finalizado', data_devolucao = %s WHERE id = %s AND status = 'ativo'",
        [data_devolucao, aluguel_id],
    )


def tem_multas(aluguel_id: int) -> bool:
    return bool(db.buscar_valor('SELECT EXISTS(SELECT 1 FROM locadora_multa WHERE aluguel_id = %s)', [aluguel_id]))


def excluir(aluguel_id: int) -> int:
    return db.executar(f'DELETE FROM {TABELA} WHERE id = %s', [aluguel_id])
