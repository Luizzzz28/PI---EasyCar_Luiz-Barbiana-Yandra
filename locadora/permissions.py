"""Controle de acesso pelos grupos do Django (criados no admin)."""
from rest_framework.permissions import SAFE_METHODS, BasePermission

GRUPO_FUNCIONARIOS = 'Funcionários'
GRUPO_CLIENTES = 'Clientes'


def eh_funcionario(user):
    """Superusuário também conta como funcionário, para poder administrar pela API."""
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=GRUPO_FUNCIONARIOS).exists()
    )


def eh_cliente(user):
    return user.is_authenticated and user.groups.filter(name=GRUPO_CLIENTES).exists()


class EhFuncionario(BasePermission):
    message = 'Apenas usuários do grupo Funcionários podem acessar este recurso.'

    def has_permission(self, request, view):
        return eh_funcionario(request.user)


class EhCliente(BasePermission):
    message = 'Rota exclusiva para usuários do grupo Clientes.'

    def has_permission(self, request, view):
        return eh_cliente(request.user)


class FuncionarioEditaClienteConsulta(BasePermission):
    """Funcionário: tudo. Cliente: só GET. Usuário sem grupo: nada."""

    message = 'Clientes podem apenas consultar.'

    def has_permission(self, request, view):
        if eh_funcionario(request.user):
            return True
        return request.method in SAFE_METHODS and eh_cliente(request.user)