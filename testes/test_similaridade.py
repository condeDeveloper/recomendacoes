"""As medidas, conferidas contra a biblioteca padrão do Python.

`statistics.correlation` existe desde o Python 3.10 e é uma implementação que
não é minha. Se a minha correlação bate com ela em dados variados, a minha
está certa — ou as duas estão erradas do mesmo jeito, o que é
consideravelmente menos provável.

O cosseno não tem equivalente na biblioteca padrão, então o oráculo é outro:
a forma fechada para vetores binários e a forma geral são duas contas
independentes que precisam dar o mesmo número.
"""

from __future__ import annotations

import math
import random
import statistics
import unittest

from recomendacoes.similaridade import (
    coocorrencia,
    cosseno,
    cosseno_binario,
    jaccard,
    pearson,
)


class TestContraABibliotecaPadrao(unittest.TestCase):
    def test_pearson_bate_com_statistics_correlation(self):
        a = [4.0, 5.0, 5.0, 3.0, 2.0, 5.0]
        b = [3.0, 5.0, 4.0, 2.0, 1.0, 5.0]

        self.assertAlmostEqual(pearson(a, b), statistics.correlation(a, b), places=12)

    def test_pearson_bate_em_cem_amostras_sorteadas(self):
        # Um par de vetores pode dar certo por acaso; cem, não.
        sorteio = random.Random(20260924)

        for _ in range(100):
            tamanho = sorteio.randint(3, 20)
            a = [sorteio.uniform(-50, 50) for _ in range(tamanho)]
            b = [sorteio.uniform(-50, 50) for _ in range(tamanho)]

            self.assertAlmostEqual(pearson(a, b), statistics.correlation(a, b), places=9)

    def test_pearson_ve_correlacao_negativa(self):
        a = [1.0, 2.0, 3.0, 4.0]
        b = [4.0, 3.0, 2.0, 1.0]

        self.assertAlmostEqual(pearson(a, b), -1.0, places=12)
        self.assertAlmostEqual(pearson(a, b), statistics.correlation(a, b), places=12)


class TestCosseno(unittest.TestCase):
    def test_a_forma_fechada_bate_com_a_geral(self):
        # `cosseno_binario` usa |A ∩ B| / sqrt(|A|·|B|); `cosseno` faz a conta
        # completa sobre vetores de zeros e uns. São duas contas diferentes
        # para o mesmo número, e é isso que as torna um teste.
        sorteio = random.Random(7)
        universo = list(range(12))

        for _ in range(200):
            a = {i for i in universo if sorteio.random() < 0.5}
            b = {i for i in universo if sorteio.random() < 0.5}

            if not a or not b:
                continue

            vetor_a = [1.0 if i in a else 0.0 for i in universo]
            vetor_b = [1.0 if i in b else 0.0 for i in universo]

            self.assertAlmostEqual(cosseno_binario(a, b), cosseno(vetor_a, vetor_b), places=12)

    def test_conjuntos_iguais_dao_um(self):
        self.assertEqual(cosseno_binario({1, 2, 3}, {1, 2, 3}), 1.0)

    def test_conjuntos_disjuntos_dao_zero(self):
        self.assertEqual(cosseno_binario({1, 2}, {3, 4}), 0.0)

    def test_conjunto_vazio_nao_estoura(self):
        # Um título que ninguém viu não se parece com nada. Não é erro — é a
        # partida a frio, e quem divide por zero aqui descobre isso em produção.
        self.assertEqual(cosseno_binario(set(), {1, 2}), 0.0)
        self.assertEqual(cosseno([0.0, 0.0], [1.0, 2.0]), 0.0)

    def test_vetores_de_tamanhos_diferentes_sao_recusados(self):
        with self.assertRaises(ValueError):
            cosseno([1.0, 2.0], [1.0])

    def test_o_cosseno_ignora_escala(self):
        # Dobrar um vetor não muda o ângulo. É por isso que o cosseno mede
        # gosto e não intensidade.
        self.assertAlmostEqual(
            cosseno([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]),
            1.0,
            places=12,
        )


class TestOVies(unittest.TestCase):
    """O motivo de este módulo existir, em quatro linhas de conta."""

    def test_a_crua_prefere_o_popular_e_o_cosseno_nao(self):
        # Um campeão de audiência visto por 100 pessoas, e um título de nicho
        # visto por 10. O nicho tem 8 espectadores em comum com o alvo — 80%
        # dele. O campeão tem 12 — 12% dele.
        alvo = set(range(10))
        nicho = set(range(8)) | {90, 91}
        campeao = set(range(100))

        self.assertGreater(coocorrencia(alvo, campeao), coocorrencia(alvo, nicho))
        self.assertGreater(cosseno_binario(alvo, nicho), cosseno_binario(alvo, campeao))

    def test_jaccard_pune_a_popularidade_mais_que_o_cosseno(self):
        alvo = set(range(10))
        campeao = set(range(100))

        self.assertLess(jaccard(alvo, campeao), cosseno_binario(alvo, campeao))


class TestJaccard(unittest.TestCase):
    def test_interseccao_sobre_uniao(self):
        self.assertAlmostEqual(jaccard({1, 2, 3}, {2, 3, 4}), 2 / 4)

    def test_dois_vazios_dao_zero_em_vez_de_dividir_por_zero(self):
        self.assertEqual(jaccard(set(), set()), 0.0)

    def test_nunca_passa_de_um(self):
        sorteio = random.Random(11)

        for _ in range(100):
            a = {sorteio.randrange(20) for _ in range(sorteio.randint(0, 10))}
            b = {sorteio.randrange(20) for _ in range(sorteio.randint(0, 10))}

            self.assertLessEqual(jaccard(a, b), 1.0)
            self.assertGreaterEqual(jaccard(a, b), 0.0)


class TestPearsonRecusaOImpossivel(unittest.TestCase):
    def test_um_ponto_so_nao_tem_correlacao(self):
        with self.assertRaises(ValueError):
            pearson([1.0], [2.0])

    def test_tamanhos_diferentes(self):
        with self.assertRaises(ValueError):
            pearson([1.0, 2.0, 3.0], [1.0, 2.0])

    def test_vetor_constante_da_zero_em_vez_de_estourar(self):
        # A biblioteca padrão levanta erro aqui; esta devolve 0, porque no
        # contexto de recomendação "não dá para dizer" tem de virar "não
        # recomenda", não uma exceção no meio da página.
        self.assertEqual(pearson([3.0, 3.0, 3.0], [1.0, 2.0, 3.0]), 0.0)

        with self.assertRaises(statistics.StatisticsError):
            statistics.correlation([3.0, 3.0, 3.0], [1.0, 2.0, 3.0])


if __name__ == "__main__":
    unittest.main()
