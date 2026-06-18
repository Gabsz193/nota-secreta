#!/bin/bash

echo "Iniciando o download do modelo Phi-3.5-mini-instruct-Q4_K_M.gguf (Aprox. 2.4 GB)..."
echo "Isso pode demorar alguns minutos dependendo da sua conexão com a internet."

wget -q --show-progress -O Phi-3.5-mini-instruct-Q4_K_M.gguf https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf

echo "Download concluído!"
