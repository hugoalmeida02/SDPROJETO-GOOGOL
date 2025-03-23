Relatório Final - Projeto Googol

1. Arquitetura de Software

O sistema Googol é composto por cinco principais componentes distribuídos:

📦 Index Storage Barrel

Servidor que armazena o índice invertido.

Suporta replicacão entre barrels (Reliable Multicast).

Ficheiros utilizados:

words_data_{port}.json: palavras → URLs

urls_data_{port}.json: backlinks (URLs que apontam para outros)

page_text_{port}.json: título e texto de cada URL

🌐 Downloader

Visita páginas web e extrai palavras, links e texto com BeautifulSoup.

Envia palavras e links para um Index Barrel via RPC.

Funciona de forma paralela, consumindo da URLQueue.

🧠 Gateway

Ponto de entrada para os clientes.

Mantém lista de barrels ativos (verificação periódica).

Mede tempo médio de resposta e recolhe estatísticas.

Usa RPC para comunicar com os barrels: search, index, getStats, etc.

👤 Cliente

Interface simples via terminal para interação com o sistema.

Permite:

Introduzir URLs manualmente

Pesquisar termos (com ordenação e snippet)

Consultar backlinks

Ver estatísticas

📋 URL Queue

Integrada na Gateway.

Armazena URLs descobertos para futura indexação.

Consumida pelos downloaders.

2. Replicação do Índice (Reliable Multicast)

Ao receber uma nova entrada, o Index Barrel replica-a para as outras réplicas.

Campo from_multicast evita loops de reenvio.

Se uma réplica estiver offline, a atualização é guardada em pending_updates.

O processo process_pending_updates() trata de reenviar quando possível.

Todos os barrels mantêm a mesma informação (consistência eventual).

3. RPC/RMI - Comunicação Remota

RPCs Implementados

addToIndex(AddToIndexRequest)

putNew(PutNewRequest)

searchWord(SearchWordRequest)

searchTerms(SearchTermsRequest)

getBacklinks(GetBacklinksRequest)

registerIndex(RegisterIndexRequest)

indexInfo()

getStats()

Failover

Gateway tenta outros barrels caso um não responda.

Downloaders também escolhem um novo servidor se a ligação falhar.

4. Distribuição de Tarefas

Este projeto foi desenvolvido individualmente por Hugo, aluno de Engenharia Informática da Universidade de Coimbra.

5. Testes Realizados

Nº

Descrição do Teste

Resultado

1

Indexação de URL manual (via cliente)

✅ Pass

2

Indexação automática de links descobertos

✅ Pass

3

Evitar reindexação de URLs duplicados

✅ Pass

4

Pesquisa de termos com snippets e paginação

✅ Pass

5

Ordenação dos resultados por backlinks

✅ Pass

6

Consulta de backlinks por página

✅ Pass

7

Replicação com 2 barrels em tempo real

✅ Pass

8

Replicação com 1 barrel offline e recuperação posterior

✅ Pass

9

Verificação periódica de barrels ativos pela Gateway

✅ Pass

10

Estatísticas em tempo real na Gateway (pesquisas, tempo, index)

✅ Pass

11

Persistência das estatísticas após crash

✅ Pass

12

Failover do downloader e cliente com servidor offline

✅ Pass

6. Ficheiros de Dados

words_data_{port}.json: índice invertido.

urls_data_{port}.json: backlinks (ligações recebidas).

page_text_{port}.json: texto e título de páginas.

gateway_data_{port}.json: estatísticas persistidas.