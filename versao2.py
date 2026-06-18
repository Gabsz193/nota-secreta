import random
import re
import logging
import string
from typing import Any, Dict, List

from base_agent import BaseAgent
from fasta2a import tool

logger = logging.getLogger(__name__)

STOPWORDS_PT = {
    "a", "o", "as", "os", "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "e", "é", "que", "um", "uma", "uns", "umas", "por", "para",
    "com", "sem", "como", "mas", "ou", "se", "seu", "sua", "seus", "suas",
    "meu", "minha", "meus", "minhas", "teu", "tua", "teus", "tuas", "isso",
    "isto", "aquilo", "ele", "ela", "eles", "elas", "eu", "nós", "vós", "tu",
    "você", "vocês", "não", "sim", "já", "mais", "muito", "pouco", "tem",
    "são", "ser", "foi", "era", "está", "estão", "este", "esta", "estes", "estas"
}

def remove_stopwords(text: str) -> str:
    words = text.split()
    filtered = [w for w in words if w.lower() not in STOPWORDS_PT]
    return " ".join(filtered)

def shorten_lyrics(lyrics: str) -> str:
    # 1. Tudo em minusculo
    lyrics = lyrics.lower()
    
    return lyrics

    # 2. Retirar pontuacao
    for p in string.punctuation:
        lyrics = lyrics.replace(p, " ")
        
    lines = lyrics.split('\n')
    
    # 3. Remover linhas repetidas
    unique_lines = []
    seen = set()
    for line in lines:
        line_clean = line.strip()
        if line_clean and line_clean not in seen:
            seen.add(line_clean)
            unique_lines.append(line_clean)
            
    # 4. linha sim, linha nao (0, 2, 4...)
    short_lines = [unique_lines[i] for i in range(len(unique_lines)) if i % 2 == 0]
    short_text = "\n".join(short_lines)
    
    # 5. Remover stopwords
    return remove_stopwords(short_text)

class Versao2(BaseAgent):
    def __init__(self, name: str, llm_url: str):
        super().__init__(name=name, llm_url=llm_url, request_timeout=60.0)
        self.hand = []

    @tool()
    async def receive_hand(self, hand: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.hand = list(hand)
        return {"status": "ok", "hand_size": len(self.hand)}

    @tool()
    async def choose_card(self) -> Dict[str, Any]:
        if not self.hand:
            raise RuntimeError("Hand is empty")
        
        print("Encurtando musicas e escolhendo carta com LLM...")

        opcoes = ""
  
        for i, song in enumerate(self.hand):
            short_lyrics = shorten_lyrics(song.get("lyrics", ""))
            short_lyrics = " ".join(short_lyrics.split()[:50])
            opcoes += f"Opcao {i}: {short_lyrics}\n\n"
        
        prompt = (
            "Contexto:\n"
            "Voce eh um jogador de Dixit jogando com musicas.\n"
            "Instrucao:\n"
            "Dadas as opções de música, qual destas possui as expressoes mais genéricas que podem ser "
            "representadas por sinonimos criativos e ideias que remetam ao sentimento ou elemento contido na musica? "
            "Tenha em mente que o seu objetivo é evitar com que todos ou nenhum jogador acerte.\n"
            "Entrada:\n"
            f"\n{opcoes}\n\n"
            "Formato de saída:\n"
            "Responda APENAS com o numero da opcao (0, 1, 2 ou 3).\n"
            "Exemplo de resposta:\n"
            "0\n"
            "1\n"
            "2\n"
            "3\n"
            "Saída:\n"
        )

        print(f"--- NARRADOR: PROMPT ESCOLHA A CARTA ---\n{prompt}\n--------------------------------------")

        chosen_idx = random.randrange(len(self.hand))
        try:
            raw = await self.llm_generate(prompt, max_tokens=10, temperature=0.2)
            print(f"--- NARRADOR: RESPOSTA ESCOLHA A CARTA ---\n{raw}\n----------------------------------------")
            numbers = re.findall(r'[0-3]', raw)
            if numbers:
                chosen_idx = int(numbers[0])
                print(f"LLM escolheu a carta: {chosen_idx}")
            else:
                logger.warning(f"LLM nao retornou indice valido, usando fallback: {raw}")
        except Exception as e:
            logger.error(f"Erro na LLM em choose_card: {e}")

        print(f"--- NARRADOR: CARTA ESCOLHIDA ---\n{self.hand[chosen_idx]}\n----------------------------------")

        return {"chosen_card": self.hand[chosen_idx]}

    @tool()
    async def send_clue(self, lyrics: str, max_words: int = 6) -> Dict[str, Any]:
        short_lyrics = " ".join(lyrics.split()[:100])
        prompt = (
            "Contexto:\n"
            "Voce eh um jogador de Dixit jogando com musicas.\n"
            "Instrução:\n"
            f"Dado a letra da música, forneça uma dica usando no maximo {max_words} palavras.\n"
            "Lembre-se: a dica deve ser criativa, mas não pode ser nem muito difícil nem muito fácil de adivinhar. Por exemplo, "
            "pegue o elemento principal da canção e substitua por algo relacionado a ele. Se o elemento for algo muito específico "
            "não use-o, pegue outro. Tente buscar por coisas genéricas para poder usar a dica.\n"
            "NÃO COLOQUE PALAVRAS QUE ESTEJAM NA MUSICA, PRINCIPALMENTE AS MAIS ÓBVIAS.\n"
            "Entrada:\n"
            f"\n{short_lyrics}\n\n"
            "Formato de saída:\n"
            "Responda APENAS e UNICAMENTE com a dica.\n"
            "Saída:\n"
        )

        print(f"--- NARRADOR: PROMPT SEND_CLUE ---\n{prompt}\n---------------------------------")

        clue = "coisa estranha"
        raw_response = ""
        try:
            raw = await self.llm_generate(
                prompt, max_tokens=15, temperature=0.5, stop=["\n", "###", "Letra:"]
            )
            raw_response = raw
            print(f"--- NARRADOR: RESPOSTA SEND_CLUE ---\n{raw}\n------------------------------------")
            raw = raw.strip().replace('"', '').replace('.', '')
            if raw:
                clue_sanitized = self._sanitize_clue(raw, max_words=max_words, lyrics=lyrics)
                if clue_sanitized:
                    clue = clue_sanitized
                else:
                    clue = " ".join(raw.split()[:max_words])
                
                if not clue.strip() or len(clue) <= 1:
                    clue = "coisa estranha"
        except Exception as e:
            logger.error(f"Erro na LLM em send_clue: {e}")

        if clue == "coisa estranha":
            logger.warning(f"[DEBUG FALLBACK] send_clue gerou 'coisa estranha'. Resposta raw original da LLM: '{raw_response}'")
            
        return {"clue": clue}

    @tool()
    async def select_card_by_clue(self, clue: str) -> Dict[str, Any]:
        if not self.hand:
            raise RuntimeError("Hand is empty")

        opcoes = ""

        for i, song in enumerate(self.hand):
            short_lyrics = shorten_lyrics(song.get("lyrics", ""))
            short_lyrics = " ".join(short_lyrics.split()[:40])
            opcoes += f"Opcao {i}: {short_lyrics}\n\n"

        prompt = (
            "Contexto:\n"
            "Voce e um jogador de Dixit avaliando músicas para escolher qual mais se encaixa em uma dica.\n"
            "Instrucao:\n"
            "Dada uma dica, escolha qual das opções de música mais se encaixam na descrição dessa dica.\n"
            "Seu objetivo é enganar os outros jogadores que terão que escolher a sua carta. Se a dica for sobre um objeto "
            "escolha uma música que pode conter esse objeto. Se a dica for sobre um lugar, escolha uma música que se "
            "passa naquele lugar.\n"
            "Entrada:\n"
            f"Dica: '{clue}'\n\n"
            f"Opcoes:\n\n{opcoes}\n\n"
            "Formato de saída:\n"
            "Responda APENAS com o numero (0, 1, 2 ou 3).\n"
            "Exemplos de saída:\n"
            "0\n"
            "1\n"
            "2\n"
            "3\n"
            "Saída:\n"
        )
        
        

        print(f"--- JOGADOR: PROMPT SELECT_CARD ---\n{prompt}\n-----------------------------------")

        chosen_idx = random.randrange(len(self.hand))
        try:
            raw = await self.llm_generate(prompt, max_tokens=10, temperature=0.2)
            print(f"--- JOGADOR: RESPOSTA SELECT_CARD ---\n{raw}\n--------------------------------------")
            numbers = re.findall(r'[0-3]', raw)
            if numbers:
                chosen_idx = int(numbers[0])
        except Exception as e:
            logger.error(f"Erro na LLM em select_card_by_clue: {e}")

        return {"chosen_card": self.hand[chosen_idx]}

    @tool()
    async def vote(self, clue: str, options: List[Dict[str, Any]], my_chosen_card: Dict[str, Any]) -> Dict[str, Any]:
        my_idx = next(i for i, opt in enumerate(options) if opt["id"] == my_chosen_card["id"])
        
        opcoes = ""

        for i, opt in enumerate(options):
            if i == my_idx:
                continue
            short_lyrics = shorten_lyrics(opt.get("lyrics", ""))
            short_lyrics = " ".join(short_lyrics.split()[:30])
            opcoes += f"Opcao {i}: {short_lyrics}\n\n"

        
        prompt = (
            "Contexto:\n"
            f"Voce e um jogador de Dixit votando nas musicas dos adversarios.\n"
            "Instrução:\n"
            "Dada a dica e as opções quais são as duas melhores que se encaixam com o conceito original da dica. Lembrando que há cartas escolhidas"
            " propositalmente com ideias parecidas por outros jogadores. Existe apenas uma correta. Quando for avaliar, se a dica possuir todas as palavras "
            "da opção, marque essa. Se for algumas, suspeite."
            "Entrada:\n"
            f"Dica: '{clue}'\n"
            f"Opções: \n{opcoes}\n\n"
            "Formato de saída:\n"
            "Responda com dois números inteiros separados por vírgula: n, m\n"
            "Exemplo de Respostas:\n"
            "1, 2\n"
            "3, 1\n"
            "0, 2\n"
            "Saída:\n"
        )

        print(f"--- JOGADOR: PROMPT VOTE ---\n{prompt}\n----------------------------")

        possible_votes = [i for i in range(len(options)) if i != my_idx]
        random.shuffle(possible_votes)
        votes = possible_votes[:2]

        try:
            raw = await self.llm_generate(prompt, max_tokens=15, temperature=0.2)
            print(f"--- JOGADOR: RESPOSTA VOTE ---\n{raw}\n------------------------------")
            numbers = [int(n) for n in re.findall(r'[0-5]', raw) if int(n) != my_idx]
            
            unique_nums = []
            for n in numbers:
                if n not in unique_nums:
                    unique_nums.append(n)
            
            if len(unique_nums) >= 2:
                votes = unique_nums[:2]
            elif len(unique_nums) == 1:
                votes[0] = unique_nums[0]
                votes[1] = next(i for i in possible_votes if i != votes[0])
        except Exception as e:
            logger.error(f"Erro na LLM em vote: {e}")

        return {"votes": votes}
