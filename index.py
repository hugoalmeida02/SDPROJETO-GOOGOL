from collections import defaultdict
import re

class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(set)

    def add_page(self, url, text):
        words = set(re.findall(r'\w+', text.lower()))
        for word in words:
            self.index[word].add(url)

    def search(self, query):
        words = query.lower().split()
        results = [self.index[word] for word in words if word in self.index]
        return set.intersection(*results) if results else set()

if __name__ == "__main__":
    idx = InvertedIndex()
    idx.add_page("https://www.uc.pt", "Bem-vindo à Universidade de Coimbra")
    print(idx.search("coimbra"))
