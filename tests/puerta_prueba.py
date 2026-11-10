"""La puerta de producción con un solo cambio: deja abrir los orígenes exactos del portal falso.

Solo lo usa tests/contencion.py. La instalación de la persona no tiene este archivo en su camino: la puerta real
sigue bloqueando todas las direcciones del propio equipo.
"""
from urllib.parse import urlsplit
from postulador import navegador, puerta

def preparar(origenes, url_mcp):
    """Devuelve (Puerta, Servicio) que hablan con un Playwright MCP propio y aceptan solo esos orígenes locales."""
    permitidos = {urlsplit(origen)._replace(path='', query='', fragment='').geturl() for origen in origenes}
    original = puerta.url_prohibida
    def url_prohibida(url):
        partes = urlsplit((url or '').strip())
        if partes.scheme and partes.netloc and '%s://%s' % (partes.scheme, partes.netloc) in permitidos: return None
        return original(url)
    puerta.url_prohibida = url_prohibida
    navegador.asegurar_mcp = lambda: {'mcp': url_mcp}
    servicio = puerta.Servicio(url_mcp)
    servicio.iniciar()
    return puerta.Puerta(), servicio
