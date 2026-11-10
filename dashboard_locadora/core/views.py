import re
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from .forms import ClienteForm
from .catalogo import CARROS_DISPONIVEIS
from .models import (
    LIMITE_FAIXA_HORA,
    PERCENTUAL,
    TOLERANCIA_HORAS,
    Aluguel,
    Categoria,
    Cliente,
    FAIXAS_ATRASO,
)


def dashboard(request):
    categorias = list(Categoria.objects.all())
    filtro = request.GET.get("categoria", "")

    alugueis = Aluguel.objects.select_related("categoria", "cliente")
    if filtro:
        alugueis = alugueis.filter(categoria__nome=filtro)
    alugueis = list(alugueis)

    receita = sum((a.valor for a in alugueis), Decimal("0"))
    multas = sum((a.multa for a in alugueis), Decimal("0"))
    atrasados = sum(1 for a in alugueis if a.multa > 0)

    por_categoria = []
    for c in categorias:
        valor = sum((a.valor for a in alugueis if a.categoria_id == c.id), Decimal("0"))
        por_categoria.append({"nome": c.nome, "valor": valor})
    maximo = max((p["valor"] for p in por_categoria), default=Decimal("0")) or Decimal("1")
    for p in por_categoria:
        p["pct"] = int(p["valor"] / maximo * 100)

    contexto = {
        "alugueis": alugueis,
        "categorias": categorias,
        "filtro": filtro,
        "receita": receita,
        "multas": multas,
        "total": receita + multas,
        "qtd": len(alugueis),
        "atrasados": atrasados,
        "por_categoria": por_categoria,
        "diarias_json": {c.nome: float(c.diaria) for c in categorias},
        "faixas_atraso": FAIXAS_ATRASO,
    }
    return render(request, "core/dashboard.html", contexto)


def carros_disponiveis(request):
    return render(request, "core/carros.html", {"carros": CARROS_DISPONIVEIS})


def taxas_atraso(request):
    catalogo_calculadora = [
        {"slug": carro["slug"], "diaria": float(carro["diaria"])}
        for carro in CARROS_DISPONIVEIS
    ]
    return render(request, "core/taxas_atraso.html", {
        "faixas_atraso": FAIXAS_ATRASO,
        "carros": CARROS_DISPONIVEIS,
        "catalogo_calculadora": catalogo_calculadora,
        "parametros_calculadora": {
            "tolerancia_horas": float(TOLERANCIA_HORAS),
            "limite_faixa_hora": float(LIMITE_FAIXA_HORA),
            "percentual": float(PERCENTUAL),
        },
    })


@login_required(login_url="/api-auth/login/")
def clientes(request):
    form = ClienteForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cliente cadastrado com sucesso.")
        return redirect("clientes")

    busca = request.GET.get("q", "").strip()
    lista_clientes = Cliente.objects.all()
    if busca:
        digitos = re.sub(r"\D", "", busca)
        consulta = Q(nome__icontains=busca)
        if digitos:
            consulta |= Q(cpf__icontains=digitos)
        lista_clientes = lista_clientes.filter(consulta)

    return render(request, "core/clientes.html", {
        "form": form,
        "clientes": lista_clientes,
        "busca": busca,
    })
