from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import Categoria, Cliente
from .validators import calcular_dv
from .catalogo import CARROS_DISPONIVEIS


def cpf_teste(base9="390533447"):
    d1 = calcular_dv(base9)
    return base9 + str(d1) + str(calcular_dv(base9 + str(d1)))


class ClienteAPITest(APITestCase):
    def setUp(self):
        self.client.force_authenticate(User.objects.create_user("admin", password="x"))
        self.url = "/api/clientes/"
        self.cpf = cpf_teste()

    def payload(self, **extra):
        d = {"nome": "Maria Silva", "cpf": self.cpf, "telefone": "(61) 99999-1234"}
        d.update(extra)
        return d

    def test_cadastra_cliente_com_mascaras(self):
        r = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["telefone"], "(61) 99999-1234")

    def test_cpf_invalido(self):
        r = self.client.post(self.url, self.payload(cpf="111.111.111-11"), format="json")
        self.assertEqual(r.status_code, 400)

    def test_cpf_duplicado(self):
        self.client.post(self.url, self.payload(), format="json")
        r = self.client.post(self.url, self.payload(nome="Outra Pessoa"), format="json")
        self.assertEqual(r.status_code, 400)

    def test_exige_login(self):
        self.client.force_authenticate(None)
        self.assertIn(self.client.get(self.url).status_code, (401, 403))

    def test_tabela_de_taxas_de_atraso(self):
        Categoria.objects.create(nome="Econômico", diaria=100)
        r = self.client.get("/api/taxas-atraso/")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(len(r.data["faixas"]), 3)
        self.assertEqual(r.data["por_categoria"][0]["taxa_hora"], 10)


class LoginAPITest(APITestCase):
    def test_login_redireciona_para_api(self):
        User.objects.create_user(username="visitante", password="senha-teste")
        r = self.client.post(
            "/api-auth/login/",
            {"username": "visitante", "password": "senha-teste"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "/api/")


class ClientePageTest(TestCase):
    def setUp(self):
        User.objects.create_user(username="admin", password="senha-teste")
        self.client.login(username="admin", password="senha-teste")

    def test_pagina_de_clientes_exige_login(self):
        self.client.logout()
        r = self.client.get("/clientes/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/api-auth/login/", r["Location"])

    def test_cadastra_cliente_com_cpf_e_telefone_mascarados(self):
        r = self.client.post("/clientes/", {
            "nome": "Maria Silva",
            "cpf": "390.533.447-05",
            "telefone": "(61) 99999-1234",
        })
        self.assertRedirects(r, "/clientes/")
        cliente = Cliente.objects.get()
        self.assertEqual(cliente.cpf, "39053344705")
        self.assertEqual(cliente.telefone, "61999991234")

    def test_rejeita_cpf_invalido(self):
        r = self.client.post("/clientes/", {
            "nome": "Maria Silva",
            "cpf": "111.111.111-11",
            "telefone": "(61) 99999-1234",
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "CPF inválido.")
        self.assertEqual(Cliente.objects.count(), 0)

    def test_formulario_vazio_nao_cadastra_cliente(self):
        r = self.client.post("/clientes/", {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Cliente.objects.count(), 0)

    def test_busca_sem_resultados_nao_exibe_todos_os_clientes(self):
        Cliente.objects.create(
            nome="Maria Silva",
            cpf=cpf_teste(),
            telefone="61999991234",
        )
        r = self.client.get("/clientes/?q=nao-existe")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Nenhum cliente encontrado")
        self.assertNotContains(r, "Maria Silva")


class CarrosDisponiveisPageTest(TestCase):
    def test_catalogo_exibe_vinte_modelos_com_diaria_e_foto(self):
        response = self.client.get("/carros/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(CARROS_DISPONIVEIS), 20)
        self.assertContains(response, "20 modelos")
        for carro in CARROS_DISPONIVEIS:
            with self.subTest(modelo=carro["nome"]):
                self.assertContains(response, carro["nome"])
                preco = f'{carro["diaria"]:.2f}'.replace(".", ",")
                self.assertContains(response, f"R$ {preco}")
                self.assertTrue(
                    (
                        Path(__file__).resolve().parent
                        / "static"
                        / "core"
                        / "img"
                        / "cars"
                        / f'{carro["slug"]}.jpg'
                    ).is_file()
                )
                self.assertTrue(carro["credito"]["description_url"])

    def test_menu_publico_tem_carros_e_nao_exibe_botao_api(self):
        response = self.client.get("/carros/")
        self.assertContains(response, "Carros disponíveis")
        self.assertNotContains(response, ">API</a>")


class TaxasAtrasoPageTest(TestCase):
    def test_pagina_exibe_regras_calculadora_e_tabela_dos_vinte_carros(self):
        response = self.client.get("/taxas-atraso/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tabela de taxas de atraso")
        self.assertContains(response, "Calculadora de atraso")
        self.assertContains(response, "Até 1 hora")
        self.assertContains(response, "Acima de 3h")
        self.assertContains(response, "R$ 24,90")
        self.assertContains(response, "R$ 273,90")
        self.assertEqual(len(response.context["carros"]), 20)
        self.assertContains(response, "taxas_atraso.js")

    def test_links_de_navegacao_abrem_pagina_visual_de_taxas(self):
        User.objects.create_user(username="menu-admin", password="senha-teste")
        self.client.login(username="menu-admin", password="senha-teste")
        for pagina in ("/", "/clientes/", "/carros/"):
            with self.subTest(pagina=pagina):
                response = self.client.get(pagina)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'href="/taxas-atraso/"')

    def test_endpoint_json_da_api_continua_disponivel(self):
        User.objects.create_user(username="taxas-api", password="senha-teste")
        self.client.login(username="taxas-api", password="senha-teste")
        response = self.client.get("/api/taxas-atraso/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["faixas"]), 3)
