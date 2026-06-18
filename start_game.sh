#!/bin/bash

echo "=========================================="
echo "Iniciando a partida de Nota Secreta..."
echo "=========================================="

# Verifica se o ambiente virtual existe antes de ativar
if [ -d "venv" ]; then
    echo "Ativando o ambiente virtual..."
    source venv/bin/activate
else
    echo "Aviso: Ambiente virtual 'venv' não encontrado."
    echo "Se você não configurou as dependências globais, o script pode falhar."
fi

echo "Executando o jogo com o modelo Phi-3.5-mini-instruct-Q4_K_M.gguf..."
python3 run_game.py --model Phi-3.5-mini-instruct-Q4_K_M.gguf

echo "=========================================="
echo "Jogo finalizado! Analisando os resultados..."
echo "=========================================="
python3 analyze_logs.py
