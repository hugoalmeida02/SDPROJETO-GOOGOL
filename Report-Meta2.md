Relatório Meta 2 - Projeto Googol

Hugo Almeida N-2021234629

A Meta 2 consistiu na construção de uma interface Web interativa que comunica com a infraestrutura da Meta 1 via RPC. O projeto foi expandido com foco na interoperabilidade, usabilidade, e integração com serviços externos, seguindo uma arquitetura MVC com FastAPI.

**Interface Web (FastAPI + Jinja2)**

A interface Web foi desenvolvida com FastAPI e Jinja2 templates, apresentando as seguintes vistas:
- Página inicial: permite escolher entre pesquisa por palavra, backlinks ou adicionar URL.
- Página de resultados: mostra resultados paginados com snippet e ordenação por relevância.
- Backlinks: mostra as páginas que apontam para determinado URL.
- Página de falha: utilizada quando ocorre uma perda de ligação com a Gateway.

Todos os estilos e scripts encontram-se separados em /static, assegurando responsividade e boa experiência de utilização.
- Funcionalidades disponíveis via Web:
- Pesquisa por termos com paginação e snippet.
- Pesquisa de backlinks.
- Inserção manual de URLs.
- Geração de análise contextual via OpenAI.
- Indexação de top stories do Hacker News.
- Estatísticas do sistema em tempo real via WebSockets.

**Integração com APIs REST**

Hacker News
- Utilização da API pública para obter as top stories.
- Filtragem por título com base nos termos pesquisados.
- Indexação automática dos URLs relevantes.

OpenAI
- Utilização da API chat (GPT-4o) para gerar análises baseadas nos termos pesquisados.
- A autenticação usa variável de ambiente (.env) e o módulo pydantic-settings para leitura segura.

**Comunicação WebSocket**

Os WebClients estabelecem uma ligação ws:// com o servidor.
O WebServer recebe estatísticas agregadas da Gateway e faz broadcast para os clientes conectados.

A atualização é feita apenas quando há alteração (evita polling). Os dados incluem:
- Top 10 pesquisas
- Lista de barrels ativos (IP e tamanho do índice)
- Tempo médio de resposta

**Arquitetura Web (MVC)**

Model: webserver.py — comunica via gRPC com a Gateway
View: templates/ e static/
Controller: routes.py — define as rotas Web e WebSocket

O ficheiro main.py inicializa tanto o servidor FastAPI como o servidor gRPC (em background).

**Novos ficheiros e organização**

A estrutura do projeto foi reorganizada:
- Ficheiros gRPC (index_pb2) movidos para googol/index_pb2/.
- Ficheiros persistentes (índices, queue, gateway) estão agora em googol_grcp/files/.
- Novo ficheiro .env adicionado.

**Melhorias na Resiliência**

Reconexão automática com a Gateway caso esta reinicie.
Página falha.html apresentada ao utilizador final se uma pesquisa falhar.
web_server e send_statistics agora persistido no ficheiro da Gateway para garantir consistência após falhas.

**Distribuição de Tarefas**

Este projeto foi desenvolvido individualmente por Hugo Almeida, estudante de Engenharia Informática da Universidade de Coimbra. Todas as fases, desde a análise, desenho da arquitetura, implementação, testes e documentação foram realizadas pelo autor.

**Testes Realizados**

A seguinte tabela resume os testes realizados para validar o funcionamento do sistema Googol:

| Nº  | Descrição do Teste                              | Componente(s) envolvido(s) | Resultado Esperado                               | Resultado |
| --- | ----------------------------------------------- | -------------------------- | ------------------------------------------------ | --------- |
| 1   | Ligação do WebClient ao WebSocket               | WebServer                  | Recebe estatísticas em tempo real                | Pass      |
| 2   | Análise OpenAI com termos variados              | WebServer + OpenAI         | Texto gerado com sucesso                         | Pass      |
| 3   | Indexação das top stories com termos comuns     | WebServer + Hacker News    | URLs indexados corretamente                      | Pass      |
| 4   | Simulação de perda de Gateway                   | WebServer + Gateway        | Página de falha apresentada                      | Pass      |
| 5   | Reinício da Gateway                             | Gateway                    | Reenvio de estatísticas garantido                | Pass      |


**Conclusão**

A Meta 2 ampliou o projeto Googol com uma interface web robusta, integrando funcionalidades modernas de pesquisa com APIs externas e comunicação em tempo real.
Todos os objetivos definidos foram atingidos com sucesso, mantendo a modularidade, escalabilidade e resiliência do sistema. A experiência do utilizador foi fortemente melhorada com a adoção de WebSockets, layout responsivo e feedback informativo em caso de erro.
O sistema está pronto para ser estendido com novas funcionalidades (ex: autenticação, favoritos, histórico) e demonstra uma base sólida para aplicações Web distribuídas baseadas em RPC.


Desenvolvido por Hugo Almeida, N.º 2021234629 — Engenharia Informática, Universidade de Coimbra