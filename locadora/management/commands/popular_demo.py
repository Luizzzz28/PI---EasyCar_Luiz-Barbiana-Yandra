'''
Arquivo responsável por popular o banco de dados, criando dados de demonstração de exemplo,
através de um comando de gerenciamento. Pode ser executado várias vezes sem criar duplicatas.'''

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from locadora import services
from locadora.models import Aluguel, Carro, PerfilCliente
from locadora.permissions import GRUPO_CLIENTES, GRUPO_FUNCIONARIOS

SENHA_DEMO = 'easycar-demo-2026'

CARROS = [
    ('Fiat Argo', 'BRA2E19', 2023),
    ('Chevrolet Onix', 'QWE1234', 2022),
    ('Hyundai HB20', 'RTY5F67', 2024),
    ('Renault Kwid', 'JKL9876', 2021),
    ('Volkswagen Nivus', 'ASD4G56', 2023),
    ('Toyota Corolla', 'ZXC7V89', 2022),
    ('Nissan Kicks', 'RST3U67', 2022),
    ('Honda City', 'HJK1L23', 2024),
    ('Jeep Renegade', 'MNO2P45', 2023),
    ('Peugeot 208', 'VWX4Y89', 2025),
    ('BYD Dolphin', 'BCD5E12', 2025),
    ('Toyota Yaris', 'FGH6J78', 2023),
    ('Chevrolet Tracker', 'QAZ1S23', 2024),
    ('Ford EcoSport', 'WSX2D34', 2022),
    ('Chevrolet Zafira', 'EDC3F45', 2021),
    ('Honda City', 'FGH8J12', 2024),
]

CLIENTES = [
    ('bruno', 'Bruno', 'Lima', '12345678901', '(61) 99999-0001', 'QNA 10, Taguatinga'),
    ('carla', 'Carla', 'Souza', '98765432100', '(61) 99999-0002', 'Rua 20, Águas Claras'),
]


class Command(BaseCommand):
    help = 'Cria dados de demonstração (pode ser executado várias vezes).'

    @transaction.atomic
    def handle(self, *args, **options):
        funcionarios, _ = Group.objects.get_or_create(name=GRUPO_FUNCIONARIOS)
        clientes, _ = Group.objects.get_or_create(name=GRUPO_CLIENTES)

        ana = self.usuario('ana', 'Ana', 'Ribeiro', funcionarios)

        perfis = []
        for username, nome, sobrenome, cnh, telefone, endereco in CLIENTES:
            user = self.usuario(username, nome, sobrenome, clientes)
            perfil, _ = PerfilCliente.objects.get_or_create(
                user=user, defaults={'cnh': cnh, 'telefone': telefone, 'endereco': endereco}
            )
            perfis.append(perfil)

        carros = [
            Carro.objects.get_or_create(placa=placa, defaults={'modelo': modelo, 'ano': ano})[0]
            for modelo, placa, ano in CARROS
        ]

        if not Aluguel.objects.exists():
            hoje = timezone.localdate()
            antigo = services.registrar_aluguel({
                'perfil_cliente': perfis[0], 'carro': carros[0], 'valor': Decimal('450.00'),
                'data_inicio': hoje - timedelta(days=20), 'data_fim': hoje - timedelta(days=17),
            }, ana)
            services.devolver_carro(antigo)
            services.registrar_aluguel({
                'perfil_cliente': perfis[0], 'carro': carros[1], 'valor': Decimal('600.00'),
                'data_inicio': hoje, 'data_fim': hoje + timedelta(days=4),
            }, ana)
            services.registrar_aluguel({
                'perfil_cliente': perfis[1], 'carro': carros[0], 'valor': Decimal('300.00'),
                'data_inicio': hoje, 'data_fim': hoje + timedelta(days=2),
            }, ana)

        self.stdout.write(self.style.SUCCESS(
            f'Pronto: {Carro.objects.count()} carros, {PerfilCliente.objects.count()} clientes, '
            f'{Aluguel.objects.count()} aluguéis. Usuários ana, bruno e carla com a senha "{SENHA_DEMO}".'
        ))

    def usuario(self, username, nome, sobrenome, grupo):
        user, criado = User.objects.get_or_create(
            username=username, defaults={'first_name': nome, 'last_name': sobrenome}
        )
        if criado:
            user.set_password(SENHA_DEMO)
            user.save()
        user.groups.add(grupo)
        return user