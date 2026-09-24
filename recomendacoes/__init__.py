"""Recomendações do CondePlay: "porque você assistiu X".

Filtragem colaborativa item-item, semelhança por conteúdo e a mistura das
duas — em Python puro, sem uma dependência.
"""

from .catalogo import Catalogo, Titulo
from .colaborativa import Contribuicao, ModeloItemItem, Sugestao, coocorrencia_crua
from .conteudo import Parecenca, parecenca, parecidos
from .eventos import (
    Evento,
    interesse_do_evento,
    matriz_de_interesse,
    popularidade,
    quem_viu,
)
from .mistura import Recomendacao, Recomendador
from .similaridade import cosseno, cosseno_binario, coocorrencia, jaccard, pearson

__all__ = [
    "Catalogo",
    "Contribuicao",
    "Evento",
    "ModeloItemItem",
    "Parecenca",
    "Recomendacao",
    "Recomendador",
    "Sugestao",
    "Titulo",
    "coocorrencia",
    "coocorrencia_crua",
    "cosseno",
    "cosseno_binario",
    "interesse_do_evento",
    "jaccard",
    "matriz_de_interesse",
    "parecenca",
    "parecidos",
    "pearson",
    "popularidade",
    "quem_viu",
]
