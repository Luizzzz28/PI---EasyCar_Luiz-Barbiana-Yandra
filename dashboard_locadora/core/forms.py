import re

from django import forms

from .catalogo import CARROS_DISPONIVEIS
from .models import Cliente


class ClienteForm(forms.ModelForm):
    cpf = forms.CharField(
        label="CPF",
        max_length=18,
        help_text="Informe o CPF com ou sem pontuação.",
        widget=forms.TextInput(attrs={"placeholder": "000.000.000-00", "autocomplete": "off"}),
    )
    telefone = forms.CharField(
        label="Telefone",
        max_length=20,
        help_text="Informe o DDD e o número.",
        widget=forms.TextInput(attrs={"placeholder": "(11) 99999-9999", "autocomplete": "tel"}),
    )

    class Meta:
        model = Cliente
        fields = ["nome", "cpf", "telefone"]
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Nome e sobrenome", "autocomplete": "name"}),
        }

    def clean_cpf(self):
        return re.sub(r"\D", "", self.cleaned_data["cpf"])

    def clean_telefone(self):
        return re.sub(r"\D", "", self.cleaned_data["telefone"])


class AluguelCatalogoForm(forms.Form):
    cliente = forms.ModelChoiceField(
        label="Cliente",
        queryset=Cliente.objects.none(),
        empty_label="Selecione um cliente cadastrado",
    )
    carro = forms.ChoiceField(label="Carro")
    diarias = forms.IntegerField(
        label="Quantidade de diárias",
        min_value=1,
        max_value=365,
        initial=1,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = Cliente.objects.order_by("nome")
        self.fields["carro"].choices = [
            (
                carro["slug"],
                f'{carro["nome"]} — R$ {carro["diaria"]:.2f} por diária',
            )
            for carro in CARROS_DISPONIVEIS
        ]
