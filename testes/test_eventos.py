"""Do sinal bruto para o interesse.

As decisões testadas aqui são as que ninguém vê e todo mundo sente: quando um
clique vira interesse, quando não vira, e o que acontece com quem reassiste.
"""

from __future__ import annotations

import unittest

from recomendacoes.eventos import (
    FRACAO_DE_CONCLUSAO,
    FRACAO_MINIMA,
    INTERESSE_MAXIMO,
    Evento,
    interesse_do_evento,
    matriz_de_interesse,
    popularidade,
    quem_viu,
)
from recomendacoes.historico import DEMONSTRACAO as HISTORICO


class TestInteresseDeUmEvento(unittest.TestCase):
    def test_quem_terminou_demonstra_interesse_pleno(self):
        evento = Evento(perfil=1, titulo=1, segundos_assistidos=7000, segundos_totais=7080)

        self.assertEqual(interesse_do_evento(evento), 1.0)

    def test_quem_parou_nos_primeiros_segundos_nao_conta(self):
        # Três por cento de um filme de duas horas são três minutos. Pode ter
        # sido clique errado, pode ter sido o trailer. O que não pode é isso
        # contar como "gostou" — nem como "não gostou".
        evento = Evento(perfil=1, titulo=1, segundos_assistidos=212, segundos_totais=7080)

        self.assertLess(evento.fracao, FRACAO_MINIMA)
        self.assertEqual(interesse_do_evento(evento), 0.0)

    def test_quem_viu_metade_demonstra_meio_interesse(self):
        evento = Evento(perfil=1, titulo=1, segundos_assistidos=3540, segundos_totais=7080)

        self.assertAlmostEqual(interesse_do_evento(evento), 0.5)

    def test_um_segundo_nao_vale_por_um_segundo(self):
        # Quarenta minutos de um filme de duas horas e quarenta minutos de um
        # episódio de quarenta e dois são o mesmo tempo e interesses opostos.
        do_filme = Evento(perfil=1, titulo=1, segundos_assistidos=2400, segundos_totais=7080)
        do_episodio = Evento(perfil=1, titulo=7, segundos_assistidos=2400, segundos_totais=2520)

        self.assertLess(interesse_do_evento(do_filme), 0.4)
        self.assertEqual(interesse_do_evento(do_episodio), 1.0)

    def test_duracao_desconhecida_nao_inventa_interesse(self):
        # Sem duração não há fração. Chutar 1.0 inventaria um interesse que
        # não foi observado, e o recomendador passaria a recomendar com base
        # em dados que não existem.
        evento = Evento(perfil=1, titulo=1, segundos_assistidos=3000, segundos_totais=0)

        self.assertEqual(evento.fracao, 0.0)
        self.assertEqual(interesse_do_evento(evento), 0.0)

    def test_reassistir_aumenta_ate_um_teto(self):
        eventos = [
            Evento(perfil=1, titulo=1, segundos_assistidos=7080, segundos_totais=7080)
            for _ in range(10)
        ]

        matriz = matriz_de_interesse(eventos)

        self.assertEqual(matriz[1][1], INTERESSE_MAXIMO)

    def test_sem_teto_um_maratonista_dominaria_sozinho(self):
        # Este é o motivo do teto: dez sessões completas valem 10 sem ele, e
        # esse 10 multiplicaria a semelhança de um título inteiro por causa de
        # uma pessoa só.
        muitas = [
            Evento(perfil=1, titulo=1, segundos_assistidos=7080, segundos_totais=7080)
            for _ in range(10)
        ]

        soma_crua = sum(interesse_do_evento(evento) for evento in muitas)

        self.assertEqual(soma_crua, 10.0)
        self.assertEqual(matriz_de_interesse(muitas)[1][1], 2.0)


class TestMatriz(unittest.TestCase):
    def test_sessoes_partidas_somam(self):
        # Metade hoje, metade amanhã: assistiu o filme inteiro.
        eventos = [
            Evento(perfil=1, titulo=1, segundos_assistidos=3540, segundos_totais=7080),
            Evento(perfil=1, titulo=1, segundos_assistidos=3540, segundos_totais=7080),
        ]

        self.assertAlmostEqual(matriz_de_interesse(eventos)[1][1], 1.0)

    def test_quem_so_clicou_nao_aparece_na_matriz(self):
        eventos = [Evento(perfil=1, titulo=1, segundos_assistidos=10, segundos_totais=7080)]

        self.assertEqual(matriz_de_interesse(eventos), {})

    def test_o_perfil_3_largou_a_ficcao_e_isso_aparece(self):
        # No histórico de demonstração o perfil 3 viu 3% de Cidade de Vidro.
        # Se esse abandono contasse como interesse, ele receberia ficção
        # científica pelo resto da vida.
        matriz = matriz_de_interesse(HISTORICO)

        self.assertNotIn(1, matriz[3])
        self.assertIn(2, matriz[3])


class TestInversao(unittest.TestCase):
    def test_quem_viu_inverte_a_matriz(self):
        matriz = {1: {10: 1.0, 20: 0.5}, 2: {10: 1.0}}

        self.assertEqual(quem_viu(matriz), {10: {1, 2}, 20: {1}})

    def test_popularidade_conta_perfis_e_nao_sessoes(self):
        # Uma pessoa que viu dez vezes é uma pessoa. Contar sessões deixaria
        # um fã solitário parecer um fenômeno de audiência.
        eventos = [
            Evento(perfil=1, titulo=1, segundos_assistidos=7080, segundos_totais=7080)
            for _ in range(10)
        ] + [Evento(perfil=2, titulo=1, segundos_assistidos=7080, segundos_totais=7080)]

        self.assertEqual(popularidade(matriz_de_interesse(eventos)), {1: 2})

    def test_o_campeao_do_historico_de_demonstracao(self):
        quantos = popularidade(matriz_de_interesse(HISTORICO))

        self.assertEqual(max(quantos, key=quantos.get), 3)
        self.assertEqual(quantos[3], 9)


class TestConstantes(unittest.TestCase):
    def test_os_limiares_fazem_sentido_juntos(self):
        self.assertLess(FRACAO_MINIMA, FRACAO_DE_CONCLUSAO)
        self.assertGreaterEqual(INTERESSE_MAXIMO, 1.0)


if __name__ == "__main__":
    unittest.main()
