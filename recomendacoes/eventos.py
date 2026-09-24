"""Do que aconteceu na tela para o que a pessoa gosta.

O sinal que chega é bruto: "o perfil 3 assistiu 812 segundos do título 7, que
tem 2520". Transformar isso em interesse é onde moram as decisões que ninguém
vê e todo mundo sente.

**Um segundo não vale por um segundo.** Assistir 40 minutos de um filme de 2
horas é diferente de assistir 40 minutos de um episódio de 42. A fração conta,
não o total.

**Abandonar cedo é sinal negativo, e o mais honesto que existe.** Quem parou em
3% não gostou — mas quem parou em 3% também pode ter clicado por engano. Abaixo
de um piso, o evento não vale como interesse nenhum, nem a favor nem contra.

**Terminar não é o teto.** Quem reassistiu três vezes gosta mais do que quem
viu uma vez até o fim, e o interesse precisa poder passar de 1.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

#: Abaixo desta fração, o evento não conta: é clique, não interesse.
FRACAO_MINIMA = 0.05

#: Acima desta fração, considera-se assistido por inteiro.
FRACAO_DE_CONCLUSAO = 0.92

#: O interesse não passa disto, por mais que se reassista.
INTERESSE_MAXIMO = 2.0


@dataclass(frozen=True)
class Evento:
    """Uma sessão de reprodução."""

    perfil: int
    titulo: int
    segundos_assistidos: float
    segundos_totais: float

    @property
    def fracao(self) -> float:
        """Quanto da obra foi assistido, de 0 a 1 (ou mais, se reassistiu)."""
        if self.segundos_totais <= 0:
            # Sem duração conhecida não há fração nenhuma a calcular. Chutar
            # 1.0 aqui inventaria interesse que não foi observado.
            return 0.0

        return self.segundos_assistidos / self.segundos_totais


def interesse_do_evento(evento: Evento) -> float:
    """O interesse que um evento isolado demonstra, de 0 a ``INTERESSE_MAXIMO``."""
    fracao = evento.fracao

    if fracao < FRACAO_MINIMA:
        return 0.0

    if fracao >= FRACAO_DE_CONCLUSAO:
        # Terminou. Reassistir aumenta, mas com teto: quem viu dez vezes não
        # gosta dez vezes mais do que quem viu duas, e sem teto um maratonista
        # sozinho dominaria a semelhança de um título inteiro.
        return min(INTERESSE_MAXIMO, max(1.0, fracao))

    return fracao


def matriz_de_interesse(eventos) -> dict[int, dict[int, float]]:
    """Agrega os eventos num mapa ``perfil -> título -> interesse``.

    Sessões do mesmo par somam: quem assistiu metade hoje e metade amanhã
    assistiu o filme inteiro.
    """
    somado: dict[int, dict[int, float]] = defaultdict(lambda: defaultdict(float))

    for evento in eventos:
        somado[evento.perfil][evento.titulo] += interesse_do_evento(evento)

    matriz = {}

    for perfil, titulos in somado.items():
        interesses = {
            titulo: min(INTERESSE_MAXIMO, valor)
            for titulo, valor in titulos.items()
            if valor > 0.0
        }

        # Um perfil cujos eventos ficaram todos abaixo do piso não tem
        # histórico nenhum, e não pode aparecer como chave: quem perguntar
        # `perfil in matriz` receberia "sim" e concluiria que há o que usar.
        if interesses:
            matriz[perfil] = interesses

    return matriz


def quem_viu(matriz: dict[int, dict[int, float]]) -> dict[int, set[int]]:
    """Inverte a matriz: para cada título, os perfis que demonstraram interesse."""
    invertido: dict[int, set[int]] = defaultdict(set)

    for perfil, titulos in matriz.items():
        for titulo in titulos:
            invertido[titulo].add(perfil)

    return dict(invertido)


def popularidade(matriz: dict[int, dict[int, float]]) -> dict[int, int]:
    """Quantos perfis distintos demonstraram interesse em cada título."""
    return {titulo: len(perfis) for titulo, perfis in quem_viu(matriz).items()}
