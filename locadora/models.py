#Arquivo para criação de modelos do Django

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

    #--- MODELOS ESPECÍFICOS ---

#Modelo de perfil de cliente, que estende o modelo de usuário padrão do Django
class PerfilCliente(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil_cliente'
    )
    cnh = models.CharField('CNH', max_length=11, unique=True)
    telefone = models.CharField(max_length=20)
    endereco = models.CharField('endereço', max_length=255)

    # N:N com Carro, usando Aluguel como tabela intermediária
    carros = models.ManyToManyField('Carro', through='Aluguel', related_name='clientes', blank=True)

    class Meta:
        ordering = ['user__username']
        verbose_name = 'perfil de cliente'
        verbose_name_plural = 'perfis de clientes'

    def __str__(self):
        return self.user.get_full_name() or self.user.username


#Modelo de carro, com status de disponibilidade
class Carro(models.Model):
    class Status(models.TextChoices):
        DISPONIVEL = 'disponivel', 'Disponível'
        ALUGADO = 'alugado', 'Alugado'
        MANUTENCAO = 'manutencao', 'Em manutenção'

    modelo = models.CharField(max_length=100)
    placa = models.CharField(max_length=7, unique=True)
    ano = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DISPONIVEL)

    class Meta:
        ordering = ['modelo', 'placa']

    def __str__(self):
        return f'{self.modelo} ({self.placa})'


#Modelo de aluguel, que relaciona um perfil de cliente, um carro e um funcionário
class Aluguel(models.Model):
    class Status(models.TextChoices):
        ATIVO = 'ativo', 'Ativo'
        FINALIZADO = 'finalizado', 'Finalizado'

    perfil_cliente = models.ForeignKey(PerfilCliente, on_delete=models.PROTECT, related_name='alugueis')
    carro = models.ForeignKey(Carro, on_delete=models.PROTECT, related_name='alugueis')
    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='alugueis_registrados'
    )
    data_inicio = models.DateField('data de início')
    data_fim = models.DateField('data de fim prevista')
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ATIVO)
    data_devolucao = models.DateField('data de devolução', null=True, blank=True)

    class Meta:
        ordering = ['-data_inicio', '-id']
        verbose_name_plural = 'aluguéis'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(data_fim__gte=models.F('data_inicio')),
                name='aluguel_fim_depois_do_inicio',
            ),
            models.CheckConstraint(condition=models.Q(valor__gt=0), name='aluguel_valor_positivo'),
        ]

    def __str__(self):
        return f'Aluguel {self.pk}: {self.carro.placa} para {self.perfil_cliente}'


#Modelo de multas, que relaciona um aluguel e um funcionário
class Multa(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        PAGO = 'pago', 'Pago'
        ABONADO = 'abonado', 'Abonado'

    aluguel = models.ForeignKey(Aluguel, on_delete=models.PROTECT, related_name='multas')
    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='multas_registradas'
    )
    dias_atrasos = models.PositiveIntegerField('Qtd de dias atrasados', validators=[MinValueValidator(1)])
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    data_infracao = models.DateField('data da infração')
    data_pagamento = models.DateField('data de pagamento', null=True, blank=True)
    motivo = models.TextField('motivo da multa', max_length=500)
    class Meta:
        ordering = ['-data_infracao', '-id']
        verbose_name_plural = 'multas'

    def __str__(self):
        return f'Multa {self.pk}: {self.aluguel} - {self.funcionario.get_full_name()}'