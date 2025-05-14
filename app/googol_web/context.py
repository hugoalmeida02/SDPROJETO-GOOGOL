from .webserver import WebServer

_webserver = WebServer

def set_webserver(webserver):
    global _webserver
    _webserver = webserver

def get_webserver():
    return _webserver
