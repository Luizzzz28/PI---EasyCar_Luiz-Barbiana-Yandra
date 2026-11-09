"""Repositório de perfis de cliente (tabela ``locadora_perfilcliente``).

O usuário (login, nome, e-mail) fica na tabela ``auth_user`` do Django. Aqui só
LEMOS dela, via JOIN, para mostrar username e nome junto do perfil.
"""

from __future__ import annotations

from typing import TypedDict, cast

from locadora import db
from locadora.repositories.carros import CarroLinha

TABELA = 'locadora_perfilcliente'

SELECT_COM_USUARIO = f"""
    SELECT p.id, p.user_id, u.username, u.first_name, u.last_name, p.cnh, p.telefone, p.endereco
    FROM {TABELA} p
    JOIN auth_user u ON u.id = p.user_id
"""


class ClienteLinha(TypedDict):
    id: int
    user_id: int
    username: str
    first_name: str
    last_name: str
    cnh: str
    telefone: str
    endereco: str


def listar(limite: int = 20, offset: int = 0) -> list[ClienteLinha]:
    sql = SELECT_COM_USUARIO + ' ORDER BY u.username LIMIT %s OFFSET %s'
    return cast(list[ClienteLinha], db.buscar_todos(sql, [limite, offset]))


def buscar_por_id(perfil_id: int) -> ClienteLinha | None:
    return cast(ClienteLinha | None, db.buscar_um(SELECT_COM_USUARIO + ' WHERE p.id = %s', [perfil_id]))


def buscar_por_user_id(user_id: int) -> ClienteLinha | None:
    """Usado nas rotas /me/: acha o perfil do usuário logado."""
    return cast(ClienteLinha | None, db.buscar_um(SELECT_COM_USUARIO + ' WHERE p.user_id = %s', [user_id]))


def buscar_por_cnh(cnh: str) -> ClienteLinha | None:
    return cast(ClienteLinha | None, db.buscar_um(SELECT_COM_USUARIO + ' WHERE p.cnh = %s', [cnh]))


def criar(user_id: int, cnh: str, telefone: str, endereco: str) -> int:
    """Cria o perfil e devolve o id. ``user_id`` deve existir em auth_user (1 perfil por usuário)."""
    novo_id = db.buscar_valor(
        f'INSERT INTO {TABELA} (user_id, cnh, telefone, endereco) VALUES (%s, %s, %s, %s) RETURNING id',
        [user_id, cnh, telefone, endereco],
    )
    return int(novo_id)


def atualizar(perfil_id: int, telefone: str, endereco: str) -> int:
    return db.executar(
        f'UPDATE {TABELA} SET telefone = %s, endereco = %s WHERE id = %s',
        [telefone, endereco, perfil_id],
    )


def carros_alugados(perfil_id: int) -> list[CarroLinha]:
    """Carros que o cliente já alugou (relação N:N via locadora_aluguel), sem repetir."""
    sql = """
        SELECT DISTINCT c.id, c.marca, c.modelo, c.placa, c.ano, c.status
        FROM locadora_carro c
        JOIN locadora_aluguel a ON a.carro_id = c.id
        WHERE a.perfil_cliente_id = %s
        ORDER BY c.modelo, c.placa
    """
    return cast(list[CarroLinha], db.buscar_todos(sql, [perfil_id]))


def tem_alugueis(perfil_id: int) -> bool:
    return bool(
        db.buscar_valor('SELECT EXISTS(SELECT 1 FROM locadora_aluguel WHERE perfil_cliente_id = %s)', [perfil_id])
    )


def excluir(perfil_id: int) -> int:
    return db.executar(f'DELETE FROM {TABELA} WHERE id = %s', [perfil_id])
