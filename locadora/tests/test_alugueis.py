from locadora.models import Aluguel, Carro

from .base import BaseApiTestCase


class AluguelTests(BaseApiTestCase):
    def setUp(self):
        self.entrar(self.ana)

    def test_registrar_marca_carro_como_alugado(self):
        resposta = self.client.post('/api/alugueis/', self.novo_aluguel())
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()['funcionario'], 'ana')
        self.assertEqual(resposta.json()['status'], 'ativo')
        self.onix.refresh_from_db()
        self.assertEqual(self.onix.status, Carro.Status.ALUGADO)

    def test_carro_alugado_nao_pode_ser_alugado_de_novo(self):
        resposta = self.client.post('/api/alugueis/', self.novo_aluguel(carro=self.argo.pk))
        self.assertEqual(resposta.status_code, 409)

    def test_data_fim_antes_do_inicio(self):
        resposta = self.client.post('/api/alugueis/', self.novo_aluguel(data_fim='2026-11-01'))
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('data_fim', resposta.json())

    def test_valor_precisa_ser_positivo(self):
        resposta = self.client.post('/api/alugueis/', self.novo_aluguel(valor='0'))
        self.assertEqual(resposta.status_code, 400)

    def test_devolver_finaliza_e_libera_o_carro(self):
        resposta = self.client.post(f'/api/alugueis/{self.aluguel_bruno.pk}/devolver/')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()['status'], 'finalizado')
        self.argo.refresh_from_db()
        self.assertEqual(self.argo.status, Carro.Status.DISPONIVEL)
        segunda = self.client.post(f'/api/alugueis/{self.aluguel_bruno.pk}/devolver/')
        self.assertEqual(segunda.status_code, 409)

    def test_excluir_aluguel_ativo_libera_o_carro(self):
        self.assertEqual(self.client.delete(f'/api/alugueis/{self.aluguel_bruno.pk}/').status_code, 204)
        self.argo.refresh_from_db()
        self.assertEqual(self.argo.status, Carro.Status.DISPONIVEL)

    def test_put_altera_datas_e_valor(self):
        dados = self.novo_aluguel(
            perfil_cliente=self.perfil_bruno.pk, carro=self.argo.pk, valor='500.00',
            data_inicio='2026-11-01', data_fim='2026-11-05',
        )
        resposta = self.client.put(f'/api/alugueis/{self.aluguel_bruno.pk}/', dados)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()['valor'], '500.00')

    def test_nao_troca_carro_de_aluguel(self):
        resposta = self.client.patch(f'/api/alugueis/{self.aluguel_bruno.pk}/', {'carro': self.onix.pk})
        self.assertEqual(resposta.status_code, 400)

    def test_nao_apaga_carro_com_alugueis(self):
        self.assertEqual(self.client.delete(f'/api/carros/{self.argo.pk}/').status_code, 409)
        self.assertTrue(Aluguel.objects.filter(carro=self.argo).exists())


class CarroTests(BaseApiTestCase):
    def setUp(self):
        self.entrar(self.ana)

    def test_placa_e_normalizada(self):
        resposta = self.client.post('/api/carros/', {'modelo': ' Renault Kwid', 'placa': 'jkl-9876', 'ano': 2021})
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()['placa'], 'JKL9876')

    def test_placa_repetida_com_outra_grafia(self):
        resposta = self.client.post('/api/carros/', {'modelo': 'Chevrolet Onix', 'placa': 'qwe-1234', 'ano': 2022})
        self.assertEqual(resposta.status_code, 400)

    def test_placa_e_ano_invalidos(self):
        resposta = self.client.post('/api/carros/', {'modelo': 'X', 'placa': '1234ABC', 'ano': 1900})
        self.assertEqual(set(resposta.json()), {'placa', 'ano'})

    def test_status_alugado_nao_e_manual(self):
        resposta = self.client.patch(f'/api/carros/{self.onix.pk}/', {'status': 'alugado'})
        self.assertEqual(resposta.status_code, 400)
        resposta = self.client.patch(f'/api/carros/{self.argo.pk}/', {'status': 'disponivel'})
        self.assertEqual(resposta.status_code, 400)

    def test_filtro_por_status(self):
        dados = self.client.get('/api/carros/?status=disponivel').json()
        self.assertEqual([c['placa'] for c in dados['results']], ['QWE1234'])