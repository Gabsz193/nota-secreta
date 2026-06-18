import os
import glob
import json

def main():
    log_files = glob.glob('logs/*.json')
    if not log_files:
        print("Nenhum log encontrado.")
        return

    latest_log = max(log_files, key=os.path.getmtime)
    print(f"Analisando o log mais recente: {latest_log}")

    with open(latest_log, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Placar final
    print("\nPlacar final:")
    scores = data.get("final_scores", [])
    for i, score in enumerate(scores):
        print(f"  Agente {i+1}: {score} pontos")

    # Analisar turnos do Versao1
    print("\nDicas geradas pelo nosso agente (LLMAgent_1):")
    for rnd in data.get("rounds", []):
        # narrador é um int no json (0 = LLMAgent_1)
        narrador = rnd.get("narrador")
        if narrador == 0:
            clue = rnd.get("clue")
            print(f"  Rodada {rnd.get('round')}: Dica -> '{clue}'")

if __name__ == "__main__":
    main()
