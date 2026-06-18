# PARTE III: Nota Secreta

### 3.1. Objetivos

Neste trabalho vocês devem:

- Implementar agentes inteligentes que se comunicam via protocolo A2A (Agent-to-Agent).
    
- Integrar LLMs locais a agentes autônomos através de um serviço centralizado, similar a APIs como OpenAI/Google.
    
- Compreender os desafios de sistemas distribuídos: comunicação remota, concorrência, filas de requisição.
    
- Projetar estratégias para diferentes tipos de agentes (criativo vs. estratégico).
    
- Comparar o desempenho de diferentes abordagens em um ambiente competitivo.
    

> **Nota:** Diferentes componentes do software a ser implementado (o Game Master, o serviço LLM centralizado e um agente baseline aleatório) serão fornecidos pelo professor. Seu grupo deve fornecer a implementação de um agente inteligente que vocês julguem seja o mais adequado para uma avaliação competitiva.

### 3.2. O Jogo: Nota Secreta

Nota Secreta é uma adaptação do famoso jogo Dixit para o universo da música brasileira. Em vez de cartas com imagens abstratas, os jogadores utilizam letras de músicas brasileiras como elementos do jogo.

O jogo envolve 6 agentes autônomos (implementados por você e fornecidos pelo professor) que:

- Recebem uma "mão" de 4 letras de música cada.
- Alternam-se como "narrador" (quem dá a dica) e "melômanos" (amantes de músicas que tentam adivinhar as canções).
- Usam um serviço LLM centralizado para tomar decisões.
- Competem para atingir 30 pontos.

**Regras Completas**

Cada rodada funciona assim:

1. **Distribuição:** Cada agente recebe 4 músicas  (para reduzir custo de comunicação e inferência, cada música enviada ao agente contém uma visão enxuta da carta, com pelo menos id, title e uma versão truncada da letra).
2. **Narrador:** Um agente é escolhido como narrador da rodada (ordem circular).
3. **Escolha da letra:** O narrador seleciona UMA das suas 4 músicas.
4. **Dica:** O narrador gera uma dica de no máximo 6 palavras sobre a música escolhida.
5. **Seleção dos melômanos:** Cada outro agente escolhe, da sua própria mão, a música que MELHOR combina com a dica.
6. **Votação:** Todas as 6 cartas (1 do narrador + 5 dos outros) são embaralhadas e apresentadas. Cada melômano deve votar em exatamente duas opções distintas. O narrador não vota. Nenhum agente pode votar na própria carta. Um melômano acerta a carta do narrador se pelo menos um dos seus dois votos for a carta do narrador.
7. **Pontuação:** Segue as regras do Dixit (detalhadas abaixo).
8. **Reposição:** Novas músicas são distribuídas para manter 4 cartas por agente.
9. **Próxima rodada:** O papel de narrador passa para o próximo agente.

**Pontuação (Regra Oficial do Dixit Odyssey)**

| **Situação**                       | **Pontuação do narrador** | **Pontuação dos melômanos**                                                                      |
| ---------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------ |
| Ninguém votou na carta do narrador | 0                         | +2 pela rodada +1 para cada voto recebido em sua própria letra (limitado a 3)                    |
| Todos votaram na carta do narrador | 0                         | +2 pela rodada +1 para cada voto recebido em sua própria letra (limitado a 3)                    |
| Caso contrário                     | +3                        | +3 se acertou a letra do narrador +1 para cada voto recebido em sua própria letra (limitado a 3) |

**Observações:**
* O melômano acerta a letra do narrador se ele a incluir entre os seus dois votos.
* O narrador pode ganhar 3 pontos por rodada, no cenário de sucesso (ele não ganha pontos por voto recebido).
* Um agente pode ganhar no máximo 6 pontos por rodada (3 por acertar a dica do narrador e, no máximo, 3 por votos recebidos).
* O jogo termina quando um agente atinge 30 pontos, se tornando o vencedor da partida.

### 3.3 Arquitetura do Sistema

O sistema é composto por três camadas:

- **Camada de Orquestração:** Game Master (porta 8000+), gerencia o fluxo do jogo.
    - Comunicação com a camada abaixo via A2A (JSON-RPC sobre HTTP)
- **Camada de Agentes:** Agentes (portas 8001+), fornecem ferramentas para descrever ou ranquear músicas.
    - Comunicação com a camada abaixo via HTTP (REST API)
- **Camada de LLM:** LLM Service (porta 9000+), utiliza o modelo _Phi 3.5 Mini Instruct_, única instância do modelo LLM.

**Game Master (Fornecido e não deve ser modificado)**

O Game Master é o coordenador central que:
* Escuta por agentes via A2A (aguarda 6 agentes se registrarem)
* Gerencia a base de músicas brasileiras
* Distribui e repõe as mãos dos agentes
* Orquestra o fluxo do jogo (rodadas, narrador, votação)
* Calcula pontuações
* Fornece logs detalhados em JSON

**LLM Service (Fornecido e não deve ser modificado)**

O LLM Service é um servidor centralizado que:
* Carrega um único modelo LLM local ( Phi 3.5 Mini Instruct )
* Expõe uma API REST para geração de texto
* Gerencia fila de requisições dos agentes
* Simula o modelo de APIs como OpenAI/Google
* Ele é centralizado pois economiza memória (um modelo vs. vários modelos para cada agente), permite rodar em máquinas com apenas 8GB RAM e é mais realista (mesmo padrão de APIs comerciais).

**Agentes Jogadores (Você Implementa)**

Cada agente é um servidor A2A independente que:
* Comunica-se com o Game Master via A2A (JSON-RPC)
* Consulta o LLM Service via REST
* Mantém seu próprio estado (mão de cartas, histórico)
* Implementa 5 ferramentas (tools) obrigatórias

Espera-se que seu agente ( llm_agent.py ):
* Use a LLM no núcleo semântico de suas decisões, embora seja permitido — e recomendado — usar heurísticas auxiliares para:
	* validar respostas;
	* tratar timeouts;
	* fazer fallback;
	* garantir consistência do protocolo.
* Objetivo: Vencer o jogo consistentemente

### 3.4. Interface dos Agentes (A2A)

Cada agente deve expor 5 ferramentas (tools) que o Game Master irá chamar:

1. `receive_hand`: Recebe as 4 músicas.
```python
@app.tool()
async def receive_hand(hand: List[Dict]) -> Dict:
	"""
	Recebe as 4 músicas do Game Master.
	Args:
		hand: Lista de 4 músicas, cada uma no formato:
			{
				"id": 1,
				"title": "Garota de Ipanema",
				"lyrics": "Olha que coisa mais linda...",
			}
	Returns:
		{"status": "ok", "hand_size": 4}
	"""
```
2. `choose_card`: Escolhe qual carta usar como narrador.
```python
@app.tool()
async def choose_card() -> Dict:
	"""
	Escolhe qual carta da mão usar como narrador.
	(Chamado apenas quando o agente é o narrador)
	Returns:
		{"chosen_card": <música completa>}
	"""
```
3. `send_clue`: Gera uma dica de até 6 palavras.
```python
@app.tool()
async def send_clue(lyrics: str, max_words: int = 6) -> Dict:
	"""
	Gera uma dica de até max_words palavras.
	(Chamado apenas quando o agente é o narrador)
	Args:
		lyrics: A letra da música escolhida
		max_words: Número máximo de palavras permitido
	Returns:
		{"clue": "sua dica aqui (até 6 palavras)"}
	"""
```
4. `select_card_by_clue`: Escolhe a melhor carta baseada na dica (quando não é narrador).
```python
@app.tool()
async def select_card_by_clue(clue: str) -> Dict:
	"""
	Escolhe qual carta da mão melhor representa a dica.
	(Chamado quando o agente NÃO é o narrador)
	Args:
		clue: A dica fornecida pelo narrador
	Returns:
		{"chosen_card": <música completa>}
	"""
```
5. `vote`: Vota em duas opções possíveis da carta do narrador.
```python
@app.tool()
async def vote(clue: str, options: List[Dict], my_chosen_card: Dict) -> Dict:
	"""
	Responsável por votar em quais opções podem ser a carta do narrador.
	É chamada apenas quando o agente NÃO é o narrador.
	Args:
		clue: A dica fornecida pelo narrador
		options: Lista de 6 cartas embaralhadas (0 a 5)
		my_chosen_card: A carta que este agente jogou nesta rodada
	Returns:
		{"votes": [i1, i2]} # i1 e i2 entre 0 a 5; i1 != i2; i1 e i2 não podem ser o índice da sua própria carta
	"""
```
### 3.5. Como Usar o LLM Service

O serviço LLM pode operar em modo real (com um modelo local carregado) ou em modo mock, para testes de infraestrutura e depuração quando não houver modelo disponível.

Endpoint
`POST http://localhost:9000/generate`
`Content-Type: application/json`
**Corpo da Requisição**
```json
{
	"prompt": "Seu prompt aqui",
	"max_tokens": 100,
	"temperature": 0.7,
	"stop": ["\n", "###"]
}
```
**Resposta**
```json
{
	"text": "Texto gerado pela LLM",
	"usage": {
		"prompt_tokens": 45,
		"completion_tokens": 23,
		"total_tokens": 68
	}
}
```

**Exemplo de Uso no seu Agente**
```python
import aiohttp

class MeuAgente:
	def __init__(self):
		self.llm_url = "http://localhost:9000"

	async def llm_generate(self, prompt, max_tokens=100, temperature=0.7):
		async with aiohttp.ClientSession() as session:
			async with session.post(
				f"{self.llm_url}/generate",
				json={
					"prompt": prompt,
					"max_tokens": max_tokens,
					"temperature": temperature
				}
			) as resp:
				result = await resp.json()
				return result["text"]
```

### 3.6. O Que É Fornecido

- `game_master.py`: Coordenador da partida, Gerencia registro de agentes, executa o jogo completo, gera logs em logs/partida_YYYYMMDD_HHMMSS.json.
- `llm_service.py`: Serviço LLM centralizado em FastAPI, expões endpoints /generate (para inferência) e /heath para status, pode rodar em modo real ou mock.
- `random_agent.py`: Implementação completa de um agente aleatório, serve como template e baseline para comparação.
    
- `brazilian_songs.csv`: 256 músicas brasileiras com: id (identificador único), title (titulo da música), artist (Artista/Compositor), lyrics (letra).
    
- `run_game.py`: Script que orquestra toda a execução, pode escolher portas livres automaticamente.
    
- `base_agent.py`: Classe base com cliente LLM integrado, métodos auxiliares para formatação, tratamento de erros básicos.
    
- `fast_a2a.py`: mini camada A2A que implementa: A2AApp para subir o servidor do agente, @tool para marcar tools expostas remotamente, endpoint /rpc com JSON-RPC sobre HTTP.
    
- `render_log_readable.py`: Script auxiliar para leitura de logs.
    

### 3.7. O Que Você Deve Implementar

Agente Estratégico (llm_agent.py) Implemente um agente que combina heurísticas + LLM Service:

```python
from base_agent import BaseAgent
from fasta2a import A2AApp, tool
app = A2AApp(name="LLMAgent")

class LLMAgent(BaseAgent):
	def __init__(self, name: str, llm_url: str):
		super().__init__(name=name, llm_url=llm_url)
		self.hand = []
		self.vote_history = []
		self.clue_history = []
		
	@tool()
	async def receive_hand(self, hand):
		self.hand = list(hand)
		return {"status": "ok", "hand_size": len(self.hand)}
	
	@tool()
	async def choose_card(self):
		# heurística e/ou apoio da LLM
		...

	@tool()
	async def send_clue(self, lyrics: str, max_words: int = 6):
		# uso da LLM + sanitização da resposta
		...
		return {"clue": clue}

	@tool()
	async def select_card_by_clue(self, clue: str):
		# escolha de carta guiada por dica
		...
		return {"chosen_card": chosen_card}

	@tool()
	async def vote(self, clue: str, options: list, my_chosen_card: dict):
		# deve retornar exatamente dois votos distintos
		...
		return {"votes": [i1, i2]}
```


### 3.8. Setup e Execução

#### Requisitos de Hardware
- RAM: 8GB (mínimo) ou 16GB (recomendado)
- CPU: 4+ cores (qualquer processador moderno)
- GPU: Não obrigatória (usaremos CPU com modelo quantizado)
	- Em máquinas sem GPU, modelos pequenos podem apresentar alta latência e respostas inconsistentes. Portanto, espera-se que os agentes usem prompts curtos, parsing robusto, fallback e estratégias de contenção de custo.
- Disco: 5GB livres (para o modelo LLM)
    
#### Instalação

```bash
# 1. Clone o repositório (ou crie seu ambiente)
git clone <url-fornecida-pelo-professor>
cd nota-secreta
# 2. Crie ambiente virtual
python -m venv venv
source venv/bin/activate # Linux/Mac
# ou
venv\Scripts\activate # Windows
# 3. Instale dependências
pip install -r requirements.txt
# 4. Baixe o modelo LLM (Phi-3.5-mini-instruct-GGUF)
wget https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/blob/main/Phi-3.5-mini-instruct-Q4_K_M.gguf
``` 

#### Execução Completa

```bash
# ---------------------------------------------------------------------------
# Comando único para subir toda a arquitetura e executar uma partida completa
# ---------------------------------------------------------------------------
python run_game.py --model Phi-3.5-mini-instruct-Q4_K_M.gguf
# Observação:
# Se as portas padrão estiverem ocupadas, o script pode escolher portas livres automaticamente.
# O script também sobe:
# - o serviço LLM
# - o Game Master
# - 1 agente estratégico
# - 5 agentes aleatórios
# e ao final dispara uma partida completa.
# ----------------------------------------
# Outras opcoes
# --force-mock: nao usa servico da LLM. Apenas simula uso.
# --all-strategic: sobe 6 agentes estrategicos
# --llm-max-concurrency N: usa N cores concorrentemente
# ---------------------------------------------------------------------------
# Execução manual, passo a passo
# ---------------------------------------------------------------------------
# Terminal 1: LLM Service

python llm_service.py --model Phi-3.5-mini-instruct-Q4_K_M.gguf --port 9000 --max-concurrency 1

# Terminal 2: Game Master
python game_master.py --port 8000 --db brazilian_songs.csv --target-score 30 --log-dir
logs
# Terminais 3-8: agentes
python llm_agent.py http://127.0.0.1:8000 --port 8001 --llm-url http://127.0.0.1:9000 --name LLMAgent_1
python random_agent.py http://127.0.0.1:8000 --port 8002 --llm-url
http://127.0.0.1:9000 --name RandomAgent_2
python random_agent.py http://127.0.0.1:8000 --port 8003 --llm-url
http://127.0.0.1:9000 --name RandomAgent_3
python random_agent.py http://127.0.0.1:8000 --port 8004 --llm-url
http://127.0.0.1:9000 --name RandomAgent_4
python random_agent.py http://127.0.0.1:8000 --port 8005 --llm-url
http://127.0.0.1:9000 --name RandomAgent_5
python random_agent.py http://127.0.0.1:8000 --port 8006 --llm-url http://127.0.0.1:9000 --name RandomAgent_6
# Depois de subir os processos manualmente, registre os agentes no Game Master
curl -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" -d '{"name":"LLMAgent_1","url":"http://127.0.0.1:8001","kind":"strategic"}'
curl -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" -d '{"name":"RandomAgent_2","url":"http://127.0.0.1:8002","kind":"random"}'
curl -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" -d '{"name":"RandomAgent_3","url":"http://127.0.0.1:8003","kind":"random"}'
curl -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" -d '{"name":"RandomAgent_4","url":"http://127.0.0.1:8004","kind":"random"}'
curl -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" -d '{"name":"RandomAgent_5","url":"http://127.0.0.1:8005","kind":"random"}'
curl -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" -d '{"name":"RandomAgent_6","url":"http://127.0.0.1:8006","kind":"random"}'
# Por fim, peça ao Game Master para executar a partida
curl -X POST http://127.0.0.1:8000/play
```

O run_game.py é seu amigo. Ele faz tudo isso por você automaticamente:

- Inicia o LLM Service (aguarda modelo carregar)
- Inicia o Game Master
- Inicia instância do seu StrategicAgent
- Inicia 5 instâncias do RandomAgent (fornecido)
- Aguarda o fim do jogo (alguém atinge 30 pontos)
- Exibe placar final e estatísticas
- Encerra todos os processos

### 3.9. Entrega

- Código fonte: llm_agent.py (seu agente criativo) e, talvez, base_agent.py .
* README.md:
	- Instruções de instalação (se diferentes das fornecidas)
	- Como executar seu código
	- Exemplo de saída esperada (pelo menos 2 rodadas completas)
	- Descrição dos prompts e heurísticas implementadas no agente estratégico
	- Dificuldades encontradas e soluções
	- Integrantes do grupo
- Não é necessário entregar
	- O modelo LLM
	- A base de músicas (brazilian_songs.csv)
	 - Logs gerados
    
Componentes fornecidos pelo professor podem ser modificados localmente para testes, mas a avaliação priorizará a compatibilidade da interface com a infraestrutura definida no enunciado.
### 3.10. Avaliação

A avaliação considera quatro critérios: **Corretude** (3 pts), **Robustez** (2 pts), **Protocolo** (1 pt) e **Desempenho Competitivo** (0-4 pts). A pontuação competitiva avalia a consistência do agente contra o agente aleatório e o de referência .

### 3.11. Dicas e Boas Práticas

#### Performance e Otimização

- Mantenha max_tokens baixo (20-35 para respostas curtas)
- Use temperature adequadamente: valor baixo para decisões menos criativas mas mais precisas
- Timeout nas requisições: use asyncio.wait_for com 60 segundos
- Fallback para decisões: se LLM falhar, tenha comportamento padrão (ex: escolher primeira carta)
- Implemente cache para prompts repetidos (ex: mesma música sendo avaliada)

#### Debugging

```python
# Adicione logs no seu agente
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

async def choose_card(self):
	logger.info(f"Escolhendo carta entre {len(self.hand)} opções")
	# ... lógica
	logger.info(f"Carta escolhida: {chosen['title']}")
```

#### Estrutura de Arquivos Esperada

```
nota-secreta/
├── llm_agent.py # seu agente principal
├── base_agent.py # fornecido; pode ser modificado/estendido
├── game_master.py # fornecido; coordena o jogo e gera logs
├── llm_service.py # fornecido; serviço LLM centralizado
├── random_agent.py # fornecido; baseline aleatório
├── run_game.py # fornecido; sobe toda a arquitetura
├── fasta2a.py # fornecido: não modificar
├── render_log_readable.py # fornecido: pode modificar para depuração
├── brazilian_songs.csv # fornecido
├── requirements.txt # fornecido
├── logs/ # gerado
├── tests/ # opcional
└── README.md # sua documentação
```

### Q&A

- Posso usar outro modelo LLM além do Phi3.5-Mini-Instruct ?
	Não, o agente deve funcionar com o serviço LLM centralizado fornecido. Na avaliação, será usado este mesmo modelo.
- Posso usar bibliotecas e ferramentas de apoio ao uso de LLM, além das que foram usadas no código recebido, como LangChain?
	Não, pois isso pode tornar extremamente difícil garantir que todos os agentes que vocês vão entregar rodem no ambiente virtual em que a competição será jogada. Eu prefito manter os requirements restritos ao do ambiente dado para evitar problemas de conflitos entre diferentes requisitos de diferentes equipes.
- E se o LLM Service demorar muito?
	O Game Master usa timeouts para evitar travamentos. Seu agente deve ser robusto a demora do serviço LLM, respostas mal formatadas e ausência de resposta útil. Ou seja, é aconselhável que você implemente estratégias como cache de prompts repetidos, fallback heurístico, parsing tolerante de respostas e logging.
- Preciso implementar concorrência no agente?
	Não, o Game Master chama as tools sequencialmente. Seu agente processa uma requisição por vez.
- Posso modificar o base_agent.py fornecido?
	Sim, pode estender e modificar à vontade. Apenas mantenha a interface das 5 tools .
- Posso usar threads para paralelizar chamadas ao LLM?
	Não é necessário. O LLM Service já gerencia fila. Múltiplas requisições simultâneas serão enfileiradas.
	O serviço LLM centralizado pode serializar ou limitar a concorrência das requisições. Portanto, o agente não deve assumir respostas instantâneas nem paralelismo irrestrito.
- Como será a avaliação competitiva?
	A avaliação competitiva será baseada em um torneio com múltiplas partidas, de modo a reduzir o efeito do acaso de uma única execução. Além dos agentes dos alunos, o torneio também incluirá um agente aleatório (baseline mínimo) e um agente de referência (define patamar de bom desempenho).
	Para cada agente do aluno, será calculado seu desempenho médio no torneio. Também serão calculados:
	- DAA: desempenho médio do agente aleatório;
	- DAR: desempenho médio do agente de referência.
	A pontuação competitiva será atribuída da seguinte forma, considerando comparações estatísticas:
	- 0 pt: agente com desempenho similar ao agente aleatório;
	- 1 pt: agente com desempenho melhor que o aleatório, mas abaixo do agente de referência;
	- 3 pts: agente com desempenho próximo ao agente de referência;
	- 4 pts: agente com desempenho superior ao agente de referência.
	O objetivo dessa avaliação é premiar agentes que apresentem desempenho consistente ao longo de várias partidas.
	Quantos aos recursos usados no torneio, o agente aleatório é exatamente o mesmo que vocês receberam. A coleção de músicas será diferente da que vocês receberam. Ela será, contudo, uma amostra da mesma coleção geral (de cerca de 146 mil letras de músicas brasileiras).
- Como sei se meu agente estratégico é realmente bom?
	Compare a taxa de vitórias dele contra o agente aleatório.
	Compare diferentes heurísticas umas com as outras.
	- Use os logs para entender o desempenho e ter ideias de como melhorar os prompts .
	Além da taxa de vitórias, os logs são úteis para analisar qualidade das dicas, robustez do parsing, uso de fallback e consistência das decisões.
	- Em sistemas multiagente baseados em LLM local, a qualidade do agente depende não apenas do prompt, mas também de decisões de engenharia como timeout, cache, validação, fallback e formato das mensagens.