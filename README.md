# recomendacoes

O "porque você assistiu X" do **CondePlay**: filtragem colaborativa item-item,
semelhança por conteúdo e a mistura das duas. Python puro, sem uma dependência.

```
$ python -m recomendacoes para 10

Para o perfil 10:

  Cidade de Vidro
    Porque você assistiu Sinal Fraco — também é ficção científica
    nota 0.961  (comportamento 1.00, conteúdo 0.87)

  Dossiê Meia-Noite
    Porque você assistiu Sinal Fraco — também é suspense
    nota 0.729  (comportamento 0.61, conteúdo 1.00)

  Caçadores de Estática
    Porque você assistiu Sinal Fraco — também com Ivone Castelo
    nota 0.642  (comportamento 0.61, conteúdo 0.71)
```

## O viés de popularidade, medido

O erro que faz um recomendador caseiro parecer quebrado é contar
co-ocorrências: quantas pessoas viram os dois títulos. É a medida intuitiva, e
o campeão de audiência co-ocorre com **tudo** — então ele vira a recomendação
de todo mundo, para qualquer histórico.

O projeto não se limita a dizer isso. Ele calcula as duas medidas sobre o mesmo
conjunto de dados e mostra a diferença:

```
$ python -m recomendacoes vies

  O mais assistido é Enquanto a Chuva Não Passa, com 9 perfis.

  título                         co-ocorrência crua             cosseno
  --------------------------------------------------------------------------------
  Cidade de Vidro                Enquanto a Chuva Não Passa     Caçadores de Estática
  O Último Trem para Olinda      Enquanto a Chuva Não Passa     Litoral
  Enquanto a Chuva Não Passa     O Último Trem para Olinda      O Último Trem para Olinda
  Caçadores de Estática          Cidade de Vidro                Cidade de Vidro
  A Ilha dos Relógios Parados    Enquanto a Chuva Não Passa     Enquanto a Chuva Não Passa
  Dossiê Meia-Noite              Cidade de Vidro                Cidade de Vidro
  Litoral                        Enquanto a Chuva Não Passa     O Último Trem para Olinda
  Sinal Fraco                    Cidade de Vidro                Cidade de Vidro

  A crua aponta para o campeão 4 vezes; o cosseno, 1.
```

A correção cabe numa divisão:

```
co-ocorrência crua:  |A ∩ B|
cosseno:             |A ∩ B| / sqrt(|A| · |B|)
```

Deixa de ser "quantas pessoas viram os dois" e passa a ser "que fração de quem
viu A também viu B, e vice-versa". Um título de nicho com 8 dos seus 10
espectadores em comum com o alvo ganha do campeão que tem 12 dos seus 100 —
e é isso que a intuição diz que deveria acontecer.

## Duas metades, cada uma cobrindo o buraco da outra

A **colaborativa** encontra semelhanças que ninguém programou. Ninguém precisou
declarar que *Cidade de Vidro* e *Sinal Fraco* são ficção científica; o
comportamento disse. E ela é **cega para qualquer título que ninguém assistiu
ainda** — num catálogo que recebe lançamento toda semana, o pior lugar possível
para ser cega.

A **de conteúdo** conhece o lançamento desde antes de ele estrear, por gênero,
elenco, direção e época. E é **incapaz de descobrir** que dois títulos sem nada
em comum no papel agradam às mesmas pessoas: ela só repete o que já está escrito
nos metadados.

Um teste prova as duas afirmações: o lançamento de hoje aparece na lista com
`comportamento 0.00` — e some por completo quando o peso do comportamento vai a
1.

## A explicação precisa ser verdade

"Porque você assistiu X" é uma afirmação de causa. Se três títulos contribuíram
mais ou menos igual para uma recomendação, nomear um deles é escolher um culpado
ao acaso e apresentá-lo como causa — e quem clicar esperando mais daquele título
recebe outra coisa.

Então a frase só nomeia a semente quando ela responde por **pelo menos metade**
da nota. Abaixo disso, o recomendador diz o que de fato sabe:

```
  Caçadores de Estática
    Porque você assiste títulos parecidos
    nota 1.000  (comportamento 1.00, conteúdo 1.00)
```

Dois testes guardam isso: a semente citada é sempre algo que a pessoa assistiu,
e o limiar decide a frase.

## Do que aconteceu na tela para o que a pessoa gosta

O sinal que chega é bruto: "o perfil 3 assistiu 812 segundos do título 7, que
tem 2520". Virar interesse envolve decisões que ninguém vê e todo mundo sente:

- **Um segundo não vale por um segundo.** Quarenta minutos de um filme de duas
  horas e quarenta minutos de um episódio de quarenta e dois são o mesmo tempo
  e interesses opostos. Conta a fração.
- **Abandonar cedo não conta nem a favor nem contra.** Abaixo de 5% foi clique,
  não opinião. No histórico de demonstração o perfil 3 viu 3% de *Cidade de
  Vidro*; se isso contasse, ele receberia ficção científica pelo resto da vida.
- **Reassistir aumenta, com teto.** Sem teto, dez sessões valem 10, e esse 10
  multiplicaria a semelhança de um título inteiro por causa de uma pessoa só.
- **Sem duração conhecida não há fração.** Chutar 1,0 inventaria interesse que
  não foi observado.

## O oráculo dos testes

`statistics.correlation` está na biblioteca padrão do Python desde a 3.10, e não
foi escrita por mim. A correlação daqui é conferida contra ela em **cem pares de
vetores sorteados** — se as duas batem sempre, a minha está certa, ou as duas
estão erradas do mesmo jeito, o que é bem menos provável.

O cosseno não tem equivalente na biblioteca padrão, então o oráculo é outro: a
forma fechada para vetores binários e a forma geral sobre vetores de zeros e uns
são duas contas independentes, comparadas em 200 pares de conjuntos sorteados.

## Rodando

Não há o que instalar. Python 3.12 ou mais novo.

```bash
python -m recomendacoes para 1              # o que recomendar a um perfil
python -m recomendacoes para 5 --idade 10   # com controle parental
python -m recomendacoes para 1 --peso 0.0   # só conteúdo; 1.0 = só comportamento
python -m recomendacoes parecidos 1         # as duas medidas, lado a lado
python -m recomendacoes matriz              # a semelhança entre todos
python -m recomendacoes vies                # a demonstração acima
python -m recomendacoes catalogo
```

```
$ python -m recomendacoes matriz

Semelhança entre títulos, pelo comportamento:

           1      2      3      4      5      6      7      8
    1      ·   0.29   0.58   0.82   0.33   0.82   0.29   0.67   Cidade de Vidro
    2   0.29      ·   0.67   0.35   0.29   0.35   0.75   0.00   O Último Trem para Olinda
    3   0.58   0.67      ·   0.47   0.58   0.47   0.67   0.38   Enquanto a Chuva Não Passa
    4   0.82   0.35   0.47      ·   0.41   0.50   0.35   0.41   Caçadores de Estática
    5   0.33   0.29   0.58   0.41      ·   0.41   0.29   0.00   A Ilha dos Relógios Parados
    6   0.82   0.35   0.47   0.50   0.41      ·   0.35   0.41   Dossiê Meia-Noite
    7   0.29   0.75   0.67   0.35   0.29   0.35      ·   0.00   Litoral
    8   0.67   0.00   0.38   0.41   0.00   0.41   0.00      ·   Sinal Fraco
```

Como biblioteca:

```python
from recomendacoes import Recomendador, matriz_de_interesse
from recomendacoes.catalogo import DEMONSTRACAO as catalogo
from recomendacoes.historico import DEMONSTRACAO as eventos

recomendador = Recomendador(catalogo, matriz_de_interesse(eventos))

for r in recomendador.para(perfil=1, quantos=5, idade_maxima=None):
    print(catalogo.nome(r.titulo), r.explicacao, r.nota)
```

## Testes

```bash
python -m unittest discover -s testes -t . -v
```

103 testes: as medidas contra a biblioteca padrão, o viés medido nos dois
sentidos, o piso e o teto do interesse, a partida a frio nas duas direções, o
controle parental com a contraprova de que ele faz diferença, a honestidade da
explicação e a linha de comando inteira.

## Estrutura

```
recomendacoes/similaridade.py   cosseno, jaccard, pearson — e a co-ocorrência crua, para contraste
recomendacoes/eventos.py        do que aconteceu na tela para o interesse
recomendacoes/colaborativa.py   a matriz item-item
recomendacoes/conteudo.py       gênero, elenco, direção, época — e os motivos da frase
recomendacoes/mistura.py        junta as duas metades e monta a explicação
recomendacoes/catalogo.py       os títulos, iguais aos que a API semeia
recomendacoes/historico.py      eventos de demonstração, com um gosto por perfil
recomendacoes/cli.py            a linha de comando
```

## O conteúdo é próprio

Os títulos, as sinopses e os nomes são **inventados para este projeto** e são os
mesmos que a API em C# semeia. Um catálogo de exemplo com obras reais traria
sinopse e arte de terceiros para dentro do repositório sem necessidade nenhuma.

O histórico de reprodução é inventado também, e de propósito: cada perfil tem um
gosto declarado num comentário, e o recomendador precisa reencontrá-lo sem que
ninguém lhe conte.

## Onde ele se encaixa

Faz parte do **CondePlay**, um serviço de streaming montado em peças separadas:

| | |
|---|---|
| [`catalogo`](https://github.com/condeDeveloper/catalogo) | a API do catálogo, em C# e .NET 8 |
| [`player-hls`](https://github.com/condeDeveloper/player-hls) | o player HLS, do zero |
| [`conde-play`](https://github.com/condeDeveloper/conde-play) | a tela |
| [`mp4`](https://github.com/condeDeveloper/mp4) | os metadados da mídia |
| **`recomendacoes`** | o "porque você assistiu X" |

## Limites conhecidos

- **Não aprende com o clique.** Se a pessoa vê a recomendação e não clica, isso
  é informação — e aqui ela se perde. Um sistema de verdade registra a
  impressão, não só a reprodução.
- **Recalcula tudo do zero.** A matriz item-item de um catálogo grande não se
  refaz a cada requisição; num serviço de verdade ela é calculada de madrugada
  e carregada pronta.
- **Não diversifica.** As cinco recomendações podem ser cinco suspenses. Quem
  gosta de suspense talvez goste disso, mas uma lista sem variedade nenhuma
  também é uma falha, e corrigi-la exige penalizar candidatos parecidos com
  quem já entrou.
- **Sem avaliação offline.** Não há divisão entre treino e teste nem métrica de
  acerto. O que os testes verificam são propriedades — não recomendar o já
  visto, respeitar o controle parental, não mentir na explicação —, não
  qualidade de recomendação.
- **Os pesos foram escolhidos, não aprendidos.** `PESO_GENERO`, `DOMINIO_MINIMO`
  e os demais são decisões minhas, expostas como constantes com o porquê
  escrito ao lado, e não resultado de ajuste sobre dados.

## Licença

MIT.
