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

class Versao1(BaseAgent):
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
        
        logger.info("Encurtando musicas e escolhendo carta com LLM...")
        prompt = "Analise as seguintes 4 letras de musica encurtadas:\n\n"
        for i, song in enumerate(self.hand):
            short_lyrics = shorten_lyrics(song.get("lyrics", ""))
            short_lyrics = " ".join(short_lyrics.split()[:50])
            prompt += f"Opcao {i}:\n{short_lyrics}\n\n"
        
        prompt += (
            "Qual destas 4 musicas possui as expressoes mais unicas que podem ser "
            "substituidas por bons sinonimos? "
            "Responda APENAS com o numero da opcao (0, 1, 2 ou 3)."
        )

        chosen_idx = random.randrange(len(self.hand))
        try:
            raw = await self.llm_generate(prompt, max_tokens=10, temperature=0.2)
            numbers = re.findall(r'[0-3]', raw)
            if numbers:
                chosen_idx = int(numbers[0])
                logger.info(f"LLM escolheu a carta: {chosen_idx}")
            else:
                logger.warning(f"LLM nao retornou indice valido, usando fallback: {raw}")
        except Exception as e:
            logger.error(f"Erro na LLM em choose_card: {e}")

        return {"chosen_card": self.hand[chosen_idx]}

    @tool()
    async def send_clue(self, lyrics: str, max_words: int = 6) -> Dict[str, Any]:
        short_lyrics = " ".join(lyrics.split()[:100])
        prompt = (
            f"Voce e um jogador de Dixit jogando com musicas. "
            f"Descreva o TEMA dessa musica usando no maximo {max_words} palavras. "
            "Nao repita palavras do texto nem o titulo. Responda APENAS a dica curta e nada mais.\n\n"
            f"Letra:\n{short_lyrics}\n\n"
            "Dica:"
        )

        logger.info(f"--- NARRADOR: PROMPT SEND_CLUE ---\n{prompt}\n---------------------------------")

        clue = "coisa estranha"
        raw_response = ""
        try:
            raw = await self.llm_generate(
                prompt, max_tokens=15, temperature=0.3, stop=["\n", "###", "Letra:"]
            )
            raw_response = raw
            logger.info(f"--- NARRADOR: RESPOSTA SEND_CLUE ---\n{raw}\n------------------------------------")
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

        prompt = (
            f"Voce e um jogador de Dixit avaliando musicas.\n"
            f"A dica e: '{clue}'\n\n"
            "Qual das 4 musicas abaixo melhor reflete o SENTIMENTO ou a METAFORA dessa dica? "
            "Regras de deducao:\n"
            "1. Se a dica for de algo triste, elimine musicas felizes (e vice-versa).\n"
            "2. Nao escolha uma musica so porque ela repete uma palavra exata da dica.\n\n"
            "Responda APENAS com o numero (0, 1, 2 ou 3).\n\n"
        )
        
        for i, song in enumerate(self.hand):
            short_lyrics = shorten_lyrics(song.get("lyrics", ""))
            short_lyrics = " ".join(short_lyrics.split()[:40])
            prompt += f"Opcao {i}: {short_lyrics}\n\n"

        logger.info(f"--- JOGADOR: PROMPT SELECT_CARD ---\n{prompt}\n-----------------------------------")

        chosen_idx = random.randrange(len(self.hand))
        try:
            raw = await self.llm_generate(prompt, max_tokens=10, temperature=0.2)
            logger.info(f"--- JOGADOR: RESPOSTA SELECT_CARD ---\n{raw}\n--------------------------------------")
            numbers = re.findall(r'[0-3]', raw)
            if numbers:
                chosen_idx = int(numbers[0])
        except Exception as e:
            logger.error(f"Erro na LLM em select_card_by_clue: {e}")

        return {"chosen_card": self.hand[chosen_idx]}

    @tool()
    async def vote(self, clue: str, options: List[Dict[str, Any]], my_chosen_card: Dict[str, Any]) -> Dict[str, Any]:
        my_idx = next(i for i, opt in enumerate(options) if opt["id"] == my_chosen_card["id"])
        
        prompt = (
            f"Voce e um jogador de Dixit votando nas musicas dos adversarios.\n"
            f"A dica e: '{clue}'\n\n"
            "Quais das opcoes abaixo MELHOR refletem o sentimento dessa dica? "
            "Regras:\n"
            "1. Se a dica for triste, elimine opcoes felizes.\n"
            "2. Desconfie de opcoes que apenas repetem palavras da dica.\n"
            f"Me diga os 2 melhores indices, separados por virgula. Nao escolha a opcao {my_idx}.\n\n"
        )
        
        for i, opt in enumerate(options):
            short_lyrics = shorten_lyrics(opt.get("lyrics", ""))
            short_lyrics = " ".join(short_lyrics.split()[:30])
            prompt += f"Opcao {i}: {short_lyrics}\n\n"

        logger.info(f"--- JOGADOR: PROMPT VOTE ---\n{prompt}\n----------------------------")

        possible_votes = [i for i in range(len(options)) if i != my_idx]
        random.shuffle(possible_votes)
        votes = possible_votes[:2]

        try:
            raw = await self.llm_generate(prompt, max_tokens=15, temperature=0.2)
            logger.info(f"--- JOGADOR: RESPOSTA VOTE ---\n{raw}\n------------------------------")
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
