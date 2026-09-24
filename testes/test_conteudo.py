"""Semelhança por conteúdo, e as frases que ela produz."""

from __future__ import annotations

import unittest

from recomendacoes.catalogo import DEMONSTRACAO as CATALOGO
from recomendacoes.catalogo import Catalogo, Titulo
from recomendacoes.conteudo import (
    JANELA_DE_EPOCA,
    PESO_DIRECAO,
    PESO_ELENCO,
    PESO_EPOCA,
    PESO_GENERO,
    parecenca,
    parecidos,
    proximidade_de_epoca,
)


class TestPesos(unittest.TestCase):
    def test_somam_um(self):
        # Se não somassem 1, a nota máxima não seria 1 e comparar com a
        # colaborativa — que vai de 0 a 1 — deixaria de fazer sentido.
        soma = PESO_GENERO + PESO_ELENCO + PESO_DIRECAO + PESO_EPOCA

        self.assertAlmostEqual(soma, 1.0, places=12)

    def test_genero_pesa_mais_que_elenco(self):
        # Num catálogo pequeno quase todo mundo já trabalhou com todo mundo.
        # Elenco pesando mais ligaria tudo a tudo.
        self.assertGreater(PESO_GENERO, PESO_ELENCO)


class TestParecenca(unittest.TestCase):
    def test_um_titulo_e_identico_a_si_mesmo(self):
        self.assertEqual(parecenca(CATALOGO[1], CATALOGO[1]).nota, 1.0)

    def test_dois_de_ficcao_se_parecem_mais_que_ficcao_e_animacao(self):
        ficcao_com_suspense = parecenca(CATALOGO[1], CATALOGO[8])
        ficcao_com_animacao = parecenca(CATALOGO[1], CATALOGO[5])

        self.assertGreater(ficcao_com_suspense.nota, ficcao_com_animacao.nota)

    def test_a_nota_nunca_passa_de_um(self):
        for um in CATALOGO:
            for outro in CATALOGO:
                self.assertLessEqual(parecenca(um, outro).nota, 1.0)
                self.assertGreaterEqual(parecenca(um, outro).nota, 0.0)

    def test_e_simetrica(self):
        for um in CATALOGO:
            for outro in CATALOGO:
                self.assertAlmostEqual(
                    parecenca(um, outro).nota,
                    parecenca(outro, um).nota,
                    places=12,
                )

    def test_a_mesma_direcao_conta(self):
        # Cidade de Vidro e Dossiê Meia-Noite não dividem gênero nem elenco.
        # O que os liga é Rita Amorim na direção.
        resultado = parecenca(CATALOGO[1], CATALOGO[6])

        self.assertGreater(resultado.nota, 0.0)
        self.assertIn("também dirigido por Rita Amorim", resultado.motivos)


class TestMotivos(unittest.TestCase):
    def test_o_genero_aparece_por_extenso(self):
        # "também é ficcao" é o apelido do banco vazando para a tela.
        motivos = parecenca(CATALOGO[1], CATALOGO[8]).motivos

        self.assertIn("também é ficção científica", motivos)
        self.assertNotIn("também é ficcao", motivos)

    def test_o_elenco_em_comum_aparece_nomeado(self):
        motivos = parecenca(CATALOGO[1], CATALOGO[3]).motivos

        self.assertIn("também com Otávio Braga", motivos)

    def test_dois_nomes_saem_com_e(self):
        um = Titulo(1, "Um", "filme", 2020, frozenset(), frozenset({"Ana", "Bia"}), "Dir")
        outro = Titulo(2, "Outro", "filme", 2020, frozenset(), frozenset({"Ana", "Bia"}), "Outra")

        self.assertIn("também com Ana e Bia", parecenca(um, outro).motivos)

    def test_sem_nada_em_comum_nao_ha_motivo_inventado(self):
        um = Titulo(1, "Um", "filme", 1990, frozenset({"a"}), frozenset({"Ana"}), "Dir")
        outro = Titulo(2, "Outro", "filme", 2025, frozenset({"b"}), frozenset({"Bia"}), "Outra")

        self.assertEqual(parecenca(um, outro).motivos, ())


class TestEpoca(unittest.TestCase):
    def test_o_mesmo_ano_da_um(self):
        self.assertEqual(proximidade_de_epoca(CATALOGO[2], CATALOGO[7]), 1.0)

    def test_a_janela_fechada_da_zero(self):
        um = Titulo(1, "Um", "filme", 2000, frozenset(), frozenset(), "Dir")
        outro = Titulo(2, "Outro", "filme", 2000 + JANELA_DE_EPOCA, frozenset(), frozenset(), "Dir")

        self.assertEqual(proximidade_de_epoca(um, outro), 0.0)

    def test_cai_de_forma_suave(self):
        base = Titulo(1, "Um", "filme", 2000, frozenset(), frozenset(), "Dir")
        perto = Titulo(2, "Perto", "filme", 2002, frozenset(), frozenset(), "Dir")
        longe = Titulo(3, "Longe", "filme", 2008, frozenset(), frozenset(), "Dir")

        self.assertGreater(proximidade_de_epoca(base, perto), proximidade_de_epoca(base, longe))


class TestParecidos(unittest.TestCase):
    def test_nunca_devolve_o_proprio_titulo(self):
        for id_do_titulo in CATALOGO.ids():
            saida = [outro for outro, _ in parecidos(CATALOGO, id_do_titulo)]

            self.assertNotIn(id_do_titulo, saida)

    def test_vem_do_mais_parecido_para_o_menos(self):
        notas = [p.nota for _, p in parecidos(CATALOGO, 1)]

        self.assertEqual(notas, sorted(notas, reverse=True))

    def test_titulo_inexistente_devolve_lista_vazia(self):
        self.assertEqual(parecidos(CATALOGO, 999), [])

    def test_a_ordem_nao_depende_da_ordem_do_catalogo(self):
        # Sem desempate pelo id, dois títulos de nota igual sairiam na ordem
        # em que o catálogo foi montado.
        invertido = Catalogo({t.id: t for t in reversed(list(CATALOGO))})

        self.assertEqual(
            [outro for outro, _ in parecidos(CATALOGO, 1)],
            [outro for outro, _ in parecidos(invertido, 1)],
        )


class TestPartidaAFrio(unittest.TestCase):
    def test_um_lancamento_que_ninguem_viu_ja_tem_parecidos(self):
        # É o que a colaborativa não consegue: este título tem zero
        # espectadores e já se liga ao catálogo pelos metadados.
        catalogo = Catalogo(
            {t.id: t for t in list(CATALOGO)}
            | {
                99: Titulo(
                    id=99,
                    nome="Estreia de Hoje",
                    tipo="filme",
                    ano=2026,
                    generos=frozenset({"ficcao"}),
                    elenco=frozenset({"Solange Vieira"}),
                    direcao="Rita Amorim",
                )
            }
        )

        vizinhos = parecidos(catalogo, 99, quantos=1)

        self.assertTrue(vizinhos)
        self.assertEqual(vizinhos[0][0], 1, "o mais próximo é Cidade de Vidro")


class TestNomeDeTituloAusente(unittest.TestCase):
    def test_um_id_que_nao_existe_aparece_marcado(self):
        # Devolver "" faria a frase sair truncada e ninguém descobriria.
        self.assertEqual(CATALOGO.nome(4242), "[título 4242]")


if __name__ == "__main__":
    unittest.main()
