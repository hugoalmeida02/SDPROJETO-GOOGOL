**README - Projeto Googol**

Motor de busca distribuído com interface Web, pesquisa por palavras, backlinks, estatísticas em tempo real e integração com APIs externas (OpenAI e Hacker News). Desenvolvido em Python com gRPC e FastAPI.

**Requisitos**

Python 3.10+

Principais bibliotecas usadas:

- pydantic — gestão de variáveis ambiente
- fastapi, uvicorn — interface Web
- requests, beautifulsoup4, jinja2 — scraping e rendering
- openai — integração com GPT
- grpcio, grpcio-tools — comunicação RPC

Instalar dependências com:

pip install -r requirements.txt

**Estrutura do Projeto**

Googol/
├── app
│      ├── index_pb2/                     
│      │       ├── index_pb2.py
│      │       └── index_pb2_grpc.py
│      ├── googol_grcp/
│      │   ├── client.py
│      │   ├── downloader.py
│      │   ├── gateway.py
│      │   ├── indexServer.py
│      │   ├── url_queue.py
│      │   └── files/                         
│      │       ├── urls_data_*.json
│      │       ├── words_data_*.json
│      │       ├── url_queue_*.json
│      │       └── gateway_data_*.json
│      └── googol_web/
│          ├── main.py
│          ├── webserver.py
│          ├── context.py
│          ├── config.py
│          ├── routes.py
│          ├── websockets.py
│          ├── utils/
│          │   ├── hackernews_api.py
│          │   └── openai_api.py
│          ├── templates/
│          │   ├── index.html
│          │   ├── results.html
│          │   ├── backlinks.html
│          │   └── falha.html
│          └── static/
│             ├── index.js
│             ├── results.js
│             ├── websocket.js
│             └── style.css
├── .env.example
├── requirements.txt
├── Report.md
└── README.md

**Execução Passo a Passo**

Os ficheiros `index_pb2.py` e `index_pb2_grpc.py` já estão incluídos no projeto, na pasta `app/index_pb2`. **Não é necessário gerar os protos manualmente.**

1. Iniciar a Gateway
   python -m app.googol_grcp.gateway --host_gateway localhost --port_gateway 8190 --host_url_queue localhost --port_url_queue 8180

2. Iniciar a Url_queue
   python -m app.googol_grcp.url_queue --host_url_queue localhost --port_url_queue 8180

3. Iniciar um ou mais Index Barrels
   python -m app.googol_grcp.indexServer --host localhost --port 8123 --host_gateway localhost --port_gateway 8190
   python -m app.googol_grcp.indexServer --host localhost --port 8124 --host_gateway localhost --port_gateway 8190

4. Iniciar os Downloaders (um ou mais)
   python -m app.googol_grcp.downloader --host_gateway localhost --port_gateway 8190 --host_url_queue localhost --port_url_queue 8180

5. Iniciar o Cliente (Opcional)
   python -m app.googol_grcp.client --host_gateway localhost --port_gateway 8190

6. Iniciar o Webserver e Api
   python -m app.googol_web.main --host_api localhost --port_api 8080 --host_webserver localhost --port_webserver 8888 --host_gateway localhost --port_gateway 8190

7. Aceder em: http://localhost:8080 (host_api + : + port_api)

Os valores para execução são só exemplos.

**Funcionalidades Disponíveis**

- Inserir novo URL para indexação manual.
- Pesquisa de backlinks: páginas que apontam para um determinado URL.
- Pesquisa por termos (com snippet, paginação e ordenação por importância).
- Consulta de backlinks (páginas que apontam para um URL).
- Consulta de estatísticas em tempo real via WebSocket:
   1. Top 10 pesquisas.
   2. Barrels ativos com tamanhos.
   3. Tempo médio de resposta por Barrel.
- Indexação automática de links encontrados.
- Análise contextual com OpenAI baseada nos termos da pesquisa.
- Indexação de top stories do Hacker News que contêm os termos.
- Página de falha dedicada apresentada em caso de perda de ligação com a Gateway.

**Autor**
Desenvolvido por Hugo Almeida, aluno de Engenharia Informática - Universidade de Coimbra.
