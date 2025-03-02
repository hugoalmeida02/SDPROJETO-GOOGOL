import requests
from bs4 import BeautifulSoup
from url_queue import URLQueue
from urllib.parse import urljoin
from storage import Storage


def download_page(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string if soup.title else "Sem título"
        text = ' '.join(p.text for p in soup.find_all('p'))
        links = [urljoin(url, a['href']) for a in soup.find_all(
            'a', href=True) if not a['href'].startswith("#")]

        return {"url": url, "title": title, "text": text, "links": links}

    except requests.RequestException as e:
        print(f"Erro ao baixar {url}: {e}")
        return None


def crawl(seed_url, max_pages=10):
    queue = URLQueue()
    storage = Storage()
    queue.add_url(seed_url)
    pages_crawled = 0
    queue.add_url(seed_url)
    while not queue.is_empty() and pages_crawled < max_pages:
        url = queue.get_url()
        if not url:
            break

        print(f"[{pages_crawled+1}] A processar: {url}")
        data = download_page(url)

        # Verifica se o URL já está na base de dados
        if storage.get_entry(url):
            print(f"Já existe na base de dados: {url}")
            continue

        if data:
            storage.add_entry(data)
            for links in data["links"]:
                queue.add_url(links)
            pages_crawled += 1
    
    storage.close()
            


if __name__ == "__main__":
    start_url = "https://www.wikipedia.org"
    crawl(start_url, 10)
