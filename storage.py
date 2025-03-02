import sqlite3
import json
import os
import re


class Storage:
    def __init__(self, db_name="dados.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """Cria a tabela se ainda não existir."""
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,  -- Evita URLs duplicados
                title TEXT,
                text TEXT,
                links TEXT
            )"""
        )

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS index_invertido (
                palavra TEXT,
                url TEXT,
                PRIMARY KEY (palavra, url)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS page_rank (
                url TEXT PRIMARY KEY,
                links_recebidos INTEGER DEFAULT 0
            )
        """)

        # Índices para otimizar pesquisa
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_palavra ON index_invertido (palavra);")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_url ON page_rank (url);")
        self.conn.commit()

    def add_entry(self, data):
        """Adiciona uma página à base de dados, ignorando URLs já existentes."""
        try:
            self.cursor.execute(
                """INSERT OR IGNORE INTO data (url, title, text, links)
                VALUES (?, ?, ?, ?);
                """,
                (data["url"], data["title"],
                 data["text"], json.dumps(data["links"])),
            )
            self.conn.commit()

            # Criar índice invertido
            self.index_page(data["url"], data["text"])
            
            # Atualizar o número de links recebidos
            self.update_page_rank(data["url"], data["links"])

        except Exception as e:
            print(f"Erro ao inserir na base de dados: {e}")

    def get_entry(self, url):
        """Obtém uma entrada pelo URL."""
        self.cursor.execute("SELECT * FROM data WHERE url = ?;", (url,))
        return self.cursor.fetchone()

    def get_all_entries(self):
        """Obtém todas as páginas armazenadas."""
        self.cursor.execute("SELECT * FROM data;")
        return self.cursor.fetchall()

    def index_page(self, url, text):
        """Adiciona palavras ao índice invertido."""
        words = set(re.findall(r'\w+', text.lower()))  # Remove duplicadas
        for word in words:
            self.cursor.execute(
                "INSERT OR IGNORE INTO index_invertido (palavra, url) VALUES (?, ?);",
                (word, url)
            )
        self.conn.commit()

    def update_page_rank(self, url, links):
        """Atualiza o número de links recebidos por cada URL."""
        self.cursor.execute("INSERT OR IGNORE INTO page_rank (url, links_recebidos) VALUES (?, 0);", (url,))
        for link in links:
            self.cursor.execute(
                "INSERT OR IGNORE INTO page_rank (url, links_recebidos) VALUES (?, 0);", (link,)
            )
            self.cursor.execute(
                "UPDATE page_rank SET links_recebidos = links_recebidos + 1 WHERE url = ?;", (link,)
            )
        self.conn.commit()
    
    def search(self, query):
        """Pesquisa URLs que contêm as palavras da query, ordenando por links recebidos."""
        words = query.lower().split()
        results = []

        for word in words:
            self.cursor.execute("""
                SELECT index_invertido.url, page_rank.links_recebidos
                FROM index_invertido
                LEFT JOIN page_rank ON index_invertido.url = page_rank.url
                WHERE palavra = ?
                ORDER BY page_rank.links_recebidos DESC;
            """, (word,))
            
            urls = [(row[0], row[1]) for row in self.cursor.fetchall()]
            results.append(set(urls))

        if results:
            combined_results = set.intersection(*results) if len(results) > 1 else results[0]
            return sorted(combined_results, key=lambda x: x[1], reverse=True)  # Ordena por relevância

        return []

    def close(self):
        """Fecha a ligação à base de dados."""
        self.conn.close()


if __name__ == "__main__":
    storage = Storage()

    data1 = {
        "url": "https://www.wikipedia.org",
        "title": "Wikipedia",
        "text": "Enciclopédia livre sobre todos os temas.",
        "links": ["https://pt.wikipedia.org", "https://en.wikipedia.org"]
    }

    data2 = {
        "url": "https://pt.wikipedia.org",
        "title": "Wikipedia Portugal",
        "text": "Artigos enciclopédicos de Portugal.",
        "links": ["https://www.wikipedia.org"]
    }
    
    data2 = {
        "url": "https://pt.aaaaa.org",
        "title": "Wikipedia Portugal",
        "text": "Artigos wikipedia enciclopédicos de Portugal.",
        "links": ["https://www.wikipedia.org"]
    }

    storage.add_entry(data1)
    storage.add_entry(data2)

    print("Resultados para 'enciclopédicos':", storage.search("enciclopédicos"))
    print("Resultados para 'wikipedia':", storage.search("wikipedia"))

    storage.close()
