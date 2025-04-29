import requests

HACKERNEWS_TOPSTORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HACKERNEWS_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

def search_hackernews(terms, max_results=5):
    """Procura notícias no Hacker News que contenham algum dos termos."""
    try:
        top_ids = requests.get(HACKERNEWS_TOPSTORIES_URL).json()
        results = []

        for story_id in top_ids[:100]:  # só procurar nos primeiros 100
            story = requests.get(HACKERNEWS_ITEM_URL.format(story_id)).json()
            if story and 'title' in story:
                title = story['title'].lower()
                if any(term.lower() in title for term in terms.split()):
                    results.append({
                        'title': story['title'],
                        'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}")
                    })
                    if len(results) >= max_results:
                        break
        return results
    except Exception as e:
        print(f"Erro ao consultar HackerNews: {e}")
        return []