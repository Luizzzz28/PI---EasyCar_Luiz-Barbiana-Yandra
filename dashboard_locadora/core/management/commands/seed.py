from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Aluguel, Categoria, Cliente
from core.validators import calcular_dv


def cpf_ficticio(base9):
    """Gera um CPF matematicamente válido, mas FICTÍCIO, só para testes."""
    d1 = calcular_dv(base9)
    return base9 + str(d1) + str(calcular_dv(base9 + str(d1)))


class Command(BaseCommand):
    help = "Cria categorias, clientes fictícios e aluguéis de exemplo"

    def handle(self, *args, **options):
        Aluguel.objects.all().delete()
        cats = {}
        for nome, diaria in [("Econômico", 120), ("Sedan", 180), ("SUV", 260), ("Luxo", 450)]:
            cats[nome], _ = Categoria.objects.update_or_create(nome=nome, defaults={"diaria": diaria})

        dados = [
            ("Ana Souza", "Fiat Argo", "Econômico", 3, 0),
            ("Carlos Lima", "Toyota Corolla", "Sedan", 5, 2),
            ("Marina Alves", "Jeep Compass", "SUV", 4, 6),
            ("João Pereira", "BMW 320i", "Luxo", 2, 0),
            ("Paula Costa", "VW Polo", "Econômico", 7, "0.5"),
            ("Rafael Nunes", "Honda Civic", "Sedan", 3, 28),
            ("Lúcia Matos", "Toyota Hilux", "SUV", 6, 0),
            ("Diego Rocha", "Mercedes C200", "Luxo", 3, 4),
        ]
        for i, (nome, vei, cat, dias, atraso) in enumerate(dados, start=1):
            cliente, _ = Cliente.objects.get_or_create(
                cpf=cpf_ficticio(f"{i}{i * 7 % 10}2345{i}{i}1"[:9].ljust(9, "3")),
                defaults={"nome": nome, "telefone": f"6199{i:03d}{i:04d}"[:11]},
            )
            Aluguel.objects.create(cliente=cliente, veiculo=vei, categoria=cats[cat],
                                   diarias=dias, horas_atraso=Decimal(str(atraso)))
        self.stdout.write(self.style.SUCCESS("Dados de exemplo criados (CPFs fictícios)."))
