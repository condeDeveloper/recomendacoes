"""O catálogo do CondePlay, como este recomendador o enxerga.

Os títulos, as sinopses e os nomes são **inventados para este projeto** e são
os mesmos que a API em C# semeia. Um recomendador precisa de dados para ter
alguma graça, e um catálogo de exemplo com obras reais traria sinopse e arte de
terceiros para dentro do repositório sem necessidade nenhuma.

Para o recomendador, um título é bem pouca coisa: um id, gêneros, elenco,
direção e ano. É o suficiente para dizer que *Cidade de Vidro* parece com
*Sinal Fraco* — as duas são ficção científica — e que *A Ilha dos Relógios
Parados* não parece com nenhuma delas.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Titulo:
    """Um filme ou uma série, do ponto de vista de quem recomenda."""

    id: int
    nome: str
    tipo: str
    ano: int
    generos: frozenset[str]
    elenco: frozenset[str]
    direcao: str
    idade_minima: int = 0

    @property
    def pessoas(self) -> frozenset[str]:
        """Elenco e direção juntos.

        Quem dirigiu conta tanto quanto quem atuou para explicar por que duas
        obras se parecem — às vezes conta mais.
        """
        return self.elenco | {self.direcao}


@dataclass
class Catalogo:
    """Os títulos, indexados por id."""

    titulos: dict[int, Titulo] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.titulos, dict):
            self.titulos = {titulo.id: titulo for titulo in self.titulos}

    def __len__(self) -> int:
        return len(self.titulos)

    def __iter__(self):
        return iter(self.titulos.values())

    def __contains__(self, id_do_titulo: object) -> bool:
        return id_do_titulo in self.titulos

    def __getitem__(self, id_do_titulo: int) -> Titulo:
        return self.titulos[id_do_titulo]

    def get(self, id_do_titulo: int) -> Titulo | None:
        return self.titulos.get(id_do_titulo)

    def ids(self) -> list[int]:
        return sorted(self.titulos)

    def nome(self, id_do_titulo: int) -> str:
        """O nome, ou uma marca clara de que o id não existe.

        Devolver ``"?"`` silenciosamente faria uma explicação sair com um nome
        vazio e ninguém descobriria; devolver o id entre colchetes deixa o
        problema visível na própria tela.
        """
        titulo = self.titulos.get(id_do_titulo)

        return titulo.nome if titulo else f"[título {id_do_titulo}]"


#: O catálogo de demonstração, igual ao que a API semeia.
DEMONSTRACAO = Catalogo(
    {
        titulo.id: titulo
        for titulo in [
            Titulo(
                id=1,
                nome="Cidade de Vidro",
                tipo="filme",
                ano=2024,
                generos=frozenset({"ficcao"}),
                elenco=frozenset({"Solange Vieira", "Otávio Braga"}),
                direcao="Rita Amorim",
                idade_minima=12,
            ),
            Titulo(
                id=2,
                nome="O Último Trem para Olinda",
                tipo="filme",
                ano=2023,
                generos=frozenset({"drama"}),
                elenco=frozenset({"Benedito Rangel", "Solange Vieira"}),
                direcao="Rita Amorim",
                idade_minima=14,
            ),
            Titulo(
                id=3,
                nome="Enquanto a Chuva Não Passa",
                tipo="filme",
                ano=2022,
                generos=frozenset({"romance"}),
                elenco=frozenset({"Marina Teles", "Otávio Braga"}),
                direcao="Caio Sampaio",
                idade_minima=0,
            ),
            Titulo(
                id=4,
                nome="Caçadores de Estática",
                tipo="filme",
                ano=2025,
                generos=frozenset({"acao"}),
                elenco=frozenset({"Otávio Braga", "Ivone Castelo"}),
                direcao="Caio Sampaio",
                idade_minima=16,
            ),
            Titulo(
                id=5,
                nome="A Ilha dos Relógios Parados",
                tipo="filme",
                ano=2021,
                generos=frozenset({"animacao"}),
                elenco=frozenset({"Marina Teles"}),
                direcao="Lúcia Bandeira",
                idade_minima=0,
            ),
            Titulo(
                id=6,
                nome="Dossiê Meia-Noite",
                tipo="filme",
                ano=2020,
                generos=frozenset({"suspense"}),
                elenco=frozenset({"Benedito Rangel", "Ivone Castelo"}),
                direcao="Rita Amorim",
                idade_minima=18,
            ),
            Titulo(
                id=7,
                nome="Litoral",
                tipo="serie",
                ano=2023,
                generos=frozenset({"drama"}),
                elenco=frozenset({"Solange Vieira"}),
                direcao="Lúcia Bandeira",
                idade_minima=14,
            ),
            Titulo(
                id=8,
                nome="Sinal Fraco",
                tipo="serie",
                ano=2025,
                generos=frozenset({"suspense", "ficcao"}),
                elenco=frozenset({"Ivone Castelo", "Marina Teles"}),
                direcao="Caio Sampaio",
                idade_minima=16,
            ),
        ]
    }
)
