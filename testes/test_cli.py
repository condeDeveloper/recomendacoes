"""A linha de comando, rodada de verdade."""

from __future__ import annotations

import contextlib
import io
import unittest

from recomendacoes.catalogo import DEMONSTRACAO as CATALOGO
from recomendacoes.cli import principal


def rodar(*argumentos) -> tuple[int, str, str]:
    """Roda um comando e devolve código, saída e erro."""
    saida, erro = io.StringIO(), io.StringIO()

    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
        codigo = principal(list(argumentos))

    return codigo, saida.getvalue(), erro.getvalue()


class TestComandoPara(unittest.TestCase):
    def test_recomenda_e_explica(self):
        codigo, saida, _ = rodar("para", "10")

        self.assertEqual(codigo, 0)
        self.assertIn("Cidade de Vidro", saida)
        self.assertIn("Porque você assistiu Sinal Fraco", saida)

    def test_nao_recomenda_o_que_a_pessoa_viu(self):
        _, saida, _ = rodar("para", "10", "--quantos", "99")

        self.assertNotIn("Sinal Fraco\n", saida.replace("assistiu Sinal Fraco", ""))

    def test_perfil_sem_historico_recebe_uma_frase_clara(self):
        codigo, saida, _ = rodar("para", "999")

        self.assertEqual(codigo, 0)
        self.assertIn("sem histórico", saida)

    def test_o_filtro_de_idade_chega_pela_linha_de_comando(self):
        _, com_filtro, _ = rodar("para", "5", "--quantos", "99", "--idade", "10")
        _, sem_filtro, _ = rodar("para", "5", "--quantos", "99")

        self.assertNotIn("Caçadores de Estática", com_filtro)
        self.assertIn("Caçadores de Estática", sem_filtro)

    def test_o_peso_muda_o_resultado(self):
        _, comportamento, _ = rodar("para", "1", "--peso", "1.0")
        _, conteudo, _ = rodar("para", "1", "--peso", "0.0")

        self.assertNotEqual(comportamento, conteudo)

    def test_peso_invalido_sai_com_erro(self):
        codigo, _, erro = rodar("para", "1", "--peso", "3")

        self.assertEqual(codigo, 1)
        self.assertIn("de 0 a 1", erro)


class TestComandoParecidos(unittest.TestCase):
    def test_mostra_as_duas_medidas(self):
        codigo, saida, _ = rodar("parecidos", "1")

        self.assertEqual(codigo, 0)
        self.assertIn("pelo comportamento", saida)
        self.assertIn("pelo conteúdo", saida)

    def test_titulo_inexistente_sai_com_erro(self):
        codigo, _, erro = rodar("parecidos", "999")

        self.assertEqual(codigo, 1)
        self.assertIn("Não há título 999", erro)


class TestComandoVies(unittest.TestCase):
    def test_mostra_as_duas_colunas_e_o_placar(self):
        codigo, saida, _ = rodar("vies")

        self.assertEqual(codigo, 0)
        self.assertIn("co-ocorrência crua", saida)
        self.assertIn("cosseno", saida)
        self.assertIn("A crua aponta para o campeão 4 vezes; o cosseno, 1.", saida)

    def test_nomeia_o_campeao(self):
        _, saida, _ = rodar("vies")

        self.assertIn("O mais assistido é Enquanto a Chuva Não Passa, com 9 perfis.", saida)


class TestOutrosComandos(unittest.TestCase):
    def test_matriz_traz_uma_linha_por_titulo(self):
        codigo, saida, _ = rodar("matriz")

        self.assertEqual(codigo, 0)

        for titulo in CATALOGO:
            self.assertIn(titulo.nome, saida)

        # A diagonal vem marcada, e não com 1,00: um título é idêntico a si
        # mesmo e isso não é informação.
        self.assertEqual(saida.count("·"), len(CATALOGO))

    def test_catalogo_lista_os_oito(self):
        codigo, saida, _ = rodar("catalogo")

        self.assertEqual(codigo, 0)
        self.assertEqual(len(saida.strip().splitlines()), 8)


class TestArgumentosInvalidos(unittest.TestCase):
    def test_sem_comando_o_argparse_recusa(self):
        with self.assertRaises(SystemExit):
            rodar()

    def test_comando_desconhecido(self):
        with self.assertRaises(SystemExit):
            rodar("transcodificar")


if __name__ == "__main__":
    unittest.main()
