from .webserver import WebSever

_webserver = WebSever

def set_webserver(webserver):
    global _webserver
    _webserver = webserver

def get_webserver():
    return _webserver
