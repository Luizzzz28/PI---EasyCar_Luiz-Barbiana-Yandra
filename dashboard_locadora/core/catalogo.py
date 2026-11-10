import json
from decimal import Decimal
from pathlib import Path

from .models import LIMITE_FAIXA_HORA, PERCENTUAL, TOLERANCIA_HORAS


_FOTOS_DIR = Path(__file__).resolve().parent / "static" / "core" / "img" / "cars"
_CREDITOS_FOTOS = {
    item["slug"]: item
    for item in json.loads(
        (_FOTOS_DIR / "catalog-credits.json").read_text(encoding="utf-8-sig")
    )
}


def _autor_resumido(autor):
    if "Contact e-mail:" in autor:
        return autor.split(". Contact e-mail:", 1)[0].removeprefix(
            "This picture has been taken by "
        )
    return autor


_VEICULOS = [
    ("toyota-corolla", "Toyota Corolla", "Sedã", "249.00"),
    ("honda-civic", "Honda Civic", "Sedã", "229.00"),
    ("hyundai-hb20", "Hyundai HB20", "Hatch", "129.00"),
    ("chevrolet-onix", "Chevrolet Onix", "Hatch", "119.00"),
    ("volkswagen-polo", "Volkswagen Polo", "Hatch", "139.00"),
    ("volkswagen-t-cross", "Volkswagen T-Cross", "SUV compacto", "189.00"),
    ("hyundai-creta", "Hyundai Creta", "SUV compacto", "179.00"),
    ("jeep-compass", "Jeep Compass", "SUV médio", "219.00"),
    ("jeep-renegade", "Jeep Renegade", "SUV compacto", "189.00"),
    ("toyota-corolla-cross", "Toyota Corolla Cross", "SUV médio", "239.00"),
    ("nissan-kicks", "Nissan Kicks", "SUV compacto", "169.00"),
    ("chevrolet-tracker", "Chevrolet Tracker", "SUV compacto", "179.00"),
    ("hyundai-tucson", "Hyundai Tucson", "SUV médio", "199.00"),
    ("honda-hr-v", "Honda HR-V", "SUV compacto", "199.00"),
    ("toyota-rav4", "Toyota RAV4", "SUV híbrido", "329.00"),
    ("bmw-320i", "BMW 320i", "Sedã premium", "399.00"),
    ("mercedes-c-class", "Mercedes-Benz Classe C", "Sedã premium", "429.00"),
    ("audi-a3", "Audi A3", "Sedã premium", "349.00"),
    ("porsche-911", "Porsche 911", "Esportivo", "990.00"),
    ("ford-mustang", "Ford Mustang", "Esportivo", "890.00"),
]

CARROS_DISPONIVEIS = [
    {
        "slug": slug,
        "nome": nome,
        "categoria": categoria,
        "diaria": Decimal(diaria),
        "taxa_hora": Decimal(diaria) * PERCENTUAL,
        "multa_dia": Decimal(diaria) * (1 + PERCENTUAL),
        "imagem": f"core/img/cars/{slug}.jpg",
        "credito": {
            "description_url": _CREDITOS_FOTOS[slug]["description_url"],
            "artist": _autor_resumido(_CREDITOS_FOTOS[slug]["artist"]),
            "license": _CREDITOS_FOTOS[slug]["license"],
            "license_url": _CREDITOS_FOTOS[slug]["license_url"],
        },
        "alt_fotografo": _autor_resumido(_CREDITOS_FOTOS[slug]["artist"]),
    }
    for slug, nome, categoria, diaria in _VEICULOS
]
