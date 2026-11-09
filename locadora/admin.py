#Arquivo admin.py para registrar os modelos no painel de administração do Django

from django.contrib import admin

from .models import Aluguel, Carro, PerfilCliente, Multa
from .permissions import GRUPO_CLIENTES, GRUPO_FUNCIONARIOS

# User, Group e Token já são registrados pelo Django e pelo DRF (rest_framework.authtoken)


#Registrar modelo de PerfilCliente
@admin.register(PerfilCliente)
class PerfilClienteAdmin(admin.ModelAdmin):
    list_display = ['user', 'cnh', 'telefone']
    search_fields = ['user__username', 'user__first_name', 'cnh']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = db_field.related_model.objects.filter(groups__name=GRUPO_CLIENTES)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


#Registrar modelo de Carro
@admin.register(Carro)
class CarroAdmin(admin.ModelAdmin):
    list_display = ['placa', 'modelo', 'ano', 'status']
    list_filter = ['status']
    search_fields = ['placa', 'modelo']


#Registrar modelo de Aluguel
@admin.register(Aluguel)
class AluguelAdmin(admin.ModelAdmin):
    list_display = ['id', 'carro', 'perfil_cliente', 'funcionario', 'data_inicio', 'data_fim', 'valor', 'status']
    list_filter = ['status', 'funcionario']
    search_fields = ['carro__placa', 'perfil_cliente__user__username']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'funcionario':
            kwargs['queryset'] = db_field.related_model.objects.filter(groups__name=GRUPO_FUNCIONARIOS)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


#Registrar modelo de Multa
@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ['id', 'aluguel', 'funcionario', 'data_infracao', 'data_pagamento', 'motivo', 'status']
    list_filter = ['status', 'funcionario']
    search_fields = ['aluguel__carro__placa', 'aluguel__perfil_cliente__user__username']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'funcionario':
            kwargs['queryset'] = db_field.related_model.objects.filter(groups__name=GRUPO_FUNCIONARIOS)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)