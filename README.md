# Nota Secreta - Agente Dixit com LLM

Este repositório contém a implementação de um agente de IA para jogar **Nota Secreta** (um jogo inspirado em Dixit adaptado para trechos de músicas brasileiras) utilizando modelos de linguagem locais (LLM).

---

## Integrantes do Grupo
* **Luiz Gabriel Antunes Sena**
* **Marcos Paulo Vieira Pedrosa**
* **Letícia Souza de Souza**

---

## Repositório e Instalação

* **Repositório:** [Gabsz193/nota-secreta](https://github.com/Gabsz193/nota-secreta)

### Passo a Passo de Instalação:

1. Clone o repositório:
   ```bash
   git clone https://github.com/Gabsz193/nota-secreta.git
   cd nota-secreta
   ```

2. Crie e ative o ambiente virtual Python:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Baixe o modelo LLM executando o script fornecido:
   ```bash
   chmod +x download_model.sh
   ./download_model.sh
   ```
   *(Este script realiza o download do arquivo `Phi-3.5-mini-instruct-Q4_K_M.gguf` necessário para rodar o serviço de linguagem local).*

---

## Como Executar o Código

Você pode iniciar o fluxo completo do jogo através do script principal `start_game.sh`:

```bash
chmod +x start_game.sh
./start_game.sh
```

Esse script realiza as seguintes etapas automaticamente:
1. Ativa o ambiente virtual `.venv`.
2. Inicia o serviço LLM local em segundo plano (`llm_service.py`) usando o modelo baixado.
3. Inicia o Game Master (`game_master.py`) e registra os agentes da partida.
4. Executa a simulação completa do jogo (`run_game.py`).
5. Finaliza e analisa o resultado da partida gerando o placar via `analyze_logs.py`.

### Visualizando a Ajuda e Parâmetros:
Para rodar diretamente o script de execução e visualizar todas as opções e parâmetros disponíveis:

```bash
source .venv/bin/activate
python3 run_game.py --help
```
*(ou execute diretamente usando o interpretador do venv: `.venv/bin/python run_game.py --help`)*

---

## Exemplo de Saída Esperada

### 1. Resumo do Log (Console)
Ao finalizar a partida, o script de análise exibirá uma saída semelhante a esta no terminal:

```text
==========================================
Jogo finalizado! Analisando os resultados...
==========================================
Analisando o log mais recente: logs/partida_20260619_031441.json

Placar final:
  Agente 1: 26 pontos
  Agente 2: 19 pontos
  Agente 3: 19 pontos
  Agente 4: 16 pontos
  Agente 5: 13 pontos
  Agente 6: 30 pontos

Dicas geradas pelo nosso agente (LLMAgent_1):
  Rodada 1: Dica -> 'Amor escondido em um brinde não'
  Rodada 7: Dica -> 'Ímã atrai ferragem'
```

### 2. Detalhes de Rodadas Completas (Visualização Legível)
Abaixo está a representação legível das **duas primeiras rodadas completas** da partida utilizando a ferramenta de leitura de logs do jogo:

```text
round 1
Clue (agent 0 - LLMAgent_1): "Amor escondido em um brinde não"
id  card_id  title              0  1  2  3  4  5  Pts  Acm  New id  New lyrics
--  -------  -----------------  -  -  -  -  -  -  ---  ---  ------  ------------
0   116      Último Desejo         x           x  3    3    182     Vou Deixar
1   168      Modinha                  x     x  x  6    6    133     Sonífera Ilha
2   129      Uma Brasileira              x  x     2    2    103     Eu Nasci Há Dez Mil Anos Atrás
3   12       Domingo no Parque                    0    0    221     Chalana
4   152      Marina                               0    0    102     O Barquinho
5   138      Te Ver                x  x  x        6    6    131     Brincar de Viver

round 2
Clue (agent 1 - RandomAgent_2): "amor não deixa contas fazer madrugada"
id  card_id  title                   0  1  2  3  4  5  Pts  Acm  New id  New lyrics
--  -------  ----------------------  -  -  -  -  -  -  ---  ---  ------  -----------------
0   41       Bem Que Se Quis                  x        4    7    188     Aguenta Coração
1   190      Pintura Íntima          x              x  3    9    172     Sá Marina
2   194      Sentimental Demais      x           x  x  3    5    177     Amor Maior
3   58       O Mar                         x           1    1    169     Malemolência
4   150      Super-Homem - A Canção                    0    0    125     Além do Horizonte
5   70       Anna Julia                    x  x  x     6    12   143     Minha Namorada
```

---

## Descrição dos Prompts e Heurísticas Implementadas
Todas as lógicas de prompts e heurísticas específicas para o agente estratégico estão concentradas no arquivo [versao2.py](file:///home/luizg/nota-secreta/versao2.py):

1. **Escolha de Cartas (`choose_card`)**:
   O prompt orienta a LLM a selecionar, dentre as cartas de sua mão, aquela que possua as expressões mais genéricas e passíveis de representações criativas. Isso ajuda o agente a formular pistas que não sejam nem óbvias demais (onde todos acertam) nem obscuras demais (onde ninguém acerta).

2. **Envio de Dicas (`send_clue`)**:
   Instrui a LLM a gerar uma pista com no máximo 6 palavras que evite conter termos presentes na letra original da música. A dica deve ser baseada em sentimentos secundários, provérbios ou analogias. 

3. **Associação de Dica (`select_card_by_clue`)**:
   Auxilia a LLM a selecionar a melhor música que se encaixe na dica proposta por outro jogador de forma a "enganar" os demais adversários e receber votos.

4. **Tomada de Voto Inteligente (`vote`)**:
   * **Highlighting**: O agente identifica termos que aparecem tanto na dica (`clue`) quanto no trecho das letras candidatas e as transforma para **MAIÚSCULO**. Isso auxilia na contextualização rápida da LLM sobre possíveis coincidências.
   * **Detecção de Candidato Suspeito**: Caso uma música possua *todas* as palavras da dica, ela é rotulada como `Opcao (SUSPEITA) {idx}`.
   * **Heurística de Filtragem Crítica**: Se houver um candidato suspeito, o agente reduz drasticamente a lista de opções apresentadas no prompt da LLM, mantendo **apenas** a opção suspeita e **uma outra** alternativa qualquer. Isso força o modelo de linguagem local a concentrar sua escolha nos caminhos mais prováveis de voto correto, melhorando significativamente a acurácia sob limitações do modelo local.

---

## Dificuldades Encontradas e Soluções

1. **Alinhamento do Formato de Saída com LLMs Locais**:
   * *Problema:* Modelos locais pequenos (como o Phi-3.5) tendem a divagar ou falhar em restrições rígidas (por exemplo, retornar apenas um número ou formato estrito como `n, m`).
   * *Solução:* Criação de parsers regex robustos na classe base para capturar inteiros no texto gerado e implementação de listas de fallbacks aleatórios seguros caso o parse falhe.

2. **Dicas Muito Longas ou Óbvias**:
   * *Problema:* Modelos geravam frases excessivas ou usavam termos literais da letra da música.
   * *Solução:* Validação de substring no agente estratégico para zerar e regenerar a pista com base em palavras-chave extraídas da música, além de limpeza manual de cabeçalhos redundantes de geração.

3. **Otimização do Foco de Voto**:
   * *Problema:* Quando havia muitas opções parecidas, a LLM local se confundia sobre qual escolher e esquecia as instruções de buscar palavras exatas.
   * *Solução:* Destacamos as palavras sobrepostas em letras maiúsculas e introduzimos a heurística de limitar as opções do prompt para conter apenas a suspeita e mais uma opção alternativa quando uma suspeita clara é identificada.
