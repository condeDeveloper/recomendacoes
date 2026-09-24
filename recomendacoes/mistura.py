"""A mistura: comportamento e conteúdo, com a explicação junto.

Nenhuma das duas metades funciona sozinha.

A **colaborativa** encontra semelhanças que ninguém programou — e é cega para
qualquer título que ninguém assistiu ainda. Num catálogo que recebe lançamentos
toda semana, isso é o pior lugar possível para ser cego.

A **de conteúdo** sabe do lançamento desde antes de ele estrear — e é incapaz
de descobrir que dois títulos sem nada em comum no papel agradam às mesmas
pessoas. Ela só repete o que já está escrito nos metadados.

Juntas, cada uma cobre o buraco da outra. O peso é uma escolha, e este arquivo
a expõe como parâmetro em vez de escondê-la numa constante mágica.

**Sobre a explicação.** A frase "porque você assistiu X" só aparece quando X
realmente responde pela recomendação. Se três títulos contribuíram mais ou
menos igual, dizer o nome de um deles é escolher um culpado ao acaso e
apresentá-lo como causa — e a pessoa que clica esperando mais do X recebe outra
coisa. Nesse caso o recomendador diz o que sabe: que combinou vários.
"""

from __future__ import annotations

from dataclasses import dataclass

from .catalogo import Catalogo
from .colaborativa import ModeloItemItem
from .conteudo import parecenca

#: Quanto o comportamento pesa contra o conteúdo, de 0 a 1.
PESO_COLABORATIVO = 0.7

#: A semente precisa responder por esta fração da nota para virar explicação.
DOMINIO_MINIMO = 0.5


@dataclass(frozen=True)
class Recomendacao:
    """Um título recomendado, com nota, origem e a frase pronta."""

    titulo: int
    nota: float
    semente: int | None
    explicacao: str
    colaborativa: float
    conteudo: float


class Recomendador:
    """Junta as duas metades para um catálogo e um histórico."""

    def __init__(
        self,
        catalogo: Catalogo,
        matriz: dict[int, dict[int, float]],
        peso_colaborativo: float = PESO_COLABORATIVO,
    ) -> None:
        if not 0.0 <= peso_colaborativo <= 1.0:
            raise ValueError(f"O peso vai de 0 a 1; veio {peso_colaborativo}.")

        self.catalogo = catalogo
        self.matriz = matriz
        self.peso_colaborativo = peso_colaborativo
        self.modelo = ModeloItemItem(matriz)

    def para(
        self,
        perfil: int,
        quantos: int = 6,
        idade_maxima: int | None = None,
    ) -> list[Recomendacao]:
        """O que recomendar a um perfil.

        ``idade_maxima`` corta o que a classificação indicativa não permite —
        é o perfil infantil. O corte acontece antes da ordenação, para que
        ``quantos`` continue valendo.
        """
        permitidos = {
            titulo.id
            for titulo in self.catalogo
            if idade_maxima is None or titulo.idade_minima <= idade_maxima
        }

        vistos = self.matriz.get(perfil, {})
        notas: dict[int, float] = {}
        sementes: dict[int, tuple[int | None, float]] = {}
        parciais: dict[int, tuple[float, float]] = {}

        colaborativas = {
            sugestao.titulo: sugestao
            for sugestao in self.modelo.recomendar(perfil, quantos=len(self.catalogo), permitidos=permitidos)
        }

        maior_colaborativa = max((s.nota for s in colaborativas.values()), default=0.0)

        candidatos = [c for c in sorted(permitidos) if c not in vistos]

        # As duas metades saem em escalas incompatíveis: a colaborativa soma
        # sobre tudo que a pessoa viu, então cresce com o tamanho do histórico;
        # a de conteúdo vai de 0 a 2, porque o interesse pode passar de 1 em
        # quem reassistiu. Somar as duas cruas faria `peso_colaborativo` pesar
        # qualquer coisa menos o que o nome diz. Cada uma é dividida pelo seu
        # próprio máximo antes de se encontrarem.
        de_conteudo = {c: self._conteudo(c, vistos) for c in candidatos}
        maior_conteudo = max((nota for nota, _ in de_conteudo.values()), default=0.0)

        for candidato in candidatos:
            sugestao = colaborativas.get(candidato)

            nota_colaborativa = (
                sugestao.nota / maior_colaborativa if sugestao and maior_colaborativa > 0 else 0.0
            )

            bruta_de_conteudo, semente_de_conteudo = de_conteudo[candidato]
            nota_conteudo = bruta_de_conteudo / maior_conteudo if maior_conteudo > 0 else 0.0

            nota = (
                self.peso_colaborativo * nota_colaborativa
                + (1.0 - self.peso_colaborativo) * nota_conteudo
            )

            if nota <= 0.0:
                continue

            notas[candidato] = nota
            parciais[candidato] = (nota_colaborativa, nota_conteudo)
            sementes[candidato] = self._semente(sugestao, semente_de_conteudo, bruta_de_conteudo)

        ordenados = sorted(notas.items(), key=lambda par: (-par[1], par[0]))[:quantos]

        return [
            Recomendacao(
                titulo=candidato,
                nota=nota,
                semente=sementes[candidato][0],
                explicacao=self.explicar(candidato, *sementes[candidato]),
                colaborativa=parciais[candidato][0],
                conteudo=parciais[candidato][1],
            )
            for candidato, nota in ordenados
        ]

    def _conteudo(self, candidato: int, vistos: dict[int, float]) -> tuple[float, int | None]:
        """A melhor semelhança de conteúdo entre o candidato e o que já se viu."""
        alvo = self.catalogo.get(candidato)

        if alvo is None or not vistos:
            return 0.0, None

        melhor = 0.0
        melhor_semente = None

        for visto, interesse in sorted(vistos.items()):
            origem = self.catalogo.get(visto)

            if origem is None:
                continue

            nota = parecenca(origem, alvo).nota * interesse

            if nota > melhor:
                melhor = nota
                melhor_semente = visto

        return melhor, melhor_semente

    def _semente(self, sugestao, semente_de_conteudo, nota_conteudo) -> tuple[int | None, float]:
        """Qual título explica a recomendação, e com que força.

        A força é a fração da nota pela qual a semente responde. É ela que
        decide se cabe dizer "porque você assistiu X" ou não.
        """
        if sugestao and sugestao.contribuicoes:
            total = sum(c.peso for c in sugestao.contribuicoes)
            maior = sugestao.contribuicoes[0]

            if total > 0:
                return maior.semente, maior.peso / total

        if semente_de_conteudo is not None and nota_conteudo > 0:
            return semente_de_conteudo, 1.0

        return None, 0.0

    def explicar(self, candidato: int, semente: int | None, dominio: float) -> str:
        """A frase que vai na tela."""
        if semente is None:
            return "Em alta no catálogo"

        if dominio < DOMINIO_MINIMO:
            # Vários títulos empurraram parecido. Apontar um deles seria
            # escolher um culpado ao acaso e chamá-lo de causa.
            return "Porque você assiste títulos parecidos"

        origem = self.catalogo.get(semente)
        alvo = self.catalogo.get(candidato)

        frase = f"Porque você assistiu {self.catalogo.nome(semente)}"

        if origem is None or alvo is None:
            return frase

        motivos = parecenca(origem, alvo).motivos

        return f"{frase} — {motivos[0]}" if motivos else frase
