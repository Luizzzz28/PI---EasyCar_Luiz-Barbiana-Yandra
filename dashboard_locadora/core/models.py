import math
from decimal import Decimal

from django.db import models

from .validators import validar_cpf, validar_telefone

# Regras da multa (ajuste conforme o enunciado do projeto)
TOLERANCIA_HORAS = Decimal("1")      # até 1h: sem cobrança
LIMITE_FAIXA_HORA = Decimal("3")     # de 1h a 3h: cobra por hora
PERCENTUAL = Decimal("0.10")         # 10% da diária

FAIXAS_ATRASO = (
    {"faixa": "Até 1 hora", "regra": "Tolerância - sem cobrança"},
    {"faixa": "De 1h até 3h", "regra": "10% da diária por hora de atraso"},
    {"faixa": "Acima de 3h", "regra": "1 diária + 10%, por dia (ou fração) de atraso"},
)


class Categoria(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    diaria = models.DecimalField("valor da diária", max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["diaria"]

    def __str__(self):
        return self.nome

    @property
    def taxa_hora(self):
        return self.diaria * PERCENTUAL

    @property
    def multa_dia(self):
        return self.diaria * (1 + PERCENTUAL)


class Cliente(models.Model):
    nome = models.CharField(max_length=120)
    cpf = models.CharField("CPF", max_length=11, unique=True, validators=[validar_cpf],
                           help_text="Somente números (11 dígitos).")
    telefone = models.CharField(max_length=11, validators=[validar_telefone],
                                help_text="DDD + número, somente números.")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Aluguel(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="alugueis")
    veiculo = models.CharField("veículo", max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    diarias = models.PositiveIntegerField("nº de diárias", default=1)
    horas_atraso = models.DecimalField("horas de atraso", max_digits=5, decimal_places=1, default=0)

    class Meta:
        ordering = ["-id"]
        verbose_name_plural = "aluguéis"

    def __str__(self):
        return f"#{self.pk} {self.cliente} - {self.veiculo}"

    @property
    def valor(self):
        return self.categoria.diaria * self.diarias

    @property
    def multa(self):
        h = self.horas_atraso
        if h <= TOLERANCIA_HORAS:
            return Decimal("0")
        if h <= LIMITE_FAIXA_HORA:
            return self.categoria.taxa_hora * h
        dias = math.ceil(h / 24)
        return self.categoria.multa_dia * dias

    @property
    def total(self):
        return self.valor + self.multa
