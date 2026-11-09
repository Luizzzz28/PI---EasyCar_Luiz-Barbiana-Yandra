"""Repositório de carros (tabela ``locadora_carro``)."""

from __future__ import annotations

from typing import Literal, TypedDict, cast

from locadora import db

TABELA = 'locadora_carro'
COLUNAS = 'id, marca, modelo, placa, ano, status'

StatusCarro = Literal['disponivel', 'alugado', 'manutencao']


class CarroLinha(TypedDict):
    id: int
    marca: str
    modelo: str
    placa: str
    ano: int
    status: StatusCarro


def listar(status: StatusCarro | None = None, limite: int = 20, offset: int = 0) -> list[CarroLinha]:
    """Lista carros em ordem de modelo/placa, opcionalmente filtrando por status."""
    sql = f'SELECT {COLUNAS} FROM {TABELA}'
    params: list[object] = []
    if status:
        sql += ' WHERE status = %s'
        params.append(status)
    sql += ' ORDER BY modelo, placa LIMIT %s OFFSET %s'
    params += [limite, offset]
    return cast(list[CarroLinha], db.buscar_todos(sql, params))


def contar(status: StatusCarro | None = None) -> int:
    """Total de carros (para paginação)."""
    if status:
        return int(db.buscar_valor(f'SELECT COUNT(*) FROM {TABELA} WHERE status = %s', [status]))
    return int(db.buscar_valor(f'SELECT COUNT(*) FROM {TABELA}'))


def buscar_por_id(carro_id: int, bloquear: bool = False) -> CarroLinha | None:
    """Busca um carro. Com ``bloquear=True`` (dentro de transaction.atomic) trava a linha no PostgreSQL."""
    sql = f'SELECT {COLUNAS} FROM {TABELA} WHERE id = %s' + (db.for_update() if bloquear else '')
    return cast(CarroLinha | None, db.buscar_um(sql, [carro_id]))


def buscar_por_placa(placa: str) -> CarroLinha | None:
    return cast(CarroLinha | None, db.buscar_um(f'SELECT {COLUNAS} FROM {TABELA} WHERE placa = %s', [placa]))


def criar(marca: str, modelo: str, placa: str, ano: int, status: StatusCarro = 'disponivel') -> CarroLinha:
    """Insere um carro e devolve a linha criada (RETURNING: PostgreSQL e SQLite >= 3.35)."""
    linha = db.buscar_um(
        f'INSERT INTO {TABELA} (marca, modelo, placa, ano, status) VALUES (%s, %s, %s, %s, %s) RETURNING {COLUNAS}',
        [marca, modelo, placa, ano, status],
    )
    return cast(CarroLinha, linha)


def atualizar(carro_id: int, marca: str, modelo: str, ano: int) -> int:
    """Atualiza dados cadastrais. Status muda só por ``atualizar_status``. Devolve linhas afetadas."""
    return db.executar(
        f'UPDATE {TABELA} SET marca = %s, modelo = %s, ano = %s WHERE id = %s',
        [marca, modelo, ano, carro_id],
    )


def atualizar_status(carro_id: int, status: StatusCarro) -> int:
    return db.executar(f'UPDATE {TABELA} SET status = %s WHERE id = %s', [status, carro_id])


def tem_alugueis(carro_id: int) -> bool:
    """O banco NÃO aplica o PROTECT do Django: confira isto antes de excluir."""
    return bool(db.buscar_valor('SELECT EXISTS(SELECT 1 FROM locadora_aluguel WHERE carro_id = %s)', [carro_id]))


def excluir(carro_id: int) -> int:
    return db.executar(f'DELETE FROM {TABELA} WHERE id = %s', [carro_id])
