import argparse
from fasta2a import A2AApp
from versao2 import Versao2

app = A2AApp(name="Versao1Agent")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_master_url")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--llm-url", default="http://127.0.0.1:9000")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    # O nome por padrao sera "versao 1" se nao especificado, mas o GM pode passar outro nome
    agent_name = args.name or f"Versao1_{args.port}"
    
    agent = Versao2(name=agent_name, llm_url=args.llm_url)
    app.register(agent)
    app.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
