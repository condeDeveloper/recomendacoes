"""A linha de comando.

    python -m recomendacoes para 1            o que recomendar a um perfil
    python -m recomendacoes parecidos 1       o que se parece com um título
    python -m recomendacoes matriz            a semelhança entre todos
    python -m recomendacoes vies              a demonstração do viés de popularidade
    python -m recomendacoes catalogo          o que existe
"""

from __future__ import annotations

import argparse
import sys

from .catalogo import DEMONSTRACAO as CATALOGO
from .colaborativa import ModeloItemItem, coocorrencia_crua
from .conteudo import parecidos
from .eventos import matriz_de_interesse, popularidade
from .historico import DEMONSTRACAO as HISTORICO
from .mistura import Recomendador


def _recomendador(peso: float) -> Recomendador:
    return Recomendador(CATALOGO, matriz_de_interesse(HISTORICO), peso_colaborativo=peso)


def comando_para(argumentos) -> int:
    recomendador = _recomendador(argumentos.peso)
    sugestoes = recomendador.para(argumentos.perfil, quantos=argumentos.quantos, idade_maxima=argumentos.idade)

    if not sugestoes:
        print(f"Nada a recomendar ao perfil {argumentos.perfil}: sem histórico.")

        return 0

    print(f"Para o perfil {argumentos.perfil}:\n")

    for sugestao in sugestoes:
        print(f"  {CATALOGO.nome(sugestao.titulo)}")
        print(f"    {sugestao.explicacao}")
        print(
            f"    nota {sugestao.nota:.3f}"
            f"  (comportamento {sugestao.colaborativa:.2f}, conteúdo {sugestao.conteudo:.2f})"
        )
        print()

    return 0


def comando_parecidos(argumentos) -> int:
    if argumentos.titulo not in CATALOGO:
        print(f"Não há título {argumentos.titulo} no catálogo.", file=sys.stderr)

        return 1

    modelo = ModeloItemItem(matriz_de_interesse(HISTORICO))

    print(f"Parecidos com {CATALOGO.nome(argumentos.titulo)}:\n")
    print("  pelo comportamento:")

    vizinhos = modelo.parecidos_com(argumentos.titulo, quantos=argumentos.quantos)

    if vizinhos:
        for outro, nota in vizinhos:
            print(f"    {nota:.3f}  {CATALOGO.nome(outro)}")
    else:
        print("    (ninguém mais assistiu junto — é a partida a frio)")

    print("\n  pelo conteúdo:")

    for outro, parecenca in parecidos(CATALOGO, argumentos.titulo, quantos=argumentos.quantos):
        motivos = f"  ({'; '.join(parecenca.motivos)})" if parecenca.motivos else ""

        print(f"    {parecenca.nota:.3f}  {CATALOGO.nome(outro)}{motivos}")

    return 0


def comando_matriz(_argumentos) -> int:
    modelo = ModeloItemItem(matriz_de_interesse(HISTORICO))
    ids = CATALOGO.ids()

    print("Semelhança entre títulos, pelo comportamento:\n")
    print("       " + "  ".join(f"{i:>5}" for i in ids))

    for um in ids:
        celulas = "  ".join(
            "    ·" if um == outro else f"{modelo.semelhanca(um, outro):5.2f}" for outro in ids
        )

        print(f"  {um:>3}  {celulas}   {CATALOGO.nome(um)}")

    return 0


def comando_vies(_argumentos) -> int:
    matriz = matriz_de_interesse(HISTORICO)
    modelo = ModeloItemItem(matriz)
    cruas = coocorrencia_crua(matriz)
    quantos = popularidade(matriz)

    print("O viés de popularidade, no mesmo conjunto de dados.\n")
    print("Para cada título, o mais parecido segundo cada medida:\n")

    campeao = max(quantos, key=lambda t: (quantos[t], -t))

    print(f"  O mais assistido é {CATALOGO.nome(campeao)}, com {quantos[campeao]} perfis.\n")

    cabecalho = f"  {'título':<30} {'co-ocorrência crua':<30} {'cosseno':<30}"

    print(cabecalho)
    print("  " + "-" * (len(cabecalho) - 2))

    vezes_campeao_cru = 0
    vezes_campeao_cosseno = 0

    for id_do_titulo in CATALOGO.ids():
        vizinhos_crus = cruas.get(id_do_titulo, {})

        if not vizinhos_crus:
            continue

        melhor_cru = max(sorted(vizinhos_crus), key=lambda outro: vizinhos_crus[outro])
        melhor_cosseno = modelo.parecidos_com(id_do_titulo, quantos=1)

        if melhor_cru == campeao:
            vezes_campeao_cru += 1

        if melhor_cosseno and melhor_cosseno[0][0] == campeao:
            vezes_campeao_cosseno += 1

        cosseno_nome = CATALOGO.nome(melhor_cosseno[0][0]) if melhor_cosseno else "—"

        print(f"  {CATALOGO.nome(id_do_titulo):<30} {CATALOGO.nome(melhor_cru):<30} {cosseno_nome:<30}")

    print(
        f"\n  A crua aponta para o campeão {vezes_campeao_cru} vezes;"
        f" o cosseno, {vezes_campeao_cosseno}."
    )

    return 0


def comando_catalogo(_argumentos) -> int:
    for titulo in CATALOGO:
        generos = ", ".join(sorted(titulo.generos))

        print(f"  {titulo.id:>2}  {titulo.nome:<30} {titulo.ano}  {generos:<18} {titulo.idade_minima:>2}+")

    return 0


def principal(argumentos=None) -> int:
    analisador = argparse.ArgumentParser(
        prog="recomendacoes",
        description="Recomendações do CondePlay, sem uma dependência.",
    )

    subcomandos = analisador.add_subparsers(dest="comando", required=True)

    para = subcomandos.add_parser("para", help="o que recomendar a um perfil")
    para.add_argument("perfil", type=int)
    para.add_argument("--quantos", type=int, default=5)
    para.add_argument("--peso", type=float, default=0.7, help="peso do comportamento, de 0 a 1")
    para.add_argument("--idade", type=int, default=None, help="classificação máxima permitida")
    para.set_defaults(funcao=comando_para)

    parecidos_ = subcomandos.add_parser("parecidos", help="o que se parece com um título")
    parecidos_.add_argument("titulo", type=int)
    parecidos_.add_argument("--quantos", type=int, default=3)
    parecidos_.set_defaults(funcao=comando_parecidos)

    subcomandos.add_parser("matriz", help="a semelhança entre todos").set_defaults(funcao=comando_matriz)
    subcomandos.add_parser("vies", help="o viés de popularidade, com números").set_defaults(funcao=comando_vies)
    subcomandos.add_parser("catalogo", help="os títulos").set_defaults(funcao=comando_catalogo)

    analisado = analisador.parse_args(argumentos)

    try:
        return analisado.funcao(analisado)
    except ValueError as erro:
        print(erro, file=sys.stderr)

        return 1
