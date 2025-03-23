**README - Projeto Googol**

Este projeto implementa um motor de busca distribuído, com indexação automática, replicação de dados e pesquisa de páginas Web. Desenvolvido em Python, com comunicação baseada em gRPC.

**Requisitos**

Python 3.10+

Bibliotecas:

- grpcio
- grpcio-tools
- requests
- beautifulsoup4

Instalar dependências com:

pip install -r requirements.txt

**Estrutura do Projeto**

Googol/
├── protos/
    ├── generate-gRPC-code.sh
    └── index.proto
├── client.py               # Interface do utilizador
├── downloader.py           # Web crawler
├── gateway.py              # Servidor Gateway
├── indexServer.py          # Index Storage Barrel
├── url_queue.py # Url Queue
├── requirements.txt
├── Report.md
└── README.md

**Execução Passo a Passo**

1. Gerar ficheiros gRPC
   python -m grpc_tools.protoc -I. --python_out=../ --grpc_python_out=../ index.proto

2. Iniciar a Gateway
   python gateway.py --host_gateway localhost --port_gateway 8190 --host_url_queue localhost --port_url_queue 8180

3. Iniciar a Url_queue
   python url_queue.py --host_url_queue localhost --port_url_queue 8180

4. Iniciar um ou mais Index Barrels
   python indexServer.py --host localhost --port 8123 --host_gateway localhost --port_gateway 8190
   python indexServer.py --host localhost --port 8124 --host_gateway localhost --port_gateway 8190

5. Iniciar os Downloaders (um ou mais)
   python downloader.py --host_gateway localhost --port_gateway 8190 --host_url_queue localhost --port_url_queue 8180

6. Iniciar o Cliente
   python client.py --host_gateway localhost --port_gateway 8190

Os valores para execução são só exemplos.

**Funcionalidades Disponíveis**

- Inserir novo URL para indexação manual.
- Indexação automática de links extraídos.
- Pesquisa por termos (com snippet, paginação e ordenação por importância).
- Consulta de backlinks (páginas que apontam para um URL).
- Consulta de estatísticas em tempo real:

1. Top 10 pesquisas
1. Barrels ativos com tamanhos
1. Tempo médio de resposta por Barrel

Autor
Desenvolvido por Hugo Almeida, aluno de Engenharia Informática - Universidade de Coimbra.
