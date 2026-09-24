"""O histórico de demonstração.

Eventos de reprodução inventados para o catálogo de demonstração, montados
para que os testes tenham o que morder. Não são aleatórios: cada perfil tem um
gosto declarado no comentário, e o recomendador tem de reencontrá-lo sem que
ninguém lhe conte.

Um perfil é proposital: o **10**, que só assistiu um lançamento que mais
ninguém viu. Ele é a partida a frio, e existe para que o teste possa provar que
a colaborativa sozinha não o atende.
"""

from __future__ import annotations

from .eventos import Evento

#: Durações em segundos, por título — as mesmas do catálogo em C#.
DURACOES = {
    1: 118 * 60,
    2: 96 * 60,
    3: 84 * 60,
    4: 131 * 60,
    5: 77 * 60,
    6: 104 * 60,
    7: 42 * 60,
    8: 45 * 60,
}


def _viu(perfil: int, titulo: int, fracao: float) -> Evento:
    total = DURACOES[titulo]

    return Evento(perfil=perfil, titulo=titulo, segundos_assistidos=total * fracao, segundos_totais=total)


#: Quem viu o quê. A coluna da direita é a fração assistida.
#:
#: O título 3, *Enquanto a Chuva Não Passa*, é livre e curto, e quase todo
#: mundo viu — é o campeão de audiência. Ele está aqui para que o viés de
#: popularidade possa ser medido, e não apenas descrito.
DEMONSTRACAO = [
    # Perfil 1 — gosta de gênero: ficção e suspense, sempre até o fim.
    _viu(1, 1, 1.0),
    _viu(1, 6, 1.0),
    _viu(1, 8, 0.97),
    _viu(1, 3, 1.0),
    # Perfil 2 — o mesmo gosto, com um filme a menos. É quem dá à
    # colaborativa o que sugerir ao perfil 1.
    _viu(2, 1, 0.95),
    _viu(2, 8, 1.0),
    _viu(2, 4, 0.99),
    _viu(2, 3, 1.0),
    # Perfil 3 — drama e romance, e largou a ficção nos primeiros minutos.
    _viu(3, 2, 1.0),
    _viu(3, 3, 0.98),
    _viu(3, 7, 1.0),
    _viu(3, 1, 0.03),
    # Perfil 4 — o mesmo gosto do 3.
    _viu(4, 2, 0.96),
    _viu(4, 7, 1.0),
    _viu(4, 3, 1.0),
    # Perfil 5 — só animação, e é o perfil infantil.
    _viu(5, 5, 1.0),
    _viu(5, 3, 0.6),
    # Perfil 6 — assiste de tudo. É o que faria a co-ocorrência crua ligar
    # títulos que não têm nada a ver um com o outro.
    _viu(6, 1, 1.0),
    _viu(6, 2, 1.0),
    _viu(6, 3, 1.0),
    _viu(6, 4, 1.0),
    _viu(6, 5, 1.0),
    _viu(6, 6, 1.0),
    _viu(6, 7, 1.0),
    # Perfis 7 a 9 — viram só o campeão de audiência e mais um.
    _viu(7, 3, 1.0),
    _viu(7, 2, 1.0),
    _viu(8, 3, 1.0),
    _viu(8, 7, 1.0),
    _viu(9, 3, 1.0),
    _viu(9, 5, 1.0),
    # Perfil 10 — só viu uma série que mais ninguém viu. A partida a frio.
    _viu(10, 8, 1.0),
]
