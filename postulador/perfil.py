"""Perfil verificado del usuario: la única fuente de hechos para CV y formularios.

Un solo archivo por idioma. «Revisado» en el panel le pone un sello (`revisado_el` y `revisado_huella`, el SHA-256 del
contenido). Si la IA cambia algo después, el sello deja de valer y, en el equipo de la persona, no se generan CV ni
cartas hasta que ella vuelva a revisar. Los campos que el paquete de carrera marca como sensibles solo los escribe
ella, y a la IA le llegan tapados.
"""
import datetime
import hashlib
import json
import os
import re
import time
from . import carreras, datos, estricto

REQUERIDOS = {'name': str, 'contact': list, 'skills': list, 'languages': list, 'education': list, 'experience': list, 'cv_summaries': dict}
OPCIONALES = {'publications': list, 'projects': list}
CON_ID = ('experience', 'publications', 'projects')
SELLO = ('revisado_el', 'revisado_huella')
TAPADO = '•••• (lo escribe el usuario en el panel)'
VERSION = 1

def ruta(idioma='es'):
    if not re.fullmatch(r'[a-z]{2}', idioma): raise ValueError('Idioma inválido: usa dos letras, como es o en.')
    return datos() / ('perfil.json' if idioma == 'es' else 'perfil_%s.json' % idioma)

def ruta_revisado(idioma='es'):
    return datos() / 'respaldos' / ('revisado.json' if idioma == 'es' else 'revisado_%s.json' % idioma)

def _crudo(idioma):
    archivo = ruta(idioma)
    if not archivo.is_file():
        raise FileNotFoundError('No hay perfil en idioma %s: créalo siguiendo la guía referencias/perfil.md.' % idioma)
    perfil = json.loads(archivo.read_text(encoding='utf-8'))
    for clave in OPCIONALES: perfil.setdefault(clave, [])
    return perfil

def tapar(perfil):
    """Copia del perfil con los campos sensibles tapados, para la IA."""
    paquete = carreras.de_perfil(perfil)
    if paquete is None: return perfil
    copia = json.loads(json.dumps(perfil))
    valores = copia.get('campos_carrera') or {}
    for clave in carreras.sensibles(paquete):
        if str(valores.get(clave, '')).strip(): valores[clave] = TAPADO
    return copia

def leer(idioma='es', para_ia=False):
    perfil = _crudo(idioma)
    return tapar(perfil) if para_ia else perfil

def huella(perfil):
    contenido = {clave: valor for clave, valor in perfil.items() if clave not in SELLO}
    return hashlib.sha256(json.dumps(contenido, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()

def _vigente(perfil): return bool(perfil.get('revisado_huella')) and perfil['revisado_huella'] == huella(perfil)

def sello_vigente(idioma='es'):
    try: return _vigente(_crudo(idioma))
    except (OSError, ValueError): return False

def exigir_revision(idioma='es'):
    """En el equipo de la persona no se generan CV ni cartas con datos que ella no revisó."""
    if estricto() and ruta(idioma).is_file() and not sello_vigente(idioma):
        raise PermissionError('Primero revisa tu perfil en el panel (pestaña Perfil, botón «Revisado»): el asistente no genera CV ni cartas con datos que no revisaste.')

def validar(perfil):
    if not isinstance(perfil, dict): raise ValueError('El perfil debe ser un objeto.')
    for clave, tipo in REQUERIDOS.items():
        if not isinstance(perfil.get(clave), tipo): raise ValueError('Falta o es inválido: ' + clave)
    for clave, tipo in OPCIONALES.items():
        if not isinstance(perfil.get(clave, []), tipo): raise ValueError('Es inválido: ' + clave)
    if not perfil['name'].strip(): raise ValueError('Falta el nombre.')
    if not perfil['cv_summaries']: raise ValueError('cv_summaries necesita al menos un resumen.')
    for clave in CON_ID:
        ids = [item.get('id') for item in perfil.get(clave, [])]
        if not all(isinstance(valor, str) and valor for valor in ids) or len(ids) != len(set(ids)):
            raise ValueError('Cada entrada de %s necesita un id único.' % clave)
    for item in perfil['experience']:
        if not isinstance(item.get('bullets'), list): raise ValueError('La experiencia %s necesita bullets.' % item['id'])
    ids_formacion = [item.get('id') for item in perfil['education'] if item.get('id')]
    if len(ids_formacion) != len(set(ids_formacion)): raise ValueError('Cada entrada de education necesita un id único.')
    paquete = carreras.de_perfil(perfil)
    if paquete is not None:
        errores = carreras.validar(perfil.get('campos_carrera') or {}, paquete)
        if errores: raise ValueError('Campos de carrera inválidos: ' + '; '.join('%s: %s' % par for par in sorted(errores.items())))
    return perfil

def _ids_formacion(formacion):
    usados = {item['id'] for item in formacion if isinstance(item, dict) and item.get('id')}
    siguiente = 1
    for item in formacion:
        if isinstance(item, dict) and not item.get('id'):
            while 'f%d' % siguiente in usados: siguiente += 1
            item['id'] = 'f%d' % siguiente; usados.add(item['id'])
    return formacion

def _escribir(perfil, archivo, respaldar=True):
    archivo.parent.mkdir(parents=True, exist_ok=True)
    if respaldar and archivo.is_file():
        respaldos = datos() / 'respaldos'
        respaldos.mkdir(exist_ok=True)
        (respaldos / ('%s-%s' % (time.strftime('%Y%m%d-%H%M%S'), archivo.name))).write_bytes(archivo.read_bytes())
    temporal = archivo.with_suffix('.tmp')
    temporal.write_text(json.dumps(perfil, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporal, archivo)

def guardar(perfil, idioma='es', por='ia'):
    """Valida y escribe de forma atómica; la versión anterior queda en respaldos/.

    por='ia': conserva los campos sensibles del archivo y rechaza cambiarlos; el sello queda como estaba, así que
    cualquier cambio lo invalida. por='persona' (el panel): renueva el sello solo si estaba vigente antes.
    """
    if por not in ('ia', 'persona'): raise ValueError('Origen inválido.')
    perfil = json.loads(json.dumps(perfil)) if isinstance(perfil, dict) else perfil
    validar(perfil)
    archivo = ruta(idioma)
    previo = _crudo(idioma) if archivo.is_file() else None
    paquete = carreras.de_perfil(perfil)
    if paquete is not None:
        nuevos = dict(perfil.get('campos_carrera') or {})
        anteriores = (previo or {}).get('campos_carrera') or {}
        if por == 'ia':
            for clave in carreras.sensibles(paquete):
                if clave in nuevos and nuevos[clave] not in (TAPADO, anteriores.get(clave)):
                    raise PermissionError('El campo «%s» solo se escribe desde el panel: pídele al usuario que lo ponga ahí.' % clave)
                if clave in anteriores: nuevos[clave] = anteriores[clave]
                else: nuevos.pop(clave, None)
        perfil['campos_carrera'] = nuevos
    _ids_formacion(perfil['education'])
    perfil['schema_version'] = VERSION
    vigente = previo is not None and _vigente(previo)
    for clave in SELLO: perfil.pop(clave, None)
    if previo is not None:
        for clave in SELLO:
            if clave in previo: perfil[clave] = previo[clave]
    if por == 'persona' and vigente: _sellar(perfil)
    _escribir(perfil, archivo)
    if por == 'persona' and vigente: _escribir(perfil, ruta_revisado(idioma), respaldar=False)
    return {'guardado': archivo.name, 'revisado': _vigente(perfil)}

def _sellar(perfil):
    for clave in SELLO: perfil.pop(clave, None)
    perfil['revisado_el'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    perfil['revisado_huella'] = huella(perfil)
    return perfil

def marcar_revisado(idioma='es', migracion=False):
    """El botón «Revisado» del panel: sella el contenido actual y deja una copia para mostrar los cambios futuros."""
    perfil = _crudo(idioma)
    perfil['schema_version'] = VERSION
    if migracion: _ids_formacion(perfil['education'])
    _sellar(perfil)
    _escribir(perfil, ruta(idioma), respaldar=not migracion)
    _escribir(perfil, ruta_revisado(idioma), respaldar=False)
    return {'revisado_el': perfil['revisado_el'], 'idioma': idioma}

def _plano(valor, prefijo=''):
    if isinstance(valor, dict):
        salida = {}
        for clave, dato in valor.items(): salida.update(_plano(dato, '%s.%s' % (prefijo, clave) if prefijo else clave))
        return salida
    if isinstance(valor, list) and any(isinstance(item, (dict, list)) for item in valor):
        salida = {}
        for indice, dato in enumerate(valor):
            nombre = dato.get('id') if isinstance(dato, dict) and dato.get('id') else str(indice)
            salida.update(_plano(dato, '%s[%s]' % (prefijo, nombre)))
        return salida
    return {prefijo: valor}

def cambios(idioma='es'):
    """Lo que cambió desde la última revisión, campo por campo, para el panel."""
    actual = _crudo(idioma)
    try: revisado = json.loads(ruta_revisado(idioma).read_text(encoding='utf-8'))
    except (OSError, ValueError): revisado = {}
    antes, despues = _plano({k: v for k, v in revisado.items() if k not in SELLO}), _plano({k: v for k, v in actual.items() if k not in SELLO})
    lista = [{'campo': campo, 'antes': antes.get(campo), 'despues': despues.get(campo)} for campo in sorted(set(antes) | set(despues)) if antes.get(campo) != despues.get(campo)]
    return {'revisado': _vigente(actual), 'revisado_el': actual.get('revisado_el', ''), 'nunca_revisado': not actual.get('revisado_huella'), 'cambios': lista}

def faltantes(idioma='es'):
    """Lo que falta para completar el perfil: base y campos obligatorios del paquete de carrera."""
    try: perfil = _crudo(idioma)
    except FileNotFoundError: return {'sin_perfil': True, 'faltan': ['todo: crea el perfil siguiendo referencias/perfil.md'], 'carrera': []}
    base = [clave for clave in ('headline', 'contact', 'education', 'experience', 'skills', 'languages') if not perfil.get(clave)]
    return {'sin_perfil': False, 'carrera_del_perfil': perfil.get('carrera') or None, 'faltan': base, 'carrera': carreras.faltantes(perfil),
            'revisado': _vigente(perfil)}
