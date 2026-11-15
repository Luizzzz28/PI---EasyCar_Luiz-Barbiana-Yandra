import re
from decimal import Decimal
from types import SimpleNamespace

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.text import slugify

from dashboard_locadora.core.catalogo import CARROS_DISPONIVEIS, PERCENTUAL
from . import services
from .models import Aluguel, Carro, Multa, PerfilCliente
from .permissions import GRUPO_CLIENTES, eh_funcionario

TOLERANCIA_HORAS = Decimal('1')
LIMITE_FAIXA_HORA = Decimal('3')
PERCENTUAL_MULTA = PERCENTUAL
FAIXAS_ATRASO = (
    {'faixa': 'Até 1 hora', 'regra': 'Tolerância - sem cobrança'},
    {'faixa': 'De 1h até 3h', 'regra': '10% da diária por hora de atraso'},
    {'faixa': 'Acima de 3h', 'regra': '1 diária + 10%, por dia (ou fração) de atraso'},
)

User = get_user_model()


def _somente_digitos(valor):
    return re.sub(r'\D', '', valor or '')


def _carro_para_tela(carro, dados_catalogo=None):
    diaria = carro.diaria if carro else None
    if diaria is None and dados_catalogo:
        diaria = dados_catalogo['diaria']

    credito_catalogo = dados_catalogo['credito'] if dados_catalogo else None
    if carro and carro.diaria is not None:
        diaria_label = 'Diária cadastrada'
    elif dados_catalogo:
        diaria_label = 'Diária de referência'
    else:
        diaria_label = 'Diária'

    return SimpleNamespace(
        id=carro.pk if carro else None,
        slug=str(carro.pk) if carro else dados_catalogo['slug'],
        nome=carro.modelo if carro else dados_catalogo['nome'],
        ano=carro.ano if carro else None,
        placa=carro.placa if carro else '',
        categoria=dados_catalogo['categoria'] if dados_catalogo else '',
        status=carro.get_status_display() if carro else 'Modelo demonstrativo',
        diaria=diaria,
        diaria_label=diaria_label,
        taxa_hora=diaria * PERCENTUAL_MULTA if diaria is not None else None,
        multa_dia=diaria * (1 + PERCENTUAL_MULTA) if diaria is not None else None,
        imagem=dados_catalogo['imagem'] if dados_catalogo else 'core/img/car-photo-fleet.jpg',
        credito=SimpleNamespace(
            description_url=credito_catalogo['description_url'] if credito_catalogo else '',
            autor=(
                credito_catalogo.get('autor') or credito_catalogo.get('artist')
                if credito_catalogo
                else 'Imagem ilustrativa'
            ),
            license=credito_catalogo['license'] if credito_catalogo else '',
            license_url=credito_catalogo['license_url'] if credito_catalogo else '',
        ),
        eh_catalogo=dados_catalogo is not None,
        eh_frota=carro is not None,
        alugavel=carro is not None and carro.status == Carro.Status.DISPONIVEL,
    )


def _carros_para_tela():
    catalogo_por_nome = {
        slugify(item['nome']): item
        for item in CARROS_DISPONIVEIS
    }
    carros_cadastrados = list(Carro.objects.order_by('modelo', 'placa'))
    carros = []

    for carro in carros_cadastrados:
        dados_catalogo = catalogo_por_nome.pop(slugify(carro.modelo), None)
        carros.append(_carro_para_tela(carro, dados_catalogo))

    carros.extend(
        _carro_para_tela(None, dados_catalogo)
        for dados_catalogo in catalogo_por_nome.values()
    )
    return carros, len(carros_cadastrados)


class ClienteCadastroForm(forms.Form):
    nome = forms.CharField(label='Nome completo', max_length=150)
    username = forms.CharField(label='Usuário', max_length=150)
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)
    cnh = forms.CharField(label='CNH', max_length=20)
    telefone = forms.CharField(label='Telefone', max_length=20)
    endereco = forms.CharField(label='Endereço', max_length=255)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Este nome de usuário já está em uso.')
        return username

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password)
        return password

    def clean_cnh(self):
        cnh = _somente_digitos(self.cleaned_data['cnh'])
        if len(cnh) != 11:
            raise forms.ValidationError('A CNH deve ter 11 dígitos.')
        if PerfilCliente.objects.filter(cnh=cnh).exists():
            raise forms.ValidationError('Já existe um cliente com esta CNH.')
        return cnh

    def clean_telefone(self):
        telefone = _somente_digitos(self.cleaned_data['telefone'])
        if len(telefone) not in (10, 11):
            raise forms.ValidationError('Informe DDD e telefone com 10 ou 11 dígitos.')
        return telefone


class CarroCadastroForm(forms.ModelForm):
    placa = forms.CharField(label='Placa', max_length=10)

    class Meta:
        model = Carro
        fields = ['modelo', 'placa', 'chassi', 'ano', 'diaria']
        widgets = {
            'diaria': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['chassi'].required = True

    def clean_placa(self):
        placa = re.sub(r'[\s-]', '', self.cleaned_data['placa']).upper()
        if not re.fullmatch(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}', placa):
            raise forms.ValidationError('Placa inválida. Use ABC1234 ou ABC1D23.')
        if Carro.objects.filter(placa=placa).exists():
            raise forms.ValidationError('Já existe um carro com esta placa.')
        return placa

    def clean_chassi(self):
        chassi = re.sub(r'\s', '', self.cleaned_data['chassi']).upper()
        if not re.fullmatch(r'[A-HJ-NPR-Z0-9]{17}', chassi):
            raise forms.ValidationError('O chassi deve ter 17 caracteres e não pode conter I, O ou Q.')
        if Carro.objects.filter(chassi=chassi).exists():
            raise forms.ValidationError('Já existe um carro com este chassi.')
        return chassi


class AluguelCadastroForm(forms.Form):
    perfil_cliente = forms.ModelChoiceField(
        label='Cliente',
        queryset=PerfilCliente.objects.none(),
        empty_label='Selecione um cliente',
    )
    carro = forms.ModelChoiceField(
        label='Carro',
        queryset=Carro.objects.none(),
        empty_label='Selecione um carro disponível',
    )
    data_inicio = forms.DateField(label='Data de início', widget=forms.DateInput(attrs={'type': 'date'}))
    data_fim = forms.DateField(label='Data prevista de devolução', widget=forms.DateInput(attrs={'type': 'date'}))
    valor = forms.DecimalField(
        label='Valor total do aluguel',
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['perfil_cliente'].queryset = PerfilCliente.objects.select_related('user').order_by(
            'user__first_name', 'user__username'
        )
        self.fields['carro'].queryset = Carro.objects.filter(
            status=Carro.Status.DISPONIVEL
        ).order_by('modelo', 'placa')

    def clean(self):
        dados = super().clean()
        inicio = dados.get('data_inicio')
        fim = dados.get('data_fim')
        if inicio and fim and fim < inicio:
            self.add_error('data_fim', 'A devolução prevista não pode ser anterior ao início.')
        return dados


def _exigir_funcionario(request):
    if not eh_funcionario(request.user):
        raise PermissionDenied


@login_required(login_url='/api-auth/login/')
def dashboard(request):
    _exigir_funcionario(request)
    filtro = request.GET.get('modelo', '').strip()
    alugueis = Aluguel.objects.select_related('carro', 'perfil_cliente__user', 'funcionario').prefetch_related(
        'multas'
    )
    if filtro:
        alugueis = alugueis.filter(carro__modelo=filtro)
    alugueis = list(alugueis)
    carros = list(Carro.objects.order_by('modelo', 'placa'))
    receita = sum((aluguel.valor for aluguel in alugueis), Decimal('0'))
    multas_por_aluguel = {
        item['aluguel_id']: item['total']
        for item in Multa.objects.filter(aluguel__in=alugueis)
        .values('aluguel_id')
        .annotate(total=Sum('valor'))
    }
    multas = sum(multas_por_aluguel.values(), Decimal('0'))
    hoje = timezone.localdate()
    for aluguel in alugueis:
        aluguel.multa_total = multas_por_aluguel.get(aluguel.pk, Decimal('0'))
        aluguel.atrasado = aluguel.status == Aluguel.Status.ATIVO and aluguel.data_fim < hoje
    atrasados = sum(
        aluguel.status == Aluguel.Status.ATIVO and aluguel.data_fim < hoje
        for aluguel in alugueis
    )
    por_categoria = []
    for modelo in sorted({aluguel.carro.modelo for aluguel in alugueis}):
        valor = sum(
            (aluguel.valor for aluguel in alugueis if aluguel.carro.modelo == modelo),
            Decimal('0'),
        )
        por_categoria.append({'nome': modelo, 'valor': valor})
    maximo = max((item['valor'] for item in por_categoria), default=Decimal('0')) or Decimal('1')
    for item in por_categoria:
        item['pct'] = int(item['valor'] / maximo * 100)
    diarios = {
        carro.modelo: float(carro.diaria)
        for carro in carros
        if carro.diaria is not None
    }
    tarifas_por_modelo = {}
    for carro in carros:
        if carro.diaria is not None:
            tarifas_por_modelo.setdefault(carro.modelo, carro)
    return render(request, 'core/dashboard.html', {
        'alugueis': alugueis,
        'categorias': [
            SimpleNamespace(
                nome=modelo,
                diaria=carro.diaria,
                taxa_hora=carro.diaria * PERCENTUAL_MULTA,
                multa_dia=carro.diaria * (1 + PERCENTUAL_MULTA),
            )
            for modelo, carro in sorted(tarifas_por_modelo.items())
        ],
        'filtro': filtro,
        'receita': receita,
        'multas': multas,
        'total': receita + multas,
        'qtd': len(alugueis),
        'atrasados': atrasados,
        'por_categoria': por_categoria,
        'diarias_json': diarios,
        'faixas_atraso': FAIXAS_ATRASO,
        'carros_count': len(carros),
    })


def carros_disponiveis(request):
    carros, veiculos_cadastrados = _carros_para_tela()
    return render(request, 'core/carros.html', {
        'carros': carros,
        'quantidade_modelos': len(CARROS_DISPONIVEIS),
        'veiculos_cadastrados': veiculos_cadastrados,
        'is_funcionario': eh_funcionario(request.user),
    })


@login_required(login_url='/api-auth/login/')
def novo_carro(request):
    _exigir_funcionario(request)
    form = CarroCadastroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        carro = form.save(commit=False)
        carro.status = Carro.Status.DISPONIVEL
        carro.save()
        messages.success(request, f'{carro.modelo} cadastrado com sucesso.')
        return redirect('carros-disponiveis')
    return render(request, 'core/novo_carro.html', {'form': form})


@login_required(login_url='/api-auth/login/')
def novo_aluguel(request):
    _exigir_funcionario(request)
    carro_id = request.GET.get('carro')
    initial = {}
    if carro_id:
        initial['carro'] = carro_id
    form = AluguelCadastroForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        try:
            aluguel = services.registrar_aluguel(form.cleaned_data, request.user)
        except services.RegraDeNegocio as erro:
            form.add_error('carro', str(erro))
        else:
            messages.success(request, f'Aluguel #{aluguel.pk} registrado com sucesso.')
            return redirect('dashboard')
    carro_selecionado = None
    if form['carro'].value():
        carro_selecionado = Carro.objects.filter(pk=form['carro'].value()).first()
        if carro_selecionado:
            carro_selecionado = _carro_para_tela(carro_selecionado)
    return render(request, 'core/novo_aluguel.html', {
        'form': form,
        'carro_selecionado': carro_selecionado,
        'tem_clientes': PerfilCliente.objects.exists(),
    })


def taxas_atraso(request):
    carros, _ = _carros_para_tela()
    carros = [carro for carro in carros if carro.diaria is not None]
    return render(request, 'core/taxas_atraso.html', {
        'faixas_atraso': FAIXAS_ATRASO,
        'carros': carros,
        'catalogo_calculadora': [
            {'slug': carro.slug, 'diaria': float(carro.diaria)}
            for carro in carros
        ],
        'parametros_calculadora': {
            'tolerancia_horas': float(TOLERANCIA_HORAS),
            'limite_faixa_hora': float(LIMITE_FAIXA_HORA),
            'percentual': float(PERCENTUAL_MULTA),
        },
    })


@login_required(login_url='/api-auth/login/')
def clientes(request):
    _exigir_funcionario(request)
    form = ClienteCadastroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        nome = form.cleaned_data['nome'].strip()
        partes = nome.split(maxsplit=1)
        with transaction.atomic():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                first_name=partes[0],
                last_name=partes[1] if len(partes) > 1 else '',
            )
            grupo, _ = Group.objects.get_or_create(name=GRUPO_CLIENTES)
            user.groups.add(grupo)
            PerfilCliente.objects.create(
                user=user,
                cnh=form.cleaned_data['cnh'],
                telefone=form.cleaned_data['telefone'],
                endereco=form.cleaned_data['endereco'],
            )
        messages.success(request, 'Cliente cadastrado com sucesso.')
        return redirect('clientes')

    busca = request.GET.get('q', '').strip()
    lista_clientes = PerfilCliente.objects.select_related('user').order_by(
        'user__first_name', 'user__last_name', 'user__username'
    )
    if busca:
        digitos = _somente_digitos(busca)
        consulta = (
            Q(user__first_name__icontains=busca)
            | Q(user__last_name__icontains=busca)
            | Q(user__username__icontains=busca)
        )
        if digitos:
            consulta |= Q(cnh__icontains=digitos)
        lista_clientes = lista_clientes.filter(consulta)
    clientes_tela = [
        SimpleNamespace(
            nome=perfil.user.get_full_name() or perfil.user.username,
            telefone=perfil.telefone,
            criado_em=perfil.user.date_joined,
        )
        for perfil in lista_clientes
    ]
    return render(request, 'core/clientes.html', {
        'form': form,
        'clientes': clientes_tela,
        'busca': busca,
    })
