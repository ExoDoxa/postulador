"""Dónde viven los datos del usuario y cómo moverlos (por ejemplo, a una USB) sin perder nada.

Mover es copiar, verificar cada archivo y registrar la nueva ubicación en un solo archivo del equipo. El original
no se borra: queda como respaldo, con una nota que dice adónde se fueron los datos.
"""
import datetime
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
from . import MARCA, RAIZ, archivo_ubicacion, datos

PUERTO_PANEL = 8770

def _huella(ruta):
    resumen = hashlib.sha256()
    with open(ruta, 'rb') as archivo:
        for bloque in iter(lambda: archivo.read(1 << 20), b''): resumen.update(bloque)
    return resumen.hexdigest()

def _panel_abierto():
    with socket.socket() as conexion:
        conexion.settimeout(.5)
        return conexion.connect_ex(('127.0.0.1', PUERTO_PANEL)) == 0

def donde():
    registrada = archivo_ubicacion()
    return {'datos': str(datos()), 'registrada_en': str(registrada) if registrada.is_file() else None}

def mover(destino, comprobar_panel=True):
    """Copia los datos a `destino` (carpeta nueva o vacía), los verifica y hace que Postulador use esa copia."""
    origen, destino = datos().resolve(), Path(destino).resolve()
    if not origen.is_dir(): raise FileNotFoundError('No hay datos que mover en %s.' % origen)
    if destino == origen or destino.is_relative_to(origen) or origen.is_relative_to(destino):
        raise ValueError('El destino no puede estar dentro de los datos actuales ni contenerlos.')
    if destino.is_relative_to(RAIZ.resolve()): raise ValueError('El destino debe estar fuera de la carpeta del código.')
    if destino.exists() and any(destino.iterdir()): raise ValueError('La carpeta %s ya tiene archivos: elige una vacía o nueva.' % destino)
    if comprobar_panel and _panel_abierto():
        raise RuntimeError('El panel de Postulador está abierto. Ciérralo, y cierra también las sesiones de Claude o Codex en la carpeta de arranque, antes de mover los datos.')
    temporal = destino.with_name(destino.name + '.copiando')
    if temporal.exists(): shutil.rmtree(temporal)
    shutil.copytree(origen, temporal, ignore=shutil.ignore_patterns(MARCA))
    archivos = [ruta for ruta in origen.rglob('*') if ruta.is_file() and ruta.name != MARCA]
    for ruta in archivos:
        copia = temporal / ruta.relative_to(origen)
        if not copia.is_file() or _huella(copia) != _huella(ruta):
            shutil.rmtree(temporal, ignore_errors=True)
            raise OSError('La copia de %s no coincide con el original; no se movió nada.' % ruta.relative_to(origen))
    for base in temporal.rglob('*.db'):
        with closing(sqlite3.connect(base)) as conexion:
            if conexion.execute('pragma integrity_check').fetchone()[0] != 'ok':
                shutil.rmtree(temporal, ignore_errors=True)
                raise OSError('La base %s quedó dañada en la copia; no se movió nada.' % base.name)
    identidad = uuid.uuid4().hex
    (temporal / MARCA).write_text(identidad, encoding='utf-8')
    if destino.exists(): destino.rmdir()
    temporal.rename(destino)
    fecha = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    registro = archivo_ubicacion()
    registro.parent.mkdir(parents=True, exist_ok=True)
    nuevo = registro.with_suffix('.tmp')
    nuevo.write_text(json.dumps({'ruta': str(destino), 'id': identidad, 'desde': str(origen), 'fecha': fecha}, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(nuevo, registro)
    (origen / 'MOVIDOS.txt').write_text('El %s estos datos se copiaron a %s y Postulador usa esa copia desde entonces.\n'
                                        'Esta carpeta quedó como respaldo y ya no se actualiza. Puedes borrarla cuando confirmes que todo funciona.\n' % (fecha, destino), encoding='utf-8')
    return {'datos': str(destino), 'archivos': len(archivos), 'respaldo': str(origen), 'registro': str(registro)}
