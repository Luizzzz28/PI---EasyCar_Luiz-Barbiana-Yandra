"""Garante que a nova constraint do banco não atrapalha a validação da API."""

import pytest

from locadora.serializers import AluguelSerializer, MultaSerializer

pytestmark = pytest.mark.django_db


def test_aluguel_serializer_valida_com_a_nova_constraint(perfil, carro):
    s = AluguelSerializer(
        data={
            'perfil_cliente': perfil.pk,
            'carro': carro.pk,
            'data_inicio': '2026-01-10',
            'data_fim': '2026-01-15',
            'valor': '350.00',
        }
    )
    assert s.is_valid(), s.errors


def test_multa_serializer_usa_campos_do_model():
    assert 'motivo' in MultaSerializer().fields
