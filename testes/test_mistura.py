"""A mistura das duas metades, e a honestidade da explicação.

O teste mais importante deste arquivo não é sobre ordenação: é sobre a frase.
"Porque você assistiu X" é uma afirmação de causa, e o recomendador só pode
fazê-la quando X de fato responde pela recomendação.
"""

from __future__ import annotations

import unittest

from recomendacoes.catalogo import DEMONSTRACAO as CATALOGO
from recomendacoes.catalogo import Catalogo, Titulo
from recomendacoes.eventos import Evento, matriz_de_interesse
from recomendacoes.historico import DEMONSTRACAO as HISTORICO
from recomendacoes.mistura import DOMINIO_MINIMO, Recomendador


class TestARecomendacao(unittest.TestCase):
    def setUp(self):
        self.matriz = matriz_de_interesse(HISTORICO)
        self.recomendador = Recomendador(CATALOGO, self.matriz)

    def test_nunca_recomenda_o_que_ja_foi_visto(self):
        for perfil in self.matriz:
            vistos = set(self.matriz[perfil])
            saida = {r.titulo for r in self.recomendador.para(perfil, quantos=99)}

            self.assertEqual(vistos & saida, set(), f"perfil {perfil}")

    def test_vem_da_maior_nota_para_a_menor(self):
        notas = [r.nota for r in self.recomendador.para(1, quantos=99)]

        self.assertEqual(notas, sorted(notas, reverse=True))

    def test_respeita_o_quantos(self):
        self.assertEqual(len(self.recomendador.para(1, quantos=2)), 2)

    def test_perfil_sem_historico_recebe_lista_vazia(self):
        self.assertEqual(self.recomendador.para(999), [])

    def test_a_ordem_e_a_mesma_a_cada_execucao(self):
        primeira = [r.titulo for r in self.recomendador.para(3, quantos=99)]

        for _ in range(5):
            outro = Recomendador(CATALOGO, matriz_de_interesse(HISTORICO))

            self.assertEqual([r.titulo for r in outro.para(3, quantos=99)], primeira)


class TestAsDuasMetadesNaMesmaEscala(unittest.TestCase):
    def test_as_duas_notas_ficam_entre_zero_e_um(self):
        # Este é o teste que pegou um desequilíbrio de verdade: a colaborativa
        # era normalizada pelo máximo e a de conteúdo não, e a de conteúdo pode
        # chegar a 2 porque o interesse passa de 1 em quem reassiste. Somar as
        # duas cruas faria o peso pesar qualquer coisa menos o que o nome diz.
        recomendador = Recomendador(CATALOGO, matriz_de_interesse(HISTORICO))

        for perfil in recomendador.matriz:
            for recomendacao in recomendador.para(perfil, quantos=99):
                self.assertGreaterEqual(recomendacao.colaborativa, 0.0)
                self.assertLessEqual(recomendacao.colaborativa, 1.0)
                self.assertGreaterEqual(recomendacao.conteudo, 0.0)
                self.assertLessEqual(recomendacao.conteudo, 1.0)
                self.assertLessEqual(recomendacao.nota, 1.0)

    def test_peso_um_ignora_o_conteudo(self):
        so_comportamento = Recomendador(CATALOGO, matriz_de_interesse(HISTORICO), peso_colaborativo=1.0)

        for recomendacao in so_comportamento.para(1, quantos=99):
            self.assertAlmostEqual(recomendacao.nota, recomendacao.colaborativa, places=12)

    def test_peso_zero_ignora_o_comportamento(self):
        so_conteudo = Recomendador(CATALOGO, matriz_de_interesse(HISTORICO), peso_colaborativo=0.0)

        for recomendacao in so_conteudo.para(1, quantos=99):
            self.assertAlmostEqual(recomendacao.nota, recomendacao.conteudo, places=12)

    def test_peso_fora_da_faixa_e_recusado(self):
        with self.assertRaises(ValueError):
            Recomendador(CATALOGO, matriz_de_interesse(HISTORICO), peso_colaborativo=1.5)


class TestAExplicacao(unittest.TestCase):
    """A parte que a pessoa lê — e que precisa ser verdade."""

    def setUp(self):
        self.recomendador = Recomendador(CATALOGO, matriz_de_interesse(HISTORICO))

    def test_a_semente_citada_e_sempre_algo_que_a_pessoa_viu(self):
        # Citar um título que a pessoa não assistiu é a pior falha possível
        # aqui: a frase deixa de ser explicação e vira invenção.
        for perfil in self.recomendador.matriz:
            vistos = set(self.recomendador.matriz[perfil])

            for recomendacao in self.recomendador.para(perfil, quantos=99):
                if recomendacao.semente is not None:
                    self.assertIn(recomendacao.semente, vistos, f"perfil {perfil}")

    def test_quando_uma_semente_domina_ela_e_nomeada(self):
        # O perfil 10 viu um título só, então toda recomendação dele vem de
        # 100% daquela semente — e a frase pode dizer o nome com segurança.
        for recomendacao in self.recomendador.para(10, quantos=99):
            self.assertEqual(recomendacao.semente, 8)
            self.assertTrue(recomendacao.explicacao.startswith("Porque você assistiu Sinal Fraco"))

    def test_quando_nenhuma_domina_o_recomendador_nao_escolhe_um_culpado(self):
        # O perfil 1 viu quatro títulos, e a principal recomendação dele vem
        # de todos os quatro somados. Nomear um seria apontar uma causa que
        # não é a causa — e a pessoa que clicar esperando mais daquele título
        # recebe outra coisa.
        recomendacoes = self.recomendador.para(1, quantos=99)
        primeira = recomendacoes[0]

        self.assertEqual(primeira.explicacao, "Porque você assiste títulos parecidos")

    def test_a_explicacao_traz_o_motivo_quando_existe(self):
        do_perfil_10 = {r.titulo: r for r in self.recomendador.para(10, quantos=99)}

        # Sinal Fraco e Cidade de Vidro são as duas de ficção científica.
        self.assertIn("também é ficção científica", do_perfil_10[1].explicacao)

    def test_nunca_sai_uma_frase_vazia(self):
        for perfil in self.recomendador.matriz:
            for recomendacao in self.recomendador.para(perfil, quantos=99):
                self.assertTrue(recomendacao.explicacao.strip())

    def test_o_limiar_de_dominio_e_o_que_decide(self):
        # Abaixo do limiar a frase não nomeia ninguém; no limiar, nomeia.
        abaixo = self.recomendador.explicar(1, semente=8, dominio=DOMINIO_MINIMO - 0.01)
        acima = self.recomendador.explicar(1, semente=8, dominio=DOMINIO_MINIMO)

        self.assertEqual(abaixo, "Porque você assiste títulos parecidos")
        self.assertIn("Sinal Fraco", acima)

    def test_sem_semente_nenhuma_a_frase_nao_promete_causa(self):
        self.assertEqual(self.recomendador.explicar(1, semente=None, dominio=0.0), "Em alta no catálogo")


class TestControleParental(unittest.TestCase):
    def test_o_perfil_infantil_nao_recebe_dezesseis_nem_dezoito(self):
        recomendador = Recomendador(CATALOGO, matriz_de_interesse(HISTORICO))

        for recomendacao in recomendador.para(5, quantos=99, idade_maxima=10):
            self.assertLessEqual(CATALOGO[recomendacao.titulo].idade_minima, 10)

    def test_sem_o_filtro_ele_receberia_dezesseis(self):
        # A prova de que o filtro está fazendo alguma coisa: sem ele, o mesmo
        # perfil recebe um título de dezesseis anos.
        recomendador = Recomendador(CATALOGO, matriz_de_interesse(HISTORICO))
        sem_filtro = recomendador.para(5, quantos=99)

        self.assertTrue(any(CATALOGO[r.titulo].idade_minima > 10 for r in sem_filtro))

    def test_o_corte_acontece_antes_da_ordenacao(self):
        # Filtrar depois devolveria menos do que os `quantos` pedidos.
        recomendador = Recomendador(CATALOGO, matriz_de_interesse(HISTORICO))
        com_filtro = recomendador.para(5, quantos=2, idade_maxima=14)

        self.assertEqual(len(com_filtro), 2)


class TestPartidaAFrio(unittest.TestCase):
    def test_um_lancamento_e_recomendado_no_dia_da_estreia(self):
        # O buraco que a colaborativa não tapa: este título tem zero
        # espectadores, logo semelhança colaborativa zero com tudo — e mesmo
        # assim chega à lista, pela semelhança de conteúdo.
        catalogo = Catalogo(
            {t.id: t for t in CATALOGO}
            | {
                99: Titulo(
                    id=99,
                    nome="Estreia de Hoje",
                    tipo="filme",
                    ano=2026,
                    generos=frozenset({"suspense", "ficcao"}),
                    elenco=frozenset({"Ivone Castelo"}),
                    direcao="Caio Sampaio",
                    idade_minima=16,
                )
            }
        )

        recomendador = Recomendador(catalogo, matriz_de_interesse(HISTORICO))
        recomendacoes = recomendador.para(10, quantos=99)
        estreia = next((r for r in recomendacoes if r.titulo == 99), None)

        self.assertIsNotNone(estreia, "o lançamento precisa aparecer")
        self.assertEqual(estreia.colaborativa, 0.0, "e sem nenhum apoio do comportamento")
        self.assertGreater(estreia.conteudo, 0.0)

    def test_com_peso_um_o_lancamento_some(self):
        # A contraprova: ignorando o conteúdo, o lançamento desaparece. É
        # exatamente por isso que a mistura existe.
        catalogo = Catalogo(
            {t.id: t for t in CATALOGO}
            | {
                99: Titulo(
                    id=99,
                    nome="Estreia de Hoje",
                    tipo="filme",
                    ano=2026,
                    generos=frozenset({"suspense", "ficcao"}),
                    elenco=frozenset({"Ivone Castelo"}),
                    direcao="Caio Sampaio",
                    idade_minima=16,
                )
            }
        )

        recomendador = Recomendador(catalogo, matriz_de_interesse(HISTORICO), peso_colaborativo=1.0)

        self.assertNotIn(99, {r.titulo for r in recomendador.para(10, quantos=99)})


class TestHistoricoDeUmPerfilNovo(unittest.TestCase):
    def test_quem_so_clicou_e_saiu_nao_tem_recomendacao(self):
        eventos = [Evento(perfil=50, titulo=1, segundos_assistidos=5, segundos_totais=7080)]
        recomendador = Recomendador(CATALOGO, matriz_de_interesse(eventos))

        self.assertEqual(recomendador.para(50), [])


if __name__ == "__main__":
    unittest.main()
