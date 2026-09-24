"""As medidas de semelhança.

Três medidas, e a diferença entre elas é a razão de este arquivo existir.

**Co-ocorrência crua** conta quantas pessoas viram os dois títulos. É a medida
intuitiva, e é a errada: o título mais assistido do catálogo co-ocorre com tudo,
então ele vira a recomendação de todo mundo. O recomendador fica dizendo
"porque você assistiu X, veja o campeão de audiência" — para qualquer X.

**Cosseno** divide a co-ocorrência pela raiz do produto das popularidades.
Essa divisão é toda a diferença: perguntar "que fração de quem viu A também viu
B, e vice-versa" em vez de "quantos".

**Jaccard** divide pela união. Pune a popularidade ainda mais que o cosseno, e
por isso tende a trazer títulos de nicho.

Nenhuma é "a certa". A escolhida aqui é o cosseno, e o teste
``testes/test_similaridade.py`` mostra numericamente o que a crua faria.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def coocorrencia(a: Iterable, b: Iterable) -> int:
    """Quantos elementos os dois conjuntos têm em comum.

    A medida ingênua. Está aqui para ser comparada, não para ser usada.
    """
    return len(set(a) & set(b))


def cosseno_binario(a: Iterable, b: Iterable) -> float:
    """Cosseno entre dois conjuntos vistos como vetores de zeros e uns.

    Para vetores binários o cosseno tem forma fechada::

        |A ∩ B| / sqrt(|A| · |B|)

    que é a co-ocorrência normalizada pela popularidade dos dois lados.
    """
    primeiro, segundo = set(a), set(b)

    if not primeiro or not segundo:
        # Um título que ninguém viu não se parece com nada — e não é erro:
        # é a partida a frio, que a semelhança por conteúdo resolve.
        return 0.0

    return len(primeiro & segundo) / math.sqrt(len(primeiro) * len(segundo))


def jaccard(a: Iterable, b: Iterable) -> float:
    """Interseção sobre união."""
    primeiro, segundo = set(a), set(b)
    uniao = primeiro | segundo

    if not uniao:
        return 0.0

    return len(primeiro & segundo) / len(uniao)


def cosseno(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosseno entre dois vetores de números.

    Usado quando o interesse não é sim-ou-não, mas quanto da obra a pessoa
    assistiu.
    """
    if len(a) != len(b):
        raise ValueError(f"Vetores de tamanhos diferentes: {len(a)} e {len(b)}.")

    produto = math.sumprod(a, b)
    norma_a = math.sqrt(math.sumprod(a, a))
    norma_b = math.sqrt(math.sumprod(b, b))

    if norma_a == 0.0 or norma_b == 0.0:
        return 0.0

    return produto / (norma_a * norma_b)


def pearson(a: Sequence[float], b: Sequence[float]) -> float:
    """Correlação de Pearson: o cosseno depois de tirar a média.

    A diferença importa em avaliações por estrelas. Quem dá 4 e 5 para tudo e
    quem dá 1 e 2 para tudo têm cosseno alto — os dois vetores apontam para o
    mesmo canto — mas gostos opostos. Tirar a média de cada um revela isso.

    Não é usada na recomendação principal, que trabalha com quanto se assistiu
    e não com notas. Está aqui porque é o contraste que explica o cosseno.
    """
    if len(a) != len(b):
        raise ValueError(f"Vetores de tamanhos diferentes: {len(a)} e {len(b)}.")

    if len(a) < 2:
        raise ValueError("Correlação precisa de ao menos dois pontos.")

    media_a = sum(a) / len(a)
    media_b = sum(b) / len(b)

    centrado_a = [valor - media_a for valor in a]
    centrado_b = [valor - media_b for valor in b]

    return cosseno(centrado_a, centrado_b)
