import queue

class URLQueue:
    def __init__(self):
        self.q = queue.Queue()
        self.visited = set()  # Guarda os URLs já processados

    def add_url(self, url):
        """Adiciona um URL à fila se ainda não foi visitado."""
        if url not in self.visited:
            self.q.put(url)
            self.visited.add(url)

    def get_url(self):
        """Obtém o próximo URL da fila e marca-o como visitado (ou None se estiver vazia)."""
        if not self.q.empty():
            url = self.q.get()
            self.visited.add(url)  # Marca como visitado
            return url
        return None

    def is_empty(self):
        """Verifica se ainda há URLs para visitar."""
        return self.q.empty()
