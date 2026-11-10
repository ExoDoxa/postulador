"""Ofertas de los tableros públicos de Greenhouse, Lever y Ashby que el usuario configure."""
import html
import json
import re
import urllib.request
from . import datos

PLANTILLAS = {'greenhouse': 'https://boards-api.greenhouse.io/v1/boards/%s/jobs?content=true', 'lever': 'https://api.lever.co/v0/postings/%s?mode=json',
              'ashby': 'https://api.ashbyhq.com/posting-api/job-board/%s'}
RESUMEN = 300

def limpio(texto):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', html.unescape(texto or '')))).strip()

def _json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Postulador/0.2'}), timeout=20) as respuesta:
        return json.load(respuesta)

def _normalizar(fuente, sitio, dato):
    if fuente == 'greenhouse':
        for item in dato.get('jobs', []):
            yield item.get('title', ''), item.get('absolute_url', ''), (item.get('location') or {}).get('name', ''), item.get('content', '')
    elif fuente == 'lever':
        for item in dato:
            yield item.get('text', ''), item.get('hostedUrl', ''), (item.get('categories') or {}).get('location', ''), item.get('descriptionPlain', '')
    else:
        for item in dato.get('jobs', []):
            yield item.get('title', ''), item.get('jobUrl', ''), item.get('location', ''), item.get('descriptionPlain', '')

def tableros():
    archivo = datos() / 'tableros.json'
    return json.loads(archivo.read_text(encoding='utf-8')).get('boards', []) if archivo.is_file() else []

def buscar(texto='', ubicacion='', limite=30, leer=_json):
    """Filtra por palabras del cargo o descripción y por ubicación; lo que falla se informa sin cortar el resto."""
    palabras, encontradas, errores = texto.lower().split(), [], []
    for tablero in tableros():
        fuente, sitio = tablero.get('source'), str(tablero.get('site', ''))
        if fuente not in PLANTILLAS or not re.fullmatch(r'[\w.-]+', sitio):
            errores.append('Tablero no válido: %s' % tablero); continue
        try:
            dato = leer(PLANTILLAS[fuente] % sitio)
        except (OSError, ValueError) as error:
            errores.append('%s: %s' % (sitio, error)); continue
        for titulo, url, lugar, descripcion in _normalizar(fuente, sitio, dato):
            cuerpo = limpio(descripcion)
            if palabras and not any(palabra in (titulo + ' ' + cuerpo).lower() for palabra in palabras): continue
            if ubicacion and ubicacion.lower() not in lugar.lower(): continue
            encontradas.append({'cargo': titulo, 'empresa': sitio, 'fuente': fuente, 'url': url, 'ubicacion': lugar, 'resumen': cuerpo[:RESUMEN]})
    encontradas.sort(key=lambda oferta: -sum(palabra in oferta['cargo'].lower() for palabra in palabras))
    return {'total': len(encontradas), 'ofertas': encontradas[:limite], 'errores': errores}
