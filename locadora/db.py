"""Acesso ao banco com SQL puro (sem ORM).

Usa a conexão que o Django já abre, que funciona igual em SQLite e PostgreSQL:

- placeholders sempre ``%s`` (o Django converte para ``?`` no SQLite);
- ``transaction.atomic`` continua valendo;
- cada linha volta como ``dict`` (coluna -> valor).

Regra de ouro: NUNCA monte SQL com f-string/concatenação de VALORES vindos do
usuário. Valores vão sempre em ``params``. F-string só para nomes fixos do código
(tabela, colunas), nunca para dados.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from django.db import connection

Linha = dict[str, Any]
Params = Sequence[Any]

CENTAVOS = Decimal('0.01')


def buscar_todos(sql: str, params: Params = ()) -> list[Linha]:
    """Executa um SELECT e devolve todas as linhas."""
    with connection.cursor() as cur:
        cur.execute(sql, params)
        colunas = [c[0] for c in cur.description]
        return [dict(zip(colunas, linha, strict=True)) for linha in cur.fetchall()]


def buscar_um(sql: str, params: Params = ()) -> Linha | None:
    """Executa um SELECT (ou INSERT/UPDATE ... RETURNING) e devolve a primeira linha, ou None."""
    with connection.cursor() as cur:
        cur.execute(sql, params)
        linha = cur.fetchone()
        if linha is None:
            return None
        colunas = [c[0] for c in cur.description]
        return dict(zip(colunas, linha, strict=True))


def buscar_valor(sql: str, params: Params = ()) -> Any:
    """Executa um SELECT que devolve um único valor (ex.: COUNT, EXISTS)."""
    with connection.cursor() as cur:
        cur.execute(sql, params)
        linha = cur.fetchone()
        return None if linha is None else linha[0]


def executar(sql: str, params: Params = ()) -> int:
    """Executa INSERT/UPDATE/DELETE sem retorno. Devolve a quantidade de linhas afetadas."""
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


def for_update() -> str:
    """Trecho ``FOR UPDATE`` para travar a linha lida dentro de uma transação.

    Só o PostgreSQL tem. O SQLite não aceita essa sintaxe (ele já trava o arquivo
    inteiro durante a escrita), então lá devolvemos string vazia.
    """
    return ' FOR UPDATE' if connection.vendor == 'postgresql' else ''


def para_decimal(valor: Any) -> Decimal | None:
    """Normaliza dinheiro lido do banco para ``Decimal`` com 2 casas.

    O PostgreSQL devolve ``Decimal``; o SQLite pode devolver ``int`` ou ``float``
    (ele não tem tipo decimal de verdade). Assim o resto do código vê sempre o mesmo tipo.
    """
    if valor is None:
        return None
    return Decimal(str(valor)).quantize(CENTAVOS)
