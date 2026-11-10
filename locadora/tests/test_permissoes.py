from .base import BaseApiTestCase


class PermissoesTests(BaseApiTestCase):
    def test_sem_login_so_ve_a_raiz(self):
        self.assertEqual(self.client.get('/api/').status_code, 200)
        self.assertEqual(self.client.get('/api/carros/').status_code, 401)

    def test_usuario_sem_grupo_nao_acessa_nada(self):
        self.entrar(self.sem_grupo)
        for url in ['/api/carros/', '/api/alugueis/', '/api/perfis-clientes/', '/api/me/alugueis/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_cliente_consulta_carros_mas_nao_edita(self):
        self.entrar(self.bruno)
        self.assertEqual(self.client.get('/api/carros/').status_code, 200)
        resposta = self.client.post('/api/carros/', {'modelo': 'X', 'placa': 'AAA1234', 'ano': 2024})
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(self.client.delete(f'/api/carros/{self.onix.pk}/').status_code, 403)

    def test_cliente_nao_acessa_rotas_de_funcionario(self):
        self.entrar(self.bruno)
        urls = [
            '/api/users/', '/api/perfis-clientes/', '/api/funcionarios/',
            f'/api/carros/{self.argo.pk}/alugueis/',
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_cliente_nao_registra_aluguel(self):
        self.entrar(self.bruno)
        self.assertEqual(self.client.post('/api/alugueis/', self.novo_aluguel()).status_code, 403)

    def test_funcionario_nao_usa_rotas_me(self):
        self.entrar(self.ana)
        self.assertEqual(self.client.get('/api/me/alugueis/').status_code, 403)

    def test_token_pelo_login(self):
        resposta = self.client.post('/api/auth/token/', {'username': 'bruno', 'password': 'senha-forte-123'})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('token', resposta.json())