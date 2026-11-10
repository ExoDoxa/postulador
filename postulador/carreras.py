"""Paquetes de carrera: los campos propios de cada profesión, el tope de páginas del CV y los tipos de documento.

Viven en postulador/paquetes/, dentro de la instalación: la IA no puede editarlos. Los escribe el autor.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

PAQUETES = Path(__file__).with_name('paquetes')
MI_CV = {'clave': 'mi_cv', 'etiqueta': 'Mi CV'}

def disponibles(): return sorted(ruta.stem for ruta in PAQUETES.glob('*.json'))

@lru_cache(maxsize=16)
def _cargar(id):
    return json.loads((PAQUETES / (id + '.json')).read_text(encoding='utf-8'))

def cargar(id):
    if not isinstance(id, str) or not re.fullmatch(r'[a-z_]+', id): raise ValueError('Carrera inválida.')
    if not (PAQUETES / (id + '.json')).is_file(): raise FileNotFoundError('No existe el paquete de carrera %s.' % id)
    return _cargar(id)

def de_perfil(perfil):
    """El paquete del perfil, o None si el perfil no tiene carrera."""
    return cargar(perfil['carrera']) if isinstance(perfil, dict) and perfil.get('carrera') else None

def validar(campos, paquete):
    """Errores por campo: claves desconocidas y valores que no son texto."""
    if not isinstance(campos, dict): return {'campos_carrera': 'debe ser un objeto'}
    conocidas = {campo['clave'] for campo in paquete['campos']}
    errores = {clave: 'campo desconocido para %s' % paquete['nombre'] for clave in campos if clave not in conocidas}
    errores.update({clave: 'debe ser texto' for clave, valor in campos.items() if clave in conocidas and not isinstance(valor, str)})
    return errores

def sensibles(paquete): return {campo['clave'] for campo in paquete['campos'] if campo.get('sensible')}

def faltantes(perfil):
    """Campos obligatorios del paquete que el perfil todavía no tiene."""
    paquete = de_perfil(perfil)
    if paquete is None: return []
    valores = perfil.get('campos_carrera') or {}
    return [{'clave': campo['clave'], 'etiqueta': campo['etiqueta'], 'sensible': bool(campo.get('sensible'))}
            for campo in paquete['campos'] if campo.get('obligatorio') and not str(valores.get(campo['clave'], '')).strip()]

def tipos_documento(id=None):
    """Los del paquete; sin carrera todavía (los documentos llegan antes que el perfil), los de todos los paquetes."""
    if id: return [MI_CV] + list(cargar(id)['tipos_documento'])
    tipos = {}
    for paquete in disponibles():
        for tipo in cargar(paquete)['tipos_documento']: tipos.setdefault(tipo['clave'], tipo)
    return [MI_CV] + list(tipos.values())

def paginas_maximas(perfil):
    paquete = de_perfil(perfil)
    return int(paquete.get('paginas_maximas', 1)) if paquete else 1

def para_cv(perfil):
    """[(etiqueta, valor)] de los campos con en_cv, en el orden del paquete. Nunca incluye campos sensibles."""
    paquete = de_perfil(perfil)
    if paquete is None: return []
    valores = perfil.get('campos_carrera') or {}
    return [(campo['etiqueta'], str(valores[campo['clave']]).strip()) for campo in paquete['campos']
            if campo.get('en_cv') and not campo.get('sensible') and str(valores.get(campo['clave'], '')).strip()]
