'''
Arquivo serializers.py que serve para converter os dados do banco de dados em JSON ou 
vice-versa, além de validar os dados recebidos da API.'''

import re

from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Aluguel, Carro, PerfilCliente, Multa
from .permissions import GRUPO_CLIENTES


class UserSerializer(serializers.ModelSerializer):
    """Usuários criados pela API entram sempre no grupo Clientes."""

    grupos = serializers.SlugRelatedField(source='groups', many=True, read_only=True, slug_field='name')

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'grupos']
        extra_kwargs = {'password': {'write_only': True, 'required': False}}

    def validate(self, attrs):
        senha = attrs.get('password')
        if self.instance is None and not senha:
            raise serializers.ValidationError({'password': 'Informe uma senha.'})
        if senha:
            validate_password(senha)
        return attrs

    def create(self, validated_data):
        senha = validated_data.pop('password')
        user = User.objects.create_user(password=senha, **validated_data)
        grupo, _ = Group.objects.get_or_create(name=GRUPO_CLIENTES)
        user.groups.add(grupo)
        return user

    def update(self, instance, validated_data):
        senha = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if senha:
            user.set_password(senha)
            user.save(update_fields=['password'])
        return user


class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class PerfilClienteSerializer(serializers.ModelSerializer):
    # Só usuários do grupo Clientes, e cada um com no máximo um perfil (relação 1:1)
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name=GRUPO_CLIENTES),
        validators=[UniqueValidator(PerfilCliente.objects.all(), message='Este usuário já tem perfil de cliente.')],
    )
    # Aceita a CNH com pontos e traço; validate_cnh deixa só os 11 dígitos
    cnh = serializers.CharField(max_length=20)
    username = serializers.CharField(source='user.username', read_only=True)
    nome = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = PerfilCliente
        fields = ['id', 'user', 'username', 'nome', 'cnh', 'telefone', 'endereco']

    def validate_cnh(self, valor):
        cnh = re.sub(r'\D', '', valor)
        if len(cnh) != 11:
            raise serializers.ValidationError('A CNH deve ter 11 dígitos.')
        repetidas = PerfilCliente.objects.filter(cnh=cnh)
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError('Já existe um cliente com esta CNH.')
        return cnh


class CarroSerializer(serializers.ModelSerializer):
    # Aceita "abc-1234"; validate_placa grava "ABC1234" (7 caracteres, como no modelo)
    placa = serializers.CharField(max_length=10)

    class Meta:
        model = Carro
        fields = ['id', 'modelo', 'placa', 'ano', 'status']

    def validate_placa(self, valor):
        placa = re.sub(r'[\s-]', '', valor).upper()
        # Aceita o padrão antigo (ABC1234) e o Mercosul (ABC1D23)
        if not re.fullmatch(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}', placa):
            raise serializers.ValidationError('Placa inválida. Use ABC1234 ou ABC1D23.')
        repetidas = Carro.objects.filter(placa=placa)
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError('Já existe um carro com esta placa.')
        return placa

    def validate_ano(self, valor):
        limite = timezone.localdate().year + 1
        if not 1950 <= valor <= limite:
            raise serializers.ValidationError(f'O ano deve estar entre 1950 e {limite}.')
        return valor

    def validate_status(self, valor):
        atual = self.instance.status if self.instance else None
        if valor == Carro.Status.ALUGADO and atual != Carro.Status.ALUGADO:
            raise serializers.ValidationError('O status "alugado" é definido ao registrar um aluguel.')
        if atual == Carro.Status.ALUGADO and valor != Carro.Status.ALUGADO:
            raise serializers.ValidationError('Este carro tem aluguel ativo: registre a devolução.')
        return valor


class AluguelSerializer(serializers.ModelSerializer):
    cliente = serializers.CharField(source='perfil_cliente.user.username', read_only=True)
    placa = serializers.CharField(source='carro.placa', read_only=True)
    funcionario = serializers.CharField(source='funcionario.username', read_only=True)

    class Meta:
        model = Aluguel
        fields = [
            'id', 'perfil_cliente', 'cliente', 'carro', 'placa', 'funcionario',
            'data_inicio', 'data_fim', 'valor', 'status', 'data_devolucao',
        ]
        read_only_fields = ['status', 'data_devolucao']

    def validate_carro(self, carro):
        if self.instance is not None and carro != self.instance.carro:
            raise serializers.ValidationError('Não é possível trocar o carro de um aluguel. Exclua e registre outro.')
        return carro

    def validate(self, attrs):
        # Num PATCH, a data que não veio no pedido é a que já está gravada
        inicio = attrs.get('data_inicio', getattr(self.instance, 'data_inicio', None))
        fim = attrs.get('data_fim', getattr(self.instance, 'data_fim', None))
        if inicio and fim and fim < inicio:
            raise serializers.ValidationError({'data_fim': 'A data de fim não pode ser anterior à de início.'})
        return attrs


class AluguelDetalhadoSerializer(AluguelSerializer):
    """Aluguel com os dados completos do carro (rotas de relacionamento)."""

    carro = CarroSerializer(read_only=True)


class MultaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Multa
        fields = ['id', 'aluguel', 'funcionario', 'valor', 'descricao', 
                  'data_infracao', 'status', 'dias_atrasos', 'data_pagamento']