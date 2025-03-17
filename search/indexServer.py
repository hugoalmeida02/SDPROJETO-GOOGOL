from concurrent import futures
import grpc
import index_pb2
import index_pb2_grpc
from google.protobuf import empty_pb2
import threading
import argparse
import queue
import sqlite3

SAVE_INTERVAL = 10
REPLICAS = ["localhost:8183", "localhost:8184"]


class IndexServicer(index_pb2_grpc.IndexServicer):
    def __init__(self, port):
        self.port = port
        self.lock = threading.Lock()
        self.pending_updates = queue.Queue()
        self.db_file = f"index_barrel_{port}.db"
        self.setup_database()
        # self.sync_with_existing_replicas()
        

    def registerIndex(self):
        gateway_channel = grpc.insecure_channel("localhost:8190")
        gateway_stub = index_pb2_grpc.IndexStub(gateway_channel)
        try:
            response = gateway_stub.registerIndexBarrel(index_pb2.IndexBarrelRequest(ip=f"localhost:{self.port}"))
            if response.valid:
                print("Server registado com sucesso")
                return True
            else:
                print("Nao foi possivel registar server")
                return False
        except grpc.RpcError:
            print("Erro ao registar server. Gateway indisponivel")
            return False
            
            
    # def replicate_update(self, word, url):
    #     def send_update(replica):
    #         if replica == f"localhost:{self.port}":
    #             return
    #         try:
    #             with grpc.insecure_channel(replica) as channel:
    #                 stub = index_pb2_grpc.IndexStub(channel)
    #                 stub.addToIndex(
    #                     index_pb2.AddToIndexRequest(word=word, url=url))
    #         except grpc.RpcError:
    #             # Guardar para tentar depois
    #             self.pending_updates.put((word, url, replica))

    #     # Criar threads para envio paralelo
    #     threads = [threading.Thread(target=send_update, args=(
    #         replica,)) for replica in REPLICAS]
    #     for thread in threads:
    #         thread.start()
    #     for thread in threads:
    #         thread.join()

    # def sync_with_existing_replicas(self):
    #     gateway_channel = grpc.insecure_channel("localhost:8190")
    #     gateway_stub = index_pb2_grpc.IndexStub(gateway_channel)
    #     try:
    #         response = gateway_stub.getIndexBarrels(index_pb2.IndexBarrelRequest(ip=f"localhost:{self.port}"))
    #         if response.valid:
    #             print("Server registado com sucesso")
    #             return True
    #         else:
    #             print("Nao foi possivel registar server")
    #             return False
    #     except grpc.RpcError:
    #         print("Erro ao registar server. Gateway indisponivel")
    #         return False
    #     REPLICAS = 
        
        
    #     for replica in REPLICAS:
    #         if replica == f"localhost:{self.port}":
    #             continue  # Ignorar a própria réplica

    #         try:
    #             print(f"🔄 Tentando sincronizar com {replica}...")
    #             with grpc.insecure_channel(replica) as channel:
    #                 stub = index_pb2_grpc.IndexStub(channel)
    #                 response = stub.getFullIndex(empty_pb2.Empty())

    #                 # Atualiza a base de dados local com os dados recebidos
    #                 with sqlite3.connect(self.db_file) as conn:
    #                     cursor = conn.cursor()
    #                     for entry in response.entries:
    #                         cursor.execute("""
    #                             INSERT OR REPLACE INTO index_data (palavra, url)
    #                             VALUES (?, ?)
    #                         """, (entry.palavra, entry.url))
    #                     conn.commit()
                
    #             print(f"✅ Sincronização com {replica} concluída.")
    #             return  # Sai do loop após a primeira sincronização bem-sucedida

    #         except grpc.RpcError:
    #             print(f"⚠️ Falha ao sincronizar com {replica}. Tentando outro servidor...")

    #     print("❌ Nenhuma réplica disponível para sincronização. Iniciando vazio.")
        

    # def process_pending_updates(self):
    #     while True:
    #         time.sleep(5)  # Tentar reenviar a cada 5 segundos
    #         if not self.pending_updates.empty():
    #             word, url, replica = self.pending_updates.get()
    #             self.replicate_update(word, url)  # Tenta reenviar a mensagem

    def setup_database(self):
        """Cria as tabelas se ainda não existirem."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS index_data (
                            palavra TEXT,
                            url TEXT,
                            PRIMARY KEY (palavra, url))
                            """)
            
            conn.commit()
            conn.close()

    def addToIndex(self, request, context):
        
        with self.lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM index_data WHERE palavra = ? AND url = ?",
                               (request.word, request.url))
                result = cursor.fetchone()
                print(result)
                if not result:
                    cursor.execute("INSERT INTO index_data (palavra, url) VALUES (?, ?)",
                                   (request.word, request.url))

                conn.commit()
                
        return empty_pb2.Empty()

    def searchWord(self, request, context):
        """Busca URLs para uma palavra, ordenados por frequência."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url FROM index_data
                WHERE palavra = ?
                ORDER BY frequencia DESC
            """, (request.word,))
            urls = [row[0] for row in cursor.fetchall()]
        return index_pb2.SearchWordResponse(urls=urls)
    
    def getFullIndex(self, request, context):
        """Envia todo o índice para um novo servidor que está a sincronizar."""
        
        response = index_pb2.FullIndexResponse()
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Enviar index_data
            cursor.execute("SELECT palavra, url FROM index_data")
            for palavra, url in cursor.fetchall():
                entry = response.entries.add()
                entry.palavra = palavra
                entry.url = url
                
        return response


def serve(port):
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        index_service = IndexServicer(port)
        if index_service.registerIndex():
            index_pb2_grpc.add_IndexServicer_to_server(index_service, server)
            server.add_insecure_port(f"[::]:{port}")
            server.start()
            print(f"Server started on port {port}")

            server.wait_for_termination()
    except KeyboardInterrupt:
            print("\nStopping the Index Barrel...")
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index Barrel")
    parser.add_argument("--ip", type=int, required=True,
                        help="Porta para o servidor gRPC")
    args = parser.parse_args()

    serve(args.ip)
