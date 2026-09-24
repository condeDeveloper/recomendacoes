"""Filtragem colaborativa item-item.

A ideia em uma linha: dois títulos se parecem quando as mesmas pessoas
assistiram os dois. Ninguém precisou dizer que *Cidade de Vidro* e *Sinal
Fraco* são ficção científica — o comportamento disse.

Por que item-item e não pessoa-pessoa:

- **A semelhança entre títulos muda devagar.** Dá para calcular de madrugada e
  usar o dia inteiro. A semelhança entre pessoas muda a cada sessão.
- **São muito menos títulos do que pessoas.** A matriz item-item de um catálogo
  de mil títulos cabe na memória; a de um milhão de assinantes, não.
- **A explicação sai de graça.** "Porque você assistiu X" é exatamente o que a
  conta item-item calcula: cada recomendação vem de um título que a pessoa viu.

A armadilha está documentada em ``similaridade.py`` e demonstrada com números
no teste ``test_colaborativa.py``: sem dividir pela popularidade, o campeão de
audiência vira a recomendação de todo mundo.
"""

from __future__ import annotations

from dataclasses import dataclass

from .eventos import quem_viu
from .similaridade import cosseno_binario


@dataclass(frozen=True)
class Contribuicao:
    """O quanto um título que a pessoa viu empurrou uma recomendação."""

    semente: int
    peso: float


@dataclass(frozen=True)
class Sugestao:
    """Um título sugerido, com de onde ele veio."""

    titulo: int
    nota: float
    contribuicoes: tuple[Contribuicao, ...]

    @property
    def principal(self) -> int | None:
        """O título que mais contribuiu — o "porque você assistiu"."""
        return self.contribuicoes[0].semente if self.contribuicoes else None


class ModeloItemItem:
    """A matriz de semelhança entre títulos, calculada uma vez."""

    def __init__(self, matriz: dict[int, dict[int, float]]) -> None:
        self.matriz = matriz
        self.espectadores = quem_viu(matriz)
        self._semelhancas: dict[int, dict[int, float]] = {}

        self._calcular()

    def _calcular(self) -> None:
        ids = sorted(self.espectadores)

        for i, um in enumerate(ids):
            for outro in ids[i + 1 :]:
                nota = cosseno_binario(self.espectadores[um], self.espectadores[outro])

                if nota <= 0.0:
                    continue

                self._semelhancas.setdefault(um, {})[outro] = nota
                self._semelhancas.setdefault(outro, {})[um] = nota

    def semelhanca(self, um: int, outro: int) -> float:
        """Quanto dois títulos se parecem, pelo comportamento."""
        if um == outro:
            return 1.0

        return self._semelhancas.get(um, {}).get(outro, 0.0)

    def parecidos_com(self, id_do_titulo: int, quantos: int = 10) -> list[tuple[int, float]]:
        """Os títulos mais parecidos com um dado, pelo comportamento."""
        vizinhos = self._semelhancas.get(id_do_titulo, {})

        return sorted(vizinhos.items(), key=lambda par: (-par[1], par[0]))[:quantos]

    def recomendar(
        self,
        perfil: int,
        quantos: int = 10,
        permitidos: set[int] | None = None,
    ) -> list[Sugestao]:
        """O que sugerir a um perfil, e de onde cada sugestão veio.

        ``permitidos`` restringe o que pode sair — é por onde passa o controle
        parental, por exemplo. Filtrar aqui e não depois importa: filtrar no
        fim devolveria menos resultados do que os ``quantos`` pedidos sempre
        que algo fosse cortado.
        """
        vistos = self.matriz.get(perfil, {})

        if not vistos:
            # Perfil novo: não há histórico de onde tirar nada. Devolver lista
            # vazia é honesto — quem chama decide o que mostrar no lugar.
            return []

        notas: dict[int, float] = {}
        origens: dict[int, list[Contribuicao]] = {}

        for semente, interesse in vistos.items():
            for candidato, semelhanca in self._semelhancas.get(semente, {}).items():
                if candidato in vistos:
                    # Não se recomenda o que a pessoa já assistiu. Parece
                    # óbvio, e é o erro mais comum de recomendador caseiro.
                    continue

                if permitidos is not None and candidato not in permitidos:
                    continue

                peso = semelhanca * interesse

                notas[candidato] = notas.get(candidato, 0.0) + peso
                origens.setdefault(candidato, []).append(Contribuicao(semente, peso))

        sugestoes = [
            Sugestao(
                titulo=candidato,
                nota=nota,
                contribuicoes=tuple(
                    sorted(origens[candidato], key=lambda c: (-c.peso, c.semente))
                ),
            )
            for candidato, nota in notas.items()
        ]

        sugestoes.sort(key=lambda s: (-s.nota, s.titulo))

        return sugestoes[:quantos]


def coocorrencia_crua(matriz: dict[int, dict[int, float]]) -> dict[int, dict[int, int]]:
    """A medida ingênua, para comparação.

    Existe só para o teste poder mostrar, com números do mesmo conjunto de
    dados, o que acontece quando não se normaliza pela popularidade.
    """
    espectadores = quem_viu(matriz)
    contagem: dict[int, dict[int, int]] = {}

    ids = sorted(espectadores)

    for i, um in enumerate(ids):
        for outro in ids[i + 1 :]:
            juntos = len(espectadores[um] & espectadores[outro])

            if juntos == 0:
                continue

            contagem.setdefault(um, {})[outro] = juntos
            contagem.setdefault(outro, {})[um] = juntos

    return contagem
