"""A filtragem colaborativa, e o viés que ela existe para evitar.

O teste central deste arquivo não verifica um número: verifica que **duas
medidas discordam**, e que a discordância vai na direção prevista. É a única
forma honesta de testar uma escolha de medida — mostrando o que a outra faria
com os mesmos dados.
"""

from __future__ import annotations

import unittest

from recomendacoes.catalogo import DEMONSTRACAO as CATALOGO
from recomendacoes.colaborativa import ModeloItemItem, coocorrencia_crua
from recomendacoes.eventos import Evento, matriz_de_interesse, popularidade
from recomendacoes.historico import DEMONSTRACAO as HISTORICO
from recomendacoes.similaridade import cosseno_binario


def _visto(perfil: int, titulo: int) -> Evento:
    return Evento(perfil=perfil, titulo=titulo, segundos_assistidos=100, segundos_totais=100)


class TestOViesDePopularidade(unittest.TestCase):
    """O campeão de audiência não pode ser a resposta para tudo."""

    def setUp(self):
        self.matriz = matriz_de_interesse(HISTORICO)
        self.modelo = ModeloItemItem(self.matriz)
        self.cruas = coocorrencia_crua(self.matriz)
        self.quantos = popularidade(self.matriz)
        self.campeao = max(self.quantos, key=self.quantos.get)

    def test_o_campeao_e_quem_se_espera(self):
        self.assertEqual(self.campeao, 3, CATALOGO.nome(3))
        self.assertEqual(self.quantos[self.campeao], 9)

    def test_a_crua_aponta_para_o_campeao_muito_mais_que_o_cosseno(self):
        def vezes(escolher) -> int:
            return sum(
                1
                for id_do_titulo in CATALOGO.ids()
                if escolher(id_do_titulo) == self.campeao
            )

        def melhor_cru(id_do_titulo):
            vizinhos = self.cruas.get(id_do_titulo, {})

            return max(sorted(vizinhos), key=lambda o: vizinhos[o]) if vizinhos else None

        def melhor_cosseno(id_do_titulo):
            vizinhos = self.modelo.parecidos_com(id_do_titulo, quantos=1)

            return vizinhos[0][0] if vizinhos else None

        pela_crua = vezes(melhor_cru)
        pelo_cosseno = vezes(melhor_cosseno)

        self.assertEqual(pela_crua, 4)
        self.assertEqual(pelo_cosseno, 1)
        self.assertGreater(pela_crua, pelo_cosseno)

    def test_para_cidade_de_vidro_as_duas_medidas_discordam(self):
        # O caso concreto: a crua diz "o campeão"; o cosseno diz Caçadores de
        # Estática, que divide elenco e público de verdade com o alvo.
        vizinhos_crus = self.cruas[1]
        melhor_cru = max(sorted(vizinhos_crus), key=lambda o: vizinhos_crus[o])

        self.assertEqual(melhor_cru, self.campeao)
        self.assertEqual(self.modelo.parecidos_com(1, quantos=1)[0][0], 4)


class TestSemelhanca(unittest.TestCase):
    def setUp(self):
        self.modelo = ModeloItemItem(matriz_de_interesse(HISTORICO))

    def test_um_titulo_e_identico_a_si_mesmo(self):
        self.assertEqual(self.modelo.semelhanca(1, 1), 1.0)

    def test_a_semelhanca_e_simetrica(self):
        for um in CATALOGO.ids():
            for outro in CATALOGO.ids():
                self.assertEqual(
                    self.modelo.semelhanca(um, outro),
                    self.modelo.semelhanca(outro, um),
                )

    def test_bate_com_o_calculo_direto(self):
        # A matriz é pré-calculada; esta é a mesma conta feita na hora, a
        # partir dos conjuntos de espectadores. Se a pré-computação tivesse
        # trocado um índice, aqui apareceria.
        espectadores = self.modelo.espectadores

        for um in CATALOGO.ids():
            for outro in CATALOGO.ids():
                if um == outro:
                    continue

                esperado = cosseno_binario(espectadores.get(um, set()), espectadores.get(outro, set()))

                self.assertAlmostEqual(self.modelo.semelhanca(um, outro), esperado, places=12)

    def test_titulo_que_ninguem_viu_nao_se_parece_com_nada(self):
        modelo = ModeloItemItem(matriz_de_interesse([_visto(1, 10), _visto(2, 10)]))

        self.assertEqual(modelo.parecidos_com(99), [])
        self.assertEqual(modelo.semelhanca(99, 10), 0.0)


class TestRecomendar(unittest.TestCase):
    def setUp(self):
        self.matriz = matriz_de_interesse(HISTORICO)
        self.modelo = ModeloItemItem(self.matriz)

    def test_nunca_recomenda_o_que_a_pessoa_ja_viu(self):
        # O erro mais comum de recomendador caseiro: o título mais parecido
        # com o que você viu é o que você viu.
        for perfil in self.matriz:
            vistos = set(self.matriz[perfil])
            sugeridos = {s.titulo for s in self.modelo.recomendar(perfil, quantos=99)}

            self.assertEqual(vistos & sugeridos, set(), f"perfil {perfil}")

    def test_perfil_sem_historico_nao_recebe_nada(self):
        self.assertEqual(self.modelo.recomendar(999), [])

    def test_toda_sugestao_sabe_de_onde_veio(self):
        for sugestao in self.modelo.recomendar(1, quantos=99):
            self.assertTrue(sugestao.contribuicoes)
            self.assertIn(sugestao.principal, self.matriz[1])

    def test_as_contribuicoes_vem_da_maior_para_a_menor(self):
        for sugestao in self.modelo.recomendar(6, quantos=99):
            pesos = [c.peso for c in sugestao.contribuicoes]

            self.assertEqual(pesos, sorted(pesos, reverse=True))

    def test_a_nota_e_a_soma_das_contribuicoes(self):
        for sugestao in self.modelo.recomendar(3, quantos=99):
            self.assertAlmostEqual(
                sugestao.nota,
                sum(c.peso for c in sugestao.contribuicoes),
                places=12,
            )

    def test_o_filtro_de_permitidos_age_antes_do_corte(self):
        # Filtrar depois de cortar devolveria menos resultados do que os
        # pedidos sempre que algo fosse removido.
        # O perfil 1 viu 1, 3, 6 e 8, e a colaborativa lhe ofereceria 4, 5, 2
        # e 7 nessa ordem. Restringindo a 5, 2 e 7 e pedindo dois, têm de vir
        # dois — e não um, que é o que sairia se o corte viesse antes do
        # filtro e o 4 ocupasse uma das vagas para ser descartado depois.
        permitidos = {5, 2, 7}
        sugestoes = self.modelo.recomendar(1, quantos=2, permitidos=permitidos)

        self.assertTrue(all(s.titulo in permitidos for s in sugestoes))
        self.assertEqual(len(sugestoes), 2)
        self.assertEqual([s.titulo for s in sugestoes], [5, 2])

    def test_a_ordem_e_estavel_entre_execucoes(self):
        # Sem desempate explícito, dois títulos de nota igual trocariam de
        # lugar conforme a ordem do dicionário e a mesma pergunta daria
        # respostas diferentes.
        primeira = [s.titulo for s in self.modelo.recomendar(3, quantos=99)]

        for _ in range(5):
            outro = ModeloItemItem(matriz_de_interesse(HISTORICO))

            self.assertEqual([s.titulo for s in outro.recomendar(3, quantos=99)], primeira)


class TestPartidaAFrio(unittest.TestCase):
    def test_com_um_titulo_so_no_historico_tudo_repousa_numa_semente(self):
        # O perfil 10 viu só Sinal Fraco. Ele até recebe sugestões — mas todas
        # se apoiam no mesmo e único título, enquanto as do perfil 1 se apoiam
        # em três ou quatro. É essa diferença, e não a quantidade, que mede a
        # fragilidade de um histórico curto: basta aquele título ter sido um
        # engano para o perfil inteiro ir junto.
        matriz = matriz_de_interesse(HISTORICO)
        modelo = ModeloItemItem(matriz)

        self.assertEqual(set(matriz[10]), {8})

        sementes_do_10 = {len(s.contribuicoes) for s in modelo.recomendar(10, quantos=99)}
        sementes_do_1 = {len(s.contribuicoes) for s in modelo.recomendar(1, quantos=99)}

        self.assertEqual(sementes_do_10, {1})
        self.assertTrue(all(quantas >= 3 for quantas in sementes_do_1))

    def test_titulo_estreado_hoje_e_invisivel_para_a_colaborativa(self):
        matriz = matriz_de_interesse(HISTORICO)
        modelo = ModeloItemItem(matriz)

        # Um id que ninguém viu: nenhuma sugestão pode citá-lo.
        sugeridos = {
            s.titulo for perfil in matriz for s in modelo.recomendar(perfil, quantos=99)
        }

        self.assertNotIn(99, sugeridos)


if __name__ == "__main__":
    unittest.main()
