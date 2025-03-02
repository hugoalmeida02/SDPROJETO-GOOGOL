import sqlite3
import json


def create_table(cursor):
    
    cursor.execute(
        """ CREATE TABLE data (
            id INTEGER PRIMARY KEY autoincrement,
            url TEXT,
            title TEXT,
            text TEXT,
            links TEXT
            )"""
    )
    
def add_entry(cursor, data):
    cursor.execute(
        """ INSERT INTO data (url, title, text, links)
        VALUES (?, ?, ?, ?);
        """, (data["url"], data["title"], data["text"], json.dumps(data["links"])))
    
    
def get_entry(cursor, id):
    cursor.execute(
        """SELECT * FROM data WHERE id = ?;""", (id,)
    )
    return cursor.fetchone()


if __name__ == "__main__":
    conn = sqlite3.connect('dados.db')
    cursor = conn.cursor()
    
    data = {'url': 'https://www.wikipedia.org', 'title': 'Wikipedia', 'text': '\nSave your favorite articles to read offline, sync your reading lists across devices and customize your reading experience with the official Wikipedia app.\n \nThis page is available under the Creative Commons Attribution-ShareAlike License\nTerms of Use\nPrivacy Policy\n', 'links': ['https://en.wikipedia.org/', 'https://ja.wikipedia.org/', 'https://ru.wikipedia.org/', 'https://de.wikipedia.org/', 'https://es.wikipedia.org/', 'https://fr.wikipedia.org/']}
    
    add_entry(cursor, data)
    conn.commit()
    
    data = get_entry(cursor, 1)
    
    print(data)
    
    
    
    
