from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase

from locadora.models import Aluguel, Carro, PerfilCliente
from locadora.permissions import GRUPO_CLIENTES, GRUPO_FUNCIONARIOS


class DashboardIntegrationTests(TestCase):
    def setUp(self):
        funcionarios, _ = Group.objects.get_or_create(name=GRUPO_FUNCIONARIOS)
        self.funcionario = User.objects.create_user('funcionario', password='Senha-forte-123')
        self.funcionario.groups.add(funcionarios)
        self.client.force_login(self.funcionario)

    def test_dashboard_and_catalogue_read_the_root_database(self):
        carro = Carro.objects.create(
            modelo='Toyota Corolla',
            placa='ABC1D23',
            chassi='1HGCM82633A004352',
            ano=2024,
            diaria=Decimal('250.00'),
        )
        response = self.client.get('/carros/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Toyota Corolla')
        self.assertNotContains(response, 'ABC1D23')
        self.assertEqual(len(response.context['carros']), 20)
        carro_tela = next(item for item in response.context['carros'] if item.id == carro.pk)
        self.assertEqual(carro_tela.diaria, Decimal('250.00'))
        self.assertEqual(carro_tela.diaria_label, 'Diária cadastrada')
        self.assertEqual(carro_tela.categoria, 'Sedã')
        self.assertEqual(
            sum(item.nome == carro.modelo for item in response.context['carros']),
            1,
        )
        self.assertTrue(carro_tela.alugavel)
        self.assertEqual(response.context['veiculos_reais'], 1)
        self.assertEqual(response.context['unidades_demo'], 19)

        dashboard = self.client.get('/')
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, 'Enterprise Aluguel de carros')
        self.assertContains(dashboard, 'Toyota Corolla')
        self.assertEqual(dashboard.context['carros_count'], 1)
        self.assertEqual(dashboard.context['carros_demo_count'], 19)
        self.assertEqual(Carro.objects.get(pk=carro.pk).diaria, Decimal('250.00'))

    def test_catalog_shows_demo_units_with_rent_action_and_photo_credits(self):
        response = self.client.get('/carros/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['carros']), 20)
        self.assertContains(response, 'Toyota Corolla')
        self.assertContains(response, 'R$ 249,00')
        self.assertContains(response, 'Diária de demonstração')
        self.assertContains(response, 'Disponível · demonstração')
        self.assertContains(response, 'Alugar este carro')
        self.assertTrue(all(carro.credito.description_url for carro in response.context['carros']))
        self.assertTrue(all(carro.eh_demonstracao for carro in response.context['carros']))

    def test_rent_action_is_only_available_to_employees(self):
        self.client.logout()

        response = self.client.get('/carros/')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Alugar este carro')
        self.assertContains(response, 'a equipe pode registrar um aluguel de teste')

    def test_non_catalogue_vehicle_is_kept_with_the_reference_models(self):
        carro = Carro.objects.create(
            modelo='Volvo XC40',
            placa='XYZ1A23',
            ano=2025,
            diaria=Decimal('350.00'),
        )

        response = self.client.get('/carros/')

        self.assertEqual(len(response.context['carros']), 21)
        carro_tela = next(item for item in response.context['carros'] if item.id == carro.pk)
        self.assertEqual(carro_tela.diaria, Decimal('350.00'))
        self.assertEqual(carro_tela.status, 'Disponível')
        self.assertTrue(carro_tela.alugavel)

    def test_delay_rates_include_reference_catalog_models(self):
        response = self.client.get('/taxas-atraso/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['carros']), 20)
        self.assertContains(response, 'Toyota Corolla')
        self.assertContains(response, 'R$ 24,90')
        self.assertContains(response, 'R$ 273,90')

    def test_vehicle_form_saves_plate_chassis_and_daily_rate(self):
        response = self.client.post('/carros/novo/', {
            'modelo': 'Honda Civic',
            'placa': 'abc-1d23',
            'chassi': '1HGCM82633A004353',
            'ano': 2023,
            'diaria': '220.00',
        })
        self.assertEqual(response.status_code, 302, response.content)
        self.assertRedirects(response, '/carros/')
        carro = Carro.objects.get(placa='ABC1D23')
        self.assertEqual(carro.chassi, '1HGCM82633A004353')
        self.assertEqual(carro.status, Carro.Status.DISPONIVEL)

    def test_new_rental_uses_the_root_service_and_marks_car_unavailable(self):
        clientes, _ = Group.objects.get_or_create(name=GRUPO_CLIENTES)
        user = User.objects.create_user('cliente', first_name='Maria', last_name='Silva')
        user.groups.add(clientes)
        perfil = PerfilCliente.objects.create(
            user=user,
            cnh='12345678901',
            telefone='61999990000',
            endereco='Rua A, 10',
        )
        carro = Carro.objects.create(modelo='Fiat Argo', placa='DEF1G23', ano=2022)
        response = self.client.post('/alugueis/novo/', {
            'perfil_cliente': perfil.pk,
            'carro': carro.pk,
            'data_inicio': '2026-11-15',
            'data_fim': '2026-11-18',
            'valor': '450.00',
        })
        self.assertRedirects(response, '/')
        aluguel = Aluguel.objects.get()
        self.assertEqual(aluguel.carro, carro)
        self.assertEqual(aluguel.valor, Decimal('450.00'))
        carro.refresh_from_db()
        self.assertEqual(carro.status, Carro.Status.ALUGADO)

    def test_rental_vehicle_choices_show_only_the_model_name(self):
        cliente = User.objects.create_user('cliente_teste')
        PerfilCliente.objects.create(
            user=cliente,
            cnh='12345678901',
            telefone='61999990000',
            endereco='Rua de teste, 1',
        )
        response = self.client.get('/alugueis/novo/')
        carro = Carro.objects.get(modelo='Ford Mustang', eh_demonstracao=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<option value="{carro.pk}">{carro.modelo}</option>', html=True)
        self.assertNotContains(response, f'{carro.modelo} ({carro.placa})')

    def test_client_form_creates_root_user_and_profile(self):
        response = self.client.post('/clientes/', {
            'nome': 'Ana Souza',
            'username': 'ana.souza',
            'password': 'Xy!9_Locadora_Forte_2026',
            'cnh': '12345678901',
            'telefone': '(61) 99999-1234',
            'endereco': 'Rua das Flores, 10',
        })
        self.assertRedirects(response, '/clientes/')
        perfil = PerfilCliente.objects.select_related('user').get()
        self.assertEqual(perfil.user.get_full_name(), 'Ana Souza')
        self.assertTrue(perfil.user.groups.filter(name=GRUPO_CLIENTES).exists())
        self.assertEqual(perfil.telefone, '61999991234')

    def test_dashboard_requires_staff_group(self):
        self.client.logout()
        self.assertEqual(self.client.get('/').status_code, 302)
        visitante = User.objects.create_user('visitante', password='senha')
        self.client.force_login(visitante)
        self.assertEqual(self.client.get('/').status_code, 403)


class AdminThemeTests(TestCase):
    def test_admin_login_uses_enterprise_brand_and_styles(self):
        response = self.client.get('/admin/login/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enterprise Aluguel de carros')
        self.assertContains(response, 'core/css/admin.css')
