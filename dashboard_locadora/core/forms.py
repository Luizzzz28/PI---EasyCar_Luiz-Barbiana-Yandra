import re

from django import forms

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
