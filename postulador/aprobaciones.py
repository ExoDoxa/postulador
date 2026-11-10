"""Aprobaciones de un solo uso: cubren exactamente una postulación, vencen y solo las resuelve el usuario."""
import datetime
from contextlib import closing
from urllib.parse import urlsplit
from . import registro

VIGENCIA_HORAS = 24
ESQUEMA = '''create table if not exists aprobaciones (
  id integer primary key, url text not null, host text not null, cargo text not null, empresa text not null, cv text default '',
  detalle text default '', idoneidad integer, estado text not null, creada text, vence text default '', resuelta text default '')'''

def _conexion():
    base = registro.conexion()
    base.execute(ESQUEMA)
    return base

def host_de(url): return (urlsplit(url).hostname or '').lower().removeprefix('www.')

def solicitar(url, cargo, empresa, cv='', detalle='', idoneidad=None):
    if not host_de(url): raise ValueError('Indica la URL de la página donde se enviará.')
    with closing(_conexion()) as base, base:
        previa = base.execute("select id from aprobaciones where url=? and estado='pendiente'", (url,)).fetchone()
        if previa: return {'id': previa['id'], 'estado': 'pendiente'}
        cursor = base.execute("insert into aprobaciones (url,host,cargo,empresa,cv,detalle,idoneidad,estado,creada) values (?,?,?,?,?,?,?,'pendiente',?)",
                              (url, host_de(url), cargo, empresa, cv, detalle, idoneidad, registro.ahora()))
        return {'id': cursor.lastrowid, 'estado': 'pendiente'}

def consultar(id):
    with closing(_conexion()) as base:
        fila = base.execute('select * from aprobaciones where id=?', (id,)).fetchone()
    if fila is None: raise ValueError('No existe la solicitud %s.' % id)
    return dict(fila)

def listar(estado='pendiente', limite=50):
    with closing(_conexion()) as base:
        return [dict(fila) for fila in base.execute('select * from aprobaciones where estado=? order by id desc limit ?', (estado, limite))]

def resolver(id, aprobar):
    """No se expone como herramienta del agente: lo hace el usuario desde el panel o la terminal."""
    with closing(_conexion()) as base, base:
        fila = base.execute('select estado from aprobaciones where id=?', (id,)).fetchone()
        if fila is None: raise ValueError('No existe la solicitud %s.' % id)
        if fila['estado'] != 'pendiente': raise ValueError('La solicitud ya está %s.' % fila['estado'])
        vence = (datetime.datetime.now() + datetime.timedelta(hours=VIGENCIA_HORAS)).strftime('%Y-%m-%d %H:%M') if aprobar else ''
        base.execute('update aprobaciones set estado=?, vence=?, resuelta=? where id=?', ('aprobada' if aprobar else 'rechazada', vence, registro.ahora(), id))
    return {'id': id, 'estado': 'aprobada' if aprobar else 'rechazada', 'vence': vence}

def consumir(url):
    """Gasta la aprobación vigente de ese sitio; devuelve su id o None."""
    with closing(_conexion()) as base, base:
        fila = base.execute("select id from aprobaciones where estado='aprobada' and host=? and vence>=? order by id limit 1", (host_de(url), registro.ahora())).fetchone()
        if fila is None: return None
        base.execute("update aprobaciones set estado='usada' where id=?", (fila['id'],))
        return fila['id']

def devolver(id):
    """La acción falló antes de enviar: la firma sigue siendo válida."""
    with closing(_conexion()) as base, base:
        base.execute("update aprobaciones set estado='aprobada' where id=? and estado='usada'", (id,))
