import re

from django.core.exceptions import ValidationError


def somente_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def calcular_dv(base):
    """Dígito verificador do CPF (módulo 11)."""
    soma = sum(int(d) * p for d, p in zip(base, range(len(base) + 1, 1, -1)))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto


def cpf_valido(cpf):
    if len(cpf) != 11 or not cpf.isdigit() or cpf == cpf[0] * 11:
        return False
    d1 = calcular_dv(cpf[:9])
    d2 = calcular_dv(cpf[:9] + str(d1))
    return cpf[9:] == f"{d1}{d2}"


def validar_cpf(valor):
    if not cpf_valido(somente_digitos(valor)):
        raise ValidationError("CPF inválido.")


def validar_telefone(valor):
    t = somente_digitos(valor)
    if len(t) not in (10, 11) or int(t[:2]) < 11:
        raise ValidationError("Telefone inválido. Use DDD + número, ex.: (61) 99999-9999.")
    if len(t) == 11 and t[2] != "9":
        raise ValidationError("Celular com 11 dígitos deve começar com 9 após o DDD.")
