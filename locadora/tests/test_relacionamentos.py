from django.contrib.auth.models import User

from locadora.models import PerfilCliente

from .base import BaseApiTestCase


class RotasDoClienteTests(BaseApiTestCase):
    def test_me_alugueis_mostra_so_os_proprios(self):
        self.entrar(self.bruno)
        dados = self.client.get('/api/me/alugueis/').json()
        self.assertEqual([a['id'] for a in dados['results']], [self.aluguel_bruno.pk])
        self.assertEqual(dados['results'][0]['carro']['placa'], 'BRA2E19')

    def test_me_carros(self):
        self.entrar(self.bruno)
        dados = self.client.get('/api/me/carros/').json()
        self.assertEqual([c['placa'] for c in dados['results']], ['BRA2E19'])

    def test_cliente_sem_alugueis(self):
        self.entrar(self.carla)
        self.assertEqual(self.client.get('/api/me/alugueis/').json()['count'], 0)

    def test_cliente_nao_ve_aluguel_de_outro(self):
        self.entrar(self.carla)
        self.assertEqual(self.client.get(f'/api/alugueis/{self.aluguel_bruno.pk}/').status_code, 404)
        self.assertEqual(self.client.get('/api/alugueis/').json()['count'], 0)

    def test_me_mostra_o_perfil(self):
        self.entrar(self.bruno)
        self.assertEqual(self.client.get('/api/me/').json()['cnh'], '12345678901')


class RotasDeRelacionamentoTests(BaseApiTestCase):
    def setUp(self):
        self.entrar(self.ana)

    def test_perfil_carros_a_b(self):
        dados = self.client.get(f'/api/perfis-clientes/{self.perfil_bruno.pk}/carros/').json()
        self.assertEqual([c['placa'] for c in dados['results']], ['BRA2E19'])

    def test_carro_alugueis_b_c(self):
        dados = self.client.get(f'/api/carros/{self.argo.pk}/alugueis/').json()
        self.assertEqual(dados['results'][0]['cliente'], 'bruno')

    def test_perfil_carro_alugueis_a_b_c(self):
        url = f'/api/perfis-clientes/{self.perfil_bruno.pk}/carros/{self.argo.pk}/alugueis/'
        self.assertEqual(self.client.get(url).json()['count'], 1)
        url = f'/api/perfis-clientes/{self.perfil_carla.pk}/carros/{self.argo.pk}/alugueis/'
        self.assertEqual(self.client.get(url).json()['count'], 0)

    def test_perfil_alugueis(self):
        dados = self.client.get(f'/api/perfis-clientes/{self.perfil_bruno.pk}/alugueis/').json()
        self.assertEqual(dados['count'], 1)

    def test_funcionario_alugueis_1_n(self):
        dados = self.client.get(f'/api/funcionarios/{self.ana.pk}/alugueis/').json()
        self.assertEqual(dados['count'], 1)


class UsuariosEPerfisTests(BaseApiTestCase):
    def setUp(self):
        self.entrar(self.ana)

    def test_usuario_criado_entra_no_grupo_clientes(self):
        resposta = self.client.post('/api/users/', {'username': 'diego', 'password': 'senha-forte-123'})
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()['grupos'], ['Clientes'])
        self.assertNotIn('password', resposta.json())
        self.assertTrue(User.objects.get(username='diego').check_password('senha-forte-123'))

    def test_senha_fraca_e_recusada(self):
        resposta = self.client.post('/api/users/', {'username': 'diego', 'password': '123'})
        self.assertEqual(resposta.status_code, 400)

    def test_lista_de_usuarios_nao_mostra_funcionarios(self):
        nomes = [u['username'] for u in self.client.get('/api/users/').json()['results']]
        self.assertEqual(nomes, ['bruno', 'carla'])

    def test_cria_perfil_para_usuario_cliente(self):
        diego = self.client.post('/api/users/', {'username': 'diego', 'password': 'senha-forte-123'}).json()
        dados = {'user': diego['id'], 'cnh': '111.222.333-44', 'telefone': '61 98888-7777', 'endereco': 'QS 1'}
        resposta = self.client.post('/api/perfis-clientes/', dados)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()['cnh'], '11122233344')

    def test_perfil_so_para_usuario_do_grupo_clientes(self):
        dados = {'user': self.ana.pk, 'cnh': '11122233344', 'telefone': '1', 'endereco': 'x'}
        self.assertEqual(self.client.post('/api/perfis-clientes/', dados).status_code, 400)

    def test_um_perfil_por_usuario(self):
        dados = {'user': self.bruno.pk, 'cnh': '11122233344', 'telefone': '1', 'endereco': 'x'}
        self.assertEqual(self.client.post('/api/perfis-clientes/', dados).status_code, 400)

    def test_nao_apaga_cliente_com_alugueis(self):
        self.assertEqual(self.client.delete(f'/api/perfis-clientes/{self.perfil_bruno.pk}/').status_code, 409)
        self.assertEqual(self.client.delete(f'/api/users/{self.bruno.pk}/').status_code, 409)
        self.assertTrue(PerfilCliente.objects.filter(pk=self.perfil_bruno.pk).exists())

    def test_documentacao(self):
        for url in ['/api/schema/', '/api/docs/', '/api/docs/redoc/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)