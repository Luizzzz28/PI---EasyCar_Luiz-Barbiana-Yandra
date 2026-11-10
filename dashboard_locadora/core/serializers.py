import re

from rest_framework import serializers

from .models import Aluguel, Categoria, Cliente


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nome", "diaria"]


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ["id", "nome", "cpf", "telefone", "criado_em"]
        read_only_fields = ["criado_em"]

    def to_internal_value(self, data):
        # Aceita "123.456.789-09" ou "(61) 99999-9999": normaliza para só dígitos
        # antes das validações (assim a checagem de CPF duplicado também funciona).
        data = data.copy()
        for campo in ("cpf", "telefone"):
            if isinstance(data.get(campo), str):
                data[campo] = re.sub(r"\D", "", data[campo])
        if isinstance(data.get("nome"), str):
            data["nome"] = " ".join(data["nome"].split())
        return super().to_internal_value(data)

    def validate_nome(self, valor):
        if len(valor.split()) < 2:
            raise serializers.ValidationError("Informe nome e sobrenome.")
        return valor

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        c, t = instance.cpf, instance.telefone
        ret["cpf"] = f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"
        meio = 7 if len(t) == 11 else 6
        ret["telefone"] = f"({t[:2]}) {t[2:meio]}-{t[meio:]}"
        return ret


class AluguelSerializer(serializers.ModelSerializer):
    valor = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    multa = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Aluguel
        fields = ["id", "cliente", "veiculo", "categoria", "diarias", "horas_atraso", "valor", "multa"]
