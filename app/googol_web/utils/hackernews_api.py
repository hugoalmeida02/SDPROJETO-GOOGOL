import requests

def get_top_stories():
    """ Obtém os IDs das top stories do Hacker News """
    url = 'https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Retorna os IDs das top stories
    return []

def get_story_details(story_id):
    """ Obtém os detalhes de uma história individual pelo ID """
    url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json?print=pretty'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Detalhes da história, incluindo URL
    return None

def filter_stories_by_terms(stories, search_terms):
    """ Filtra histórias cujos títulos contêm algum dos termos de pesquisa """
    filtered_stories = []
    for story in stories:
        if 'title' in story and any(term.lower() in story['title'].lower() for term in search_terms):
            filtered_stories.append(story)
    return filtered_stories

def index_story_urls(filtered_stories):
    """ Extrai os URLs das histórias filtradas """
    urls = []
    for story in filtered_stories:
        if 'url' in story:
            urls.append(story['url'])
    return urls

def index_top_stories(search_terms):
    """ Obtem as top stories com base nos termos procurados """
    story_ids = get_top_stories()
    stories = []
    
    for story_id in story_ids[:20]:  # Limitar para as top 20
        story_details = get_story_details(story_id)
        if story_details:
            stories.append(story_details)

    filtered_stories = filter_stories_by_terms(stories, search_terms)
    return index_story_urls(filtered_stories)
