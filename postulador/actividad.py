"""Lo que hace el agente, para verlo en el panel sin importar desde dónde se lanzó.

Guarda el nombre de la acción y la URL, nunca el texto de formularios ni respuestas.
"""
import json
import re
import time
from . import cv, datos

MOSTRAR = 60
MAXIMO_ARCHIVO = 400000

def _archivo(): return datos() / 'actividad.jsonl'

def anotar(accion, lugar='', bloqueada=False, error=False):
    archivo = _archivo()
    archivo.parent.mkdir(parents=True, exist_ok=True)
    if archivo.is_file() and archivo.stat().st_size > MAXIMO_ARCHIVO:
        lineas = archivo.read_text(encoding='utf-8').splitlines()
        archivo.write_text('\n'.join(lineas[-MOSTRAR:]) + '\n', encoding='utf-8')
    with archivo.open('a', encoding='utf-8') as salida:
        salida.write(json.dumps({'hora': time.strftime('%Y-%m-%d %H:%M:%S'), 'accion': accion, 'lugar': lugar[:200], 'bloqueada': bloqueada, 'error': error}, ensure_ascii=False) + '\n')

def recientes(limite=MOSTRAR):
    archivo = _archivo()
    if not archivo.is_file(): return []
    return [json.loads(linea) for linea in archivo.read_text(encoding='utf-8').splitlines()[-limite:]][::-1]

def carpeta_informes(): return datos() / 'informes'

def guardar_informe(titulo, contenido):
    """Deja un documento Markdown que el usuario puede abrir en el editor y ver en el panel."""
    if not cv.slug(titulo) or not contenido.strip(): raise ValueError('El informe necesita título y contenido.')
    carpeta_informes().mkdir(parents=True, exist_ok=True)
    archivo = carpeta_informes() / ('%s-%s.md' % (time.strftime('%Y-%m-%d-%H%M'), cv.slug(titulo).lower()))
    archivo.write_text('# %s\n\n%s\n' % (titulo.strip(), contenido.strip()), encoding='utf-8')
    return {'informe': str(archivo)}

def informes():
    if not carpeta_informes().is_dir(): return []
    return [{'nombre': archivo.name} for archivo in sorted(carpeta_informes().glob('*.md'), reverse=True)]

def leer_informe(nombre):
    if not re.fullmatch(r'[\w.\-]+\.md', nombre, re.A): raise ValueError('Informe inválido.')
    return {'nombre': nombre, 'contenido': (carpeta_informes() / nombre).read_text(encoding='utf-8')}
