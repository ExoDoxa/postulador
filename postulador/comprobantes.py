"""Comprobantes: lo que rellenó el asistente en cada formulario, escrito por la puerta y nunca por la IA.

La tabla la crea registro.conexion() con dos disparadores que impiden cambiar o borrar filas. Ninguna herramienta
del servidor `postulador` escribe aquí: solo la puerta, al atender `formulario_listo`.
"""
import hashlib
import json
from contextlib import closing
from pathlib import Path
from . import datos, registro

def carpeta(): return datos() / 'comprobantes'

def crear(postulacion_id, url, inicio, campos, clics, archivos, cv, imagen_png, envios_bloqueados):
    """Escribe la imagen y, en una sola transacción, la fila y el paso a `rellenada`. Si algo falla, no queda nada a medias."""
    carpeta().mkdir(parents=True, exist_ok=True)
    imagen = None
    with closing(registro.conexion()) as base:
        try:
            base.execute('begin immediate')
            fila = registro.obtener(postulacion_id, base)
            if fila['estado'] != 'preparada':
                raise ValueError('La postulación %s está %s: formulario_listo solo vale para una postulación preparada.' % (postulacion_id, fila['estado']))
            nuevo = base.execute('select coalesce(max(id), 0) + 1 from comprobantes').fetchone()[0]
            nombre, huella = '', ''
            if imagen_png:
                imagen = carpeta() / ('c%d.png' % nuevo)
                imagen.write_bytes(imagen_png)
                nombre, huella = 'comprobantes/' + imagen.name, hashlib.sha256(imagen_png).hexdigest()
            fin = registro.ahora_segundos()
            base.execute('insert into comprobantes (id,postulacion_id,url,inicio,fin,campos,clics,archivos,cv,imagen,imagen_sha256,envios_bloqueados,creado) values (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                         (nuevo, postulacion_id, url, inicio, fin, json.dumps(campos, ensure_ascii=False), json.dumps(clics, ensure_ascii=False),
                          json.dumps(archivos, ensure_ascii=False), cv, nombre, huella, envios_bloqueados, fin))
            registro.cambiar(base, postulacion_id, 'rellenada', 'puerta')
            base.commit()
        except BaseException:
            base.rollback()
            if imagen is not None: imagen.unlink(missing_ok=True)
            raise
    return {'comprobante': nuevo, 'postulacion': postulacion_id, 'estado': 'rellenada'}

def _fila(fila):
    dato = dict(fila)
    for clave in ('campos', 'clics', 'archivos'): dato[clave] = json.loads(dato[clave] or '[]')
    return dato

def leer(id):
    with closing(registro.conexion()) as base:
        fila = base.execute('select c.*, p.cargo, p.empresa, p.estado from comprobantes c join postulaciones p on p.id=c.postulacion_id where c.id=?', (id,)).fetchone()
    if fila is None: raise ValueError('No existe el comprobante %s.' % id)
    return _fila(fila)

def ultimo_de(postulacion_id):
    with closing(registro.conexion()) as base:
        fila = base.execute('select id from comprobantes where postulacion_id=? order by id desc limit 1', (postulacion_id,)).fetchone()
    return leer(fila['id']) if fila else None

def ruta_imagen(id):
    """Ruta de la imagen de la página, siempre dentro de comprobantes/."""
    relativa = leer(id)['imagen']
    if not relativa: raise FileNotFoundError('Este comprobante no tiene imagen.')
    ruta = (datos() / relativa).resolve()
    if not ruta.is_relative_to(carpeta().resolve()) or not ruta.is_file(): raise FileNotFoundError('Imagen no disponible.')
    return ruta

def para_panel(id):
    """El comprobante sin rutas del equipo."""
    dato = leer(id)
    dato['tiene_imagen'] = bool(dato.pop('imagen'))
    for archivo in dato['archivos']: archivo.pop('ruta', None)
    return dato
