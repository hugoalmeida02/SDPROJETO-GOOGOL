**Relatório Meta 1 - Projeto Googol**

**Hugo Almeida N-2021234629**

**Arquitetura de Software e Comunicação**

A arquitetura segue o modelo distribuído via RPC (gRPC). Cada componente executa uma função distinta:

- **Gateway**: ponto de entrada e monitoramento.
- **Downloaders**: obtêm e analisam páginas.
- **Index Barrels**: armazenam e replicam o índice.
- **URLQueue**: sistema central de agendamento de URLs.

A comunicação entre componentes é feita com chamadas gRPC e estruturas protobuf definidas no ficheiro index.proto. O sistema é tolerante a falhas e suporta crescimento horizontal (múltiplos downloaders e barrels).

**1. Index Storage Barrel**

O Index Storage Barrel é o componente central da arquitetura distribuída do Googol, sendo responsável por armazenar os dados do índice invertido, bem como todas as informações adicionais sobre as páginas (título, citação e backlinks).

**Funções principais:**

- Armazenamento local de palavras e páginas associadas (em words_data\_{host}\_{port}.json).
- Armazenamento de dados de páginas: título, citação curta e URLs que apontam para outras (em urls_data\_{host}\_{port}.json).
- Processamento de pedidos RPC:
  - addToIndexWords: associa uma palavra a um URL.
  - addToIndexLinks: associa metadados (título, citação, links) a um URL.
  - searchWord: devolve páginas com um conjunto de palavras ordenadas por relevância.
  - searchBacklinks: devolve lista de páginas que apontam para uma URL.
  - getFullIndex: devolve o índice completo para sincronização de novas réplicas.

**Replicação automática**

- Usa protocolo de _Reliable Multicast_ sobre RPC para replicar dados para outras réplicas.
- O campo from_multicast evita ciclos infinitos de reenvio.
- As réplicas são obtidas dinamicamente da Gateway (com getIndexBarrels).
- Atualizações que falham são colocadas numa fila pending_updates para reenvio posterior.

**Lógica de sincronização**

- Quando um novo barrel é iniciado, regista-se na Gateway via registerIndexBarrel.
- Tenta sincronizar os dados com uma das réplicas ativas (via getFullIndex).
- Se não houver réplicas, inicia com dados vazios.

**Persistência e segurança**

- Os dados são guardados periodicamente com auto_save().
- A sincronização das réplicas é mantida com check_replicas_periodically().
- Toda a leitura/escrita em ficheiro é feita com threading.Lock() para evitar corrupção concorrente.

**Algoritmo de pesquisa (em searchWord())**

- Divide os termos de pesquisa.
- Faz interseção de URLs que contenham todas as palavras.
- Ordena os resultados com base no número de backlinks recebidos.
- Envia título e snippet (citação) juntamente com o URL.

**2. Gateway**

A Gateway é o ponto central de contacto entre os clientes e os Index Barrels. Atua como monitor de disponibilidade, gestor de estatísticas e reencaminhador de URLs para indexação.

**Funções principais:**

- Registo de Index Barrels com registerIndexBarrel().
- Monitorização de disponibilidade dos barrels com pings periódicos.
- Encaminhamento de pesquisas e pedidos de backlinks para barrels ativos.
- Reencaminhamento de URLs para a fila central (URLQueue).
- Geração de estatísticas em tempo real:
  - Top 10 pesquisas
  - Tamanho dos índices de cada barrel
  - Tempo médio de resposta por servidor

**Detalhes técnicos:**

- Armazena os dados persistentes no ficheiro gateway_data\_{host}\_{port}.json.
- Executa check_index_servers() em background para remover barrels inativos.
- Usa getStats() para disponibilizar as estatísticas agregadas a qualquer cliente.

**3. URL Queue**

A URL Queue é responsável por armazenar os URLs que ainda não foram processados pelos downloaders. Atua como uma fila FIFO partilhada entre os Downloaders e outros componentes que enviam URLs.

**Funções principais:**

- Armazenar URLs em espera para serem visitados.
- Retirar URLs da fila de forma sequencial (takeNext).
- Inserir novos URLs dinamicamente (putNew).
- Persistência automática com gravação periódica.

**Detalhes técnicos:**

- Os URLs são guardados no ficheiro url_queue\_{host}\_{port}.json, para caso de crash.
- Todas as operações de escrita usam threading.Lock() para garantir segurança concorrente.
- A fila é carregada ao iniciar o serviço, ou criada vazia se inexistente.

**4. Downloader**

O downloader atua como web crawler: consome URLs da fila partilhada (URL Queue), extrai informação útil e envia os dados para um Index Barrel ativo.

**Funções principais:**

- Solicita URLs ao servidor de fila (takeNext).
- Faz download da página (usando requests).
- Extrai:
  - Palavras significativas (com mais de 3 letras)
  - Título da página
  - Primeira citação (parágrafo <p>)
  - Links contidos na página
- Seleciona aleatoriamente um Index Barrel ativo fornecido pela Gateway.
- Envia os dados para o Index Barrel através de:
  - addToIndexWords (palavras)
  - addToIndexLinks (título, citação e backlinks)
- Coloca os links extraídos de volta na fila para futura indexação.

**Resiliência e Confiabilidade:**

- Reestabelece ligação à Gateway ou URL Queue se a conexão for perdida.
- Garante continuidade de execução mesmo com falhas momentâneas.

**5. Cliente (Interface do Utilizador)**

O ficheiro client.py implementa um cliente simples baseado em menu, permitindo a interação direta com o sistema Googol através da Gateway.

**Funcionalidades principais:**

- Adicionar URL à queue
  - Envia um URL manualmente para a fila (usando putNew).
- Pesquisar palavras
  - Envia termos para a Gateway, que delega a pesquisa num Index Barrel.
  - Mostra até 10 resultados por página, com título, URL e citação.
- Pesquisar backlinks
  - Consulta os URLs que apontam para uma página específica.
- Consultar estatísticas
  - Mostra as 10 pesquisas mais comuns.
  - Lista os Index Barrels ativos, com tamanho de índice e tempo médio de resposta.

**Resiliência:**

- Se perder ligação com a Gateway, tenta reconectar automaticamente.
- Valida URLs antes de os adicionar à fila.

**Replicação do Índice (Reliable Multicast)**

Ao receber uma entrada nova, o Index Barrel propaga-a às réplicas através de RPCs paralelos. Se alguma réplica estiver offline, a atualização falhada é colocada numa fila pending_updates. Um processo em background tenta reenviar periodicamente.

Cada mensagem de atualização inclui um campo from_multicast para evitar loops de replicação entre servidores. As réplicas sincronizam os dados iniciais através do método getFullIndex.

**Comunicação RPC e Failover**

Todos os métodos gRPC são definidos no index.proto e incluem:

- addToIndexWords, addToIndexLinks, searchWord, searchBacklinks, getStats, putNew, etc.
  Em caso de falha numa chamada RPC (ex: Connection reset), os clientes e downloaders tentam reconectar ou usar um servidor alternativo. O sistema garante robustez mesmo com falhas intermitentes.

**Interface. proto**

O ficheiro index.proto define a API gRPC que interliga todos os componentes do Googol. Este define o serviço Index e as mensagens utilizadas.

**Mensagens principais**

- **PutNewRequest**: recebe um URL para colocar na fila.
- **AddToIndexRequestWords**: adiciona uma palavra a um URL.
- **AddToIndexRequestLinks**: adiciona título, citação e links associados a um URL.
- **SearchWordRequest / Response**: realiza pesquisa por palavras.
- **SearchBacklinksRequest / Response**: devolve páginas que apontam para um URL.
- **FullIndexResponse**: usado para sincronizar dados entre réplicas.
- **IndexBarrelRequest / ValidRegister**: registo de servidores na gateway.
- **IndexBarrelInfo**: devolve lista de barrels ativos.
- **SystemStats / BarrelStats**: estatísticas agregadas.

**Organização das estruturas**

As mensagens estão organizadas de forma modular:

- WordInfo: informação individual de uma página (url, título, citação).
- IndexEntry: estrutura genérica usada na sincronização (param0, param1).
- BarrelStats: inclui endereço, tamanho do índice e tempo médio de resposta.
