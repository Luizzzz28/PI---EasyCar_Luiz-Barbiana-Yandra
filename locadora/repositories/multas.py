"""Repositório de multas (tabela ``locadora_multa``)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, TypedDict

from locadora import db

TABELA = 'locadora_multa'
COLUNAS = 'id, aluguel_id, funcionario_id, dias_atrasos, valor, status, data_infracao, data_pagamento, motivo'

StatusMulta = Literal['pendente', 'pago', 'abonado']


class MultaLinha(TypedDict):
    id: int
    aluguel_id: int
    funcionario_id: int
    dias_atrasos: int
    valor: Decimal
    status: StatusMulta
    data_infracao: date
    data_pagamento: date | None
    motivo: str


def _normalizar(linha: db.Linha) -> MultaLinha:
    linha['valor'] = db.para_decimal(linha['valor'])
    return linha  # type: ignore[return-value]


def criar(
    aluguel_id: int,
    funcionario_id: int,
    dias_atrasos: int,
    valor: Decimal,
    data_infracao: date,
    motivo: str,
) -> MultaLinha:
    """Insere a multa como 'pendente'."""
    linha = db.buscar_um(
        f"""INSERT INTO {TABELA}
                (aluguel_id, funcionario_id, dias_atrasos, valor, status, data_infracao, motivo)
            VALUES (%s, %s, %s, %s, 'pendente', %s, %s)
            RETURNING {COLUNAS}""",
        [aluguel_id, funcionario_id, dias_atrasos, valor, data_infracao, motivo],
    )
    assert linha is not None
    return _normalizar(linha)


def buscar_por_id(multa_id: int) -> MultaLinha | None:
    linha = db.buscar_um(f'SELECT {COLUNAS} FROM {TABELA} WHERE id = %s', [multa_id])
    return None if linha is None else _normalizar(linha)


def listar(
    aluguel_id: int | None = None,
    perfil_cliente_id: int | None = None,
    status: StatusMulta | None = None,
    limite: int = 20,
    offset: int = 0,
) -> list[MultaLinha]:
    """Lista multas. ``perfil_cliente_id`` filtra pelas multas de um cliente (JOIN com aluguel)."""
    colunas_m = ', '.join(f'm.{c.strip()}' for c in COLUNAS.split(','))
    sql = f'SELECT {colunas_m} FROM {TABELA} m JOIN locadora_aluguel a ON a.id = m.aluguel_id'
    filtros: list[str] = []
    params: list[object] = []
    if aluguel_id is not None:
        filtros.append('m.aluguel_id = %s')
        params.append(aluguel_id)
    if perfil_cliente_id is not None:
        filtros.append('a.perfil_cliente_id = %s')
        params.append(perfil_cliente_id)
    if status is not None:
        filtros.append('m.status = %s')
        params.append(status)
    if filtros:
        sql += ' WHERE ' + ' AND '.join(filtros)
    sql += ' ORDER BY m.data_infracao DESC, m.id DESC LIMIT %s OFFSET %s'
    params += [limite, offset]
    return [_normalizar(linha) for linha in db.buscar_todos(sql, params)]


def registrar_pagamento(multa_id: int, data_pagamento: date) -> int:
    """Pendente -> pago. Devolve 0 se a multa não estava pendente."""
    return db.executar(
        f"UPDATE {TABELA} SET status = 'pago', data_pagamento = %s WHERE id = %s AND status = 'pendente'",
        [data_pagamento, multa_id],
    )


def abonar(multa_id: int) -> int:
    """Pendente -> abonado (perdoada). Devolve 0 se a multa não estava pendente."""
    return db.executar(
        f"UPDATE {TABELA} SET status = 'abonado' WHERE id = %s AND status = 'pendente'",
        [multa_id],
    )


def excluir(multa_id: int) -> int:
    return db.executar(f'DELETE FROM {TABELA} WHERE id = %s', [multa_id])
