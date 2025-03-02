import xmlrpc.client

proxy = xmlrpc.client.ServerProxy("http://localhost:8000")

proxy.add_page("https://www.uc.pt", "Bem-vindo à Universidade de Coimbra")
print(proxy.search("universidade"))
