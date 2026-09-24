"""Semelhança por conteúdo: gênero, elenco, direção, época.

Serve para duas coisas que a filtragem colaborativa não faz:

1. **Partida a frio.** Um título estreado ontem não foi visto por ninguém, e
   para a filtragem colaborativa ele simplesmente não existe — não há
   co-ocorrência nenhuma. Pelo conteúdo ele já se parece com o resto do
   catálogo desde antes de estrear.

2. **Explicação.** "Porque você assistiu *Cidade de Vidro*" é vago. "Porque
   você assistiu *Cidade de Vidro* — também é ficção científica, também com
   Otávio Braga" é uma frase que se pode conferir.

Os pesos abaixo são escolha, não descoberta. Gênero pesa mais que elenco porque
num catálogo pequeno quase todo mundo já trabalhou com quase todo mundo, e o
elenco sozinho acabaria ligando tudo a tudo.
"""

from __future__ import annotations

from dataclasses import dataclass

from .catalogo import Catalogo, Titulo
from .similaridade import jaccard

#: Quanto cada aspecto vale na semelhança final.
PESO_GENERO = 0.55
PESO_ELENCO = 0.25
PESO_DIRECAO = 0.12
PESO_EPOCA = 0.08

#: A partir de quantos anos de diferença duas obras deixam de ser da mesma época.
JANELA_DE_EPOCA = 10


@dataclass(frozen=True)
class Parecenca:
    """Quanto dois títulos se parecem, e por quê."""

    nota: float
    motivos: tuple[str, ...]


def proximidade_de_epoca(um: Titulo, outro: Titulo) -> float:
    """1 para o mesmo ano, 0 a partir de ``JANELA_DE_EPOCA`` anos de distância."""
    distancia = abs(um.ano - outro.ano)

    if distancia >= JANELA_DE_EPOCA:
        return 0.0

    return 1.0 - distancia / JANELA_DE_EPOCA


def parecenca(um: Titulo, outro: Titulo) -> Parecenca:
    """Compara dois títulos e diz o quanto — e por quê — se parecem."""
    if um.id == outro.id:
        # Um título é idêntico a si mesmo, e isso nunca é recomendação.
        return Parecenca(1.0, ("é o mesmo título",))

    generos_em_comum = um.generos & outro.generos
    elenco_em_comum = um.elenco & outro.elenco
    mesma_direcao = um.direcao == outro.direcao

    nota = (
        PESO_GENERO * jaccard(um.generos, outro.generos)
        + PESO_ELENCO * jaccard(um.elenco, outro.elenco)
        + PESO_DIRECAO * (1.0 if mesma_direcao else 0.0)
        + PESO_EPOCA * proximidade_de_epoca(um, outro)
    )

    motivos = []

    if generos_em_comum:
        motivos.append(_lista(sorted(generos_em_comum), "também é", "também são"))

    if elenco_em_comum:
        motivos.append("também com " + _e(sorted(elenco_em_comum)))

    if mesma_direcao:
        motivos.append(f"também dirigido por {um.direcao}")

    return Parecenca(nota, tuple(motivos))


def parecidos(catalogo: Catalogo, id_do_titulo: int, quantos: int = 10) -> list[tuple[int, Parecenca]]:
    """Os títulos mais parecidos com um dado, do mais para o menos."""
    origem = catalogo.get(id_do_titulo)

    if origem is None:
        return []

    notas = [
        (outro.id, parecenca(origem, outro))
        for outro in catalogo
        if outro.id != id_do_titulo
    ]

    # Desempate pelo id: sem ele, dois títulos igualmente parecidos trocariam
    # de lugar a cada execução, e a mesma pergunta daria respostas diferentes.
    notas.sort(key=lambda par: (-par[1].nota, par[0]))

    return [par for par in notas if par[1].nota > 0.0][:quantos]


def _e(nomes: list[str]) -> str:
    """"a", "a e b", "a, b e c"."""
    if len(nomes) == 1:
        return nomes[0]

    return f"{', '.join(nomes[:-1])} e {nomes[-1]}"


def _lista(itens: list[str], singular: str, plural: str) -> str:
    verbo = singular if len(itens) == 1 else plural

    return f"{verbo} {_e([_GENEROS.get(item, item) for item in itens])}"


#: Os apelidos de gênero, como aparecem na frase.
_GENEROS = {
    "acao": "ação",
    "animacao": "animação",
    "documentario": "documentário",
    "drama": "drama",
    "ficcao": "ficção científica",
    "romance": "romance",
    "suspense": "suspense",
}
