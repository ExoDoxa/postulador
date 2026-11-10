"""Postulador: herramientas locales para que un agente postule con el perfil verificado de cada usuario."""
import json
import os
from pathlib import Path

__version__ = '0.3.0'
RAIZ = Path(__file__).resolve().parent.parent
SKILL = RAIZ / 'skills' / 'postulador'
MARCA = '.postulador-datos'
# De más a menos permisivo. registro.py los reexporta.
NIVELES = ('enviar_solo', 'aprobar', 'solo_rellenar', 'solo_preparar')
TOPE_SEGURO = 'solo_rellenar'

class DatosNoDisponibles(OSError):
    """La carpeta de datos registrada no está: por ejemplo, la USB no está conectada."""

def archivo_ubicacion():
    """Único lugar donde se anota dónde viven los datos. Está en el equipo, fuera del código y de OneDrive."""
    return Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'Postulador' / 'ubicacion.json'

def archivo_equipo():
    """Tope de autonomía y carpeta de arranque de este equipo. Solo lo escribe `python -m postulador arranque`."""
    return archivo_ubicacion().with_name('equipo.json')

def equipo():
    """Lee equipo.json y falla cerrado: si falta, está dañado o trae un nivel raro, el tope es solo_rellenar. Nunca lanza."""
    problema = None
    try:
        dato = json.loads(archivo_equipo().read_text(encoding='utf-8'))
        if not isinstance(dato, dict): raise ValueError
    except FileNotFoundError:
        dato, problema = {}, 'Este equipo todavía no está preparado: falta ejecutar «python -m postulador arranque».'
    except (OSError, ValueError):
        dato, problema = {}, 'El archivo equipo.json está dañado: hay que volver a ejecutar «python -m postulador arranque».'
    nivel = dato.get('nivel_maximo')
    if nivel not in NIVELES:
        if not problema: problema = 'equipo.json trae un nivel inválido: hay que volver a ejecutar «python -m postulador arranque».'
        nivel = TOPE_SEGURO
    arranque = dato.get('arranque') if isinstance(dato.get('arranque'), str) and dato.get('arranque') else None
    return {'nivel_maximo': nivel, 'arranque': arranque, 'problema': problema}

def nivel_maximo(): return equipo()['nivel_maximo']

def estricto():
    """True en el equipo de la persona: el tope no deja enviar a la IA (solo_rellenar o menos)."""
    return NIVELES.index(nivel_maximo()) >= NIVELES.index(TOPE_SEGURO)

def carpeta_arranque():
    ruta = equipo()['arranque']
    return Path(ruta) if ruta else None

def datos():
    """Carpeta privada del usuario; nunca se sube al repositorio.

    Orden: POSTULADOR_DATOS (pruebas), luego la ubicación registrada con `python -m postulador datos --mover`, y si no
    hay ninguna, `datos_usuario/` junto al código. La ubicación registrada debe tener la misma marca de identidad: así
    nunca se escribe en otra USB que reciba la misma letra ni se crea una carpeta vacía si la USB no está.
    """
    if os.environ.get('POSTULADOR_DATOS'): return Path(os.environ['POSTULADOR_DATOS'])
    try: registrada = json.loads(archivo_ubicacion().read_text(encoding='utf-8'))
    except (OSError, ValueError): return RAIZ / 'datos_usuario'
    ruta = Path(registrada['ruta'])
    try: identidad = (ruta / MARCA).read_text(encoding='utf-8').strip()
    except OSError: identidad = None
    if not identidad or identidad != registrada.get('id'):
        raise DatosNoDisponibles('No encuentro tus datos de Postulador en %s. Si están en tu USB, conéctala y vuelve a intentarlo.' % ruta)
    return ruta
