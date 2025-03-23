README - Projeto Googol

Este projeto implementa um motor de busca distribuído, com indexação automática, replicação de dados e pesquisa de páginas Web. Desenvolvido em Python, com comunicação baseada em gRPC.

⚙️ Requisitos

Python 3.10+

Bibliotecas:

grpcio

grpcio-tools

requests

beautifulsoup4

Instalar dependências com:

pip install -r requirements.txt

Ou manualmente:

pip install grpcio grpcio-tools requests beautifulsoup4

📦 Estrutura do Projeto

Googol/
├── client.py               # Interface do utilizador
├── downloader.py           # Web crawler
├── gateway.py              # Servidor Gateway
├── indexServer.py          # Index Storage Barrel
├── index.proto             # Definições gRPC
├── words_data_{port}.json  # Índice invertido (por Barrel)
├── urls_data_{port}.json   # Ligações recebidas (por Barrel)
├── page_text_{port}.json   # Texto e título das páginas
├── gateway_data_{port}.json # Estatísticas persistidas
├── requirements.txt
└── README.md

🚀 Execução Passo a Passo

1. Gerar ficheiros gRPC

Se alterares index.proto:

python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. index.proto

2. Iniciar a Gateway

python gateway.py

3. Iniciar um ou mais Index Barrels

python indexServer.py --port=8183
python indexServer.py --port=8184

4. Iniciar os Downloaders (um ou mais)

python downloader.py

5. Iniciar o Cliente

python client.py

🧪 Funcionalidades Disponíveis

Inserir novo URL para indexação manual.

Indexação automática de links extraídos.

Pesquisa por termos (com snippet, paginação e ordenação por importância).

Consulta de backlinks (páginas que apontam para um URL).

Estatísticas em tempo real:

Top 10 pesquisas

Barrels ativos com tamanhos

Tempo médio de resposta por Barrel

🛠️ Dados Persistidos

Os dados de indexação e estatísticas são guardados em ficheiros .json por porta, para garantir recuperação após falhas.

👤 Autor

Desenvolvido por Hugo, aluno de Engenharia Informática - Universidade de Coimbra.
