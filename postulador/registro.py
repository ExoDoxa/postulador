"""Registro local: postulaciones, respuestas reutilizables, políticas de autonomía, seguimientos y análisis."""
import collections
import datetime
import json
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from urllib.parse import urlsplit
from . import NIVELES, datos, estricto, nivel_maximo

ESTADOS = ('preparada', 'por_aprobar', 'rellenada', 'reportada', 'enviada', 'avanzo', 'rechazada', 'descartada', 'incompleta')
RESPONDIDAS = ('avanzo', 'rechazada')
ENVIADAS = ('enviada',) + RESPONDIDAS
# `reportada` = «Enviada según la IA»: no cuenta como enviada ni genera seguimientos hasta que la persona la confirma.
ESPERAN_ENVIO = ('rellenada', 'reportada')
ORDEN_NIVELES = tuple(reversed(NIVELES))
ACTORES = ('ia', 'puerta', 'persona')
# Rigen con el tope en solo_rellenar o menos (equipo de la persona). Con un tope mayor (equipo del autor) la IA sigue como hoy.
REGISTRO_IA = ('preparada', 'incompleta', 'descartada')
ESTADOS_IA = REGISTRO_IA + ('reportada',)
TRANSICIONES = {
    'ia': {(desde, hasta) for desde in REGISTRO_IA for hasta in REGISTRO_IA if desde != hasta} | {('rellenada', 'reportada')},
    'puerta': {('preparada', 'rellenada')},
}
# Lo que solo hace la persona desde el panel: acción -> (estados de partida, estado final)
ACCIONES = {'la_envie': (ESPERAN_ENVIO, 'enviada'), 'ya_no': (ESPERAN_ENVIO, 'descartada'), 'corregir': (ESPERAN_ENVIO, 'preparada'),
            'ya_estaba_enviada': (('preparada',) + ESPERAN_ENVIO, 'enviada'), 'avanzo': (('enviada',), 'avanzo'), 'rechazada': (('enviada',), 'rechazada')}
NIVEL_POR_DEFECTO = 'aprobar'
ADVERTENCIAS = {'linkedin': 'LinkedIn prohíbe el software que automatiza actividad en su sitio y puede restringir o cerrar la cuenta. El usuario acepta ese riesgo al automatizarlo.'}
CADENCIA = (7, 14)  # días hasta cada seguimiento; después se deja de insistir
ANTIGUEDAD_HISTORIAL = 14  # lo importado más viejo no genera seguimientos
RANGOS = ((70, '70-100'), (50, '50-69'), (0, '0-49'))
MESES = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12}
ANIO_HISTORIAL = 2026
ESQUEMA = '''
create table if not exists postulaciones (
  id integer primary key, cargo text not null, empresa text not null, sitio text not null, url text default '',
  modalidad text default '', cv text default '', estado text not null, nota text default '', creada text, actualizada text);
create table if not exists respuestas (pregunta text primary key, respuesta text not null, actualizada text);
create table if not exists comprobantes (
  id integer primary key, postulacion_id integer not null, url text default '', inicio text, fin text, campos text default '[]',
  clics text default '[]', archivos text default '[]', cv text default '', imagen text default '', imagen_sha256 text default '',
  envios_bloqueados integer default 0, creado text);
create trigger if not exists comprobantes_sin_cambios before update on comprobantes begin select raise(abort, 'Los comprobantes no se modifican'); end;
create trigger if not exists comprobantes_sin_borrar before delete on comprobantes begin select raise(abort, 'Los comprobantes no se borran'); end;
create table if not exists documentos (
  id integer primary key, huella text not null unique, archivo text not null, nombre_original text default '', tipo text default '',
  nombre text default '', ia_puede_leer integer default 0, vinculo text default '', creado text, clasificado_el text default '');
'''
COLUMNAS = {'idoneidad': 'integer', 'ats_base': 'integer', 'ats_adaptado': 'integer', 'ats_techo': 'integer', 'motivo': "text default ''",
            'enviada_el': "text default ''", 'seguir_el': "text default ''", 'seguimientos': 'integer default 0', 'origen': "text default 'agente'"}

def ahora(): return time.strftime('%Y-%m-%d %H:%M')

def ahora_segundos(): return time.strftime('%Y-%m-%d %H:%M:%S')

def conexion():
    datos().mkdir(parents=True, exist_ok=True)
    base = sqlite3.connect(datos() / 'postulador.db')
    base.row_factory = sqlite3.Row
    base.executescript(ESQUEMA)
    existentes = {fila['name'] for fila in base.execute('pragma table_info(postulaciones)')}
    for nombre, tipo in COLUMNAS.items():
        if nombre not in existentes: base.execute('alter table postulaciones add column %s %s' % (nombre, tipo))
    return base

def _estado(estado):
    if estado not in ESTADOS: raise ValueError('Estado inválido; usa: ' + ', '.join(ESTADOS))
    return estado

def _dias_despues(fecha, dias):
    return (datetime.date.fromisoformat(fecha) + datetime.timedelta(days=dias)).isoformat()

def _hoy(): return datetime.date.today().isoformat()

def similares(base, cargo, empresa, url):
    filas = base.execute('select * from postulaciones where (url<>"" and url=?) or (lower(empresa)=lower(?) and lower(cargo)=lower(?))', (url, empresa, cargo))
    return [dict(fila) for fila in filas]

def _actor(actor):
    if actor not in ACTORES: raise ValueError('Actor inválido.')
    return actor

def _permitido(actor, desde, hasta):
    """La tabla de transiciones solo rige con el tope estricto; con un tope mayor (equipo del autor) todo sigue como hoy."""
    if actor == 'puerta': return (desde, hasta) in TRANSICIONES['puerta']
    if actor == 'persona' or not estricto(): return True
    return (desde, hasta) in TRANSICIONES[actor]

def registrar(cargo, empresa, sitio, estado, url='', modalidad='', cv='', nota='', permitir_duplicado=False, idoneidad=None, ats_base=None, ats_adaptado=None, ats_techo=None, actor='persona'):
    if _actor(actor) == 'puerta': raise ValueError('La puerta no registra postulaciones.')
    if actor == 'ia' and estricto() and _estado(estado) not in REGISTRO_IA:
        raise ValueError('Esa acción no le corresponde al asistente: registra la postulación como %s.' % ', '.join(REGISTRO_IA))
    with closing(conexion()) as base, base:
        previas = similares(base, cargo, empresa, url)
        if previas and not permitir_duplicado:
            return {'duplicado': True, 'previas': previas}
        enviada = _hoy() if estado == 'enviada' else ''
        cursor = base.execute('insert into postulaciones (cargo,empresa,sitio,url,modalidad,cv,estado,nota,creada,actualizada,idoneidad,ats_base,ats_adaptado,ats_techo,enviada_el,seguir_el) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                              (cargo, empresa, sitio, url, modalidad, cv, _estado(estado), nota, ahora(), ahora(), idoneidad, ats_base, ats_adaptado, ats_techo, enviada, _dias_despues(enviada, CADENCIA[0]) if enviada else ''))
        return {'id': cursor.lastrowid, 'duplicado': False}

def obtener(id, base=None):
    if base is None:
        with closing(conexion()) as propia: return obtener(id, propia)
    fila = base.execute('select * from postulaciones where id=?', (id,)).fetchone()
    if fila is None: raise ValueError('No existe la postulación %s.' % id)
    return dict(fila)

QUIEN = {'ia': 'al asistente: lo hace el usuario en el panel', 'puerta': 'a la puerta', 'persona': 'a nadie'}

def cambiar(base, id, estado, actor, nota='', motivo=''):
    """Cambia el estado dentro de una transacción ya abierta; la usan actualizar, el panel y los comprobantes."""
    fila = obtener(id, base)
    if not _permitido(_actor(actor), fila['estado'], _estado(estado)):
        raise ValueError('Ese cambio (de %s a %s) no le corresponde %s.' % (fila['estado'], estado, QUIEN[actor]))
    enviada, seguir = fila['enviada_el'], fila['seguir_el']
    if estado == 'enviada' and not enviada: enviada, seguir = _hoy(), _dias_despues(_hoy(), CADENCIA[0])
    if estado != 'enviada': seguir = ''
    base.execute('update postulaciones set estado=?, nota=?, motivo=?, enviada_el=?, seguir_el=?, actualizada=? where id=?',
                 (estado, nota or fila['nota'], motivo or fila['motivo'], enviada, seguir, ahora(), id))
    return {'id': id, 'estado': estado}

def actualizar(id, estado, nota='', motivo='', actor='persona'):
    with closing(conexion()) as base, base:
        return cambiar(base, id, estado, actor, nota, motivo)

def accion_persona(id, accion, motivo=''):
    """Los botones del panel: solo la persona confirma envíos y registra respuestas."""
    if accion not in ACCIONES: raise ValueError('Acción inválida; usa: ' + ', '.join(ACCIONES))
    desde, hasta = ACCIONES[accion]
    with closing(conexion()) as base, base:
        fila = obtener(id, base)
        if fila['estado'] not in desde: raise ValueError('La postulación está %s: esa acción no aplica.' % fila['estado'])
        resultado = cambiar(base, id, hasta, 'persona', motivo=motivo)
    if accion == 'ya_estaba_enviada':
        from . import actividad
        actividad.anotar('incidente_envio', fila['url'], error=True)
    return resultado

def _en_espera(base):
    marcas = ','.join('?' * len(ESPERAN_ENVIO))
    return base.execute('select p.*, (select max(c.fin) from comprobantes c where c.postulacion_id=p.id) as fin from postulaciones p where p.estado in (%s) order by p.id' % marcas, ESPERAN_ENVIO)

def candado():
    """La primera postulación que espera que la persona la envíe, o None. Solo rige con el tope estricto."""
    if not estricto(): return None
    with closing(conexion()) as base:
        fila = _en_espera(base).fetchone()
    return dict(fila) if fila else None

def olvidadas(horas=24):
    """Esperan su envío desde hace más de `horas`, contadas desde el fin del último comprobante."""
    limite = (datetime.datetime.now() - datetime.timedelta(hours=horas)).strftime('%Y-%m-%d %H:%M')
    with closing(conexion()) as base:
        filas = [dict(fila) for fila in _en_espera(base)]
    return [fila for fila in filas if (fila['fin'] or fila['actualizada'] or '')[:16] < limite]

def listar(estado='', texto='', limite=50):
    consulta = 'select p.*, (select max(c.id) from comprobantes c where c.postulacion_id=p.id) as comprobante from postulaciones p where 1=1'
    parametros = []
    if estado:
        estados = [_estado(valor.strip()) for valor in estado.split(',') if valor.strip()]
        consulta += ' and estado in (%s)' % ','.join('?' * len(estados)); parametros += estados
    if texto:
        consulta += ' and (cargo like ? or empresa like ? or sitio like ? or url like ?)'
        parametros += ['%' + texto + '%'] * 4
    with closing(conexion()) as base:
        return [dict(fila) for fila in base.execute(consulta + ' order by id desc limit ?', parametros + [limite])]

def seguimientos_pendientes(limite=10):
    """Las más recientes primero: son las que todavía pueden responder."""
    with closing(conexion()) as base:
        filas = base.execute("select * from postulaciones where estado='enviada' and seguir_el<>'' and seguir_el<=? order by enviada_el desc limit ?", (_hoy(), limite))
        return [dict(fila) for fila in filas]

def seguimiento_hecho(id, nota='', actor='persona'):
    """Reprograma el siguiente contacto; pasada la cadencia deja de proponerlo."""
    if _actor(actor) != 'persona' and estricto(): raise ValueError('Los seguimientos los marca el usuario en el panel.')
    with closing(conexion()) as base, base:
        fila = base.execute('select * from postulaciones where id=?', (id,)).fetchone()
        if fila is None: raise ValueError('No existe la postulación %s.' % id)
        hechos = fila['seguimientos'] + 1
        siguiente = _dias_despues(_hoy(), CADENCIA[hechos]) if hechos < len(CADENCIA) else ''
        registro_nota = '\n'.join(filter(None, (fila['nota'], '%s seguimiento: %s' % (_hoy(), nota) if nota else '')))
        base.execute('update postulaciones set seguimientos=?, seguir_el=?, nota=?, actualizada=? where id=?', (hechos, siguiente, registro_nota, ahora(), id))
    return {'id': id, 'seguimientos': hechos, 'proximo': siguiente or 'ninguno'}

def _tasas(filas):
    """Agrupa filas [(grupo, estado)] y calcula respuesta y avance sobre lo enviado."""
    grupos = collections.defaultdict(collections.Counter)
    for grupo, estado in filas:
        if estado in ENVIADAS: grupos[grupo or 'sin dato'][estado] += 1
    resultado = []
    for grupo, cuenta in grupos.items():
        total = sum(cuenta.values())
        resultado.append({'grupo': grupo, 'enviadas': total, 'respuestas': cuenta['avanzo'] + cuenta['rechazada'], 'avances': cuenta['avanzo'], 'rechazos': cuenta['rechazada'],
                          'tasa_avance': round(100 * cuenta['avanzo'] / total), 'tasa_respuesta': round(100 * (cuenta['avanzo'] + cuenta['rechazada']) / total)})
    return sorted(resultado, key=lambda fila: (-fila['enviadas'], fila['grupo']))

def _rango(valor):
    if valor is None: return 'sin evaluar'
    return next(nombre for minimo, nombre in RANGOS if valor >= minimo)

def analisis():
    with closing(conexion()) as base:
        filas = [dict(fila) for fila in base.execute('select * from postulaciones')]
    embudo = collections.Counter(fila['estado'] for fila in filas)
    mejoras = [fila['ats_adaptado'] - fila['ats_base'] for fila in filas if fila['ats_adaptado'] is not None and fila['ats_base'] is not None]
    motivos = collections.Counter(fila['motivo'][:80] for fila in filas if fila['estado'] in ('rechazada', 'descartada') and fila['motivo'])
    return {'total': len(filas), 'embudo': dict(embudo), 'por_sitio': _tasas((fila['sitio'], fila['estado']) for fila in filas), 'por_cv': _tasas((fila['cv'], fila['estado']) for fila in filas),
            'por_idoneidad': _tasas((_rango(fila['idoneidad']), fila['estado']) for fila in filas), 'motivos': motivos.most_common(10),
            'mejora_ats_promedio': round(sum(mejoras) / len(mejoras), 1) if mejoras else None, 'evaluadas': len(mejoras), 'seguimientos_pendientes': len(seguimientos_pendientes(1000))}

def _estado_historial(texto):
    plano = texto.lower()
    if re.search(r'descartad|finalizado|no pasa', plano): return 'rechazada'
    if re.search(r'por enviar|sin terminar|sin confirmar|bloquead', plano): return 'incompleta'
    if re.search(r'avanz|shortlist|pending review|en validaci|pre-selecci.n en progreso', plano): return 'avanzo'
    return 'enviada'

def _fecha_historial(texto):
    encontrado = re.search(r'(\d{1,2}) (%s)' % '|'.join(MESES), texto.lower())
    return '%d-%02d-%02d' % (ANIO_HISTORIAL, MESES[encontrado.group(2)], int(encontrado.group(1))) if encontrado else ''

def importar_historial(ruta=None):
    """Convierte las tablas Markdown del registro manual en postulaciones; se puede repetir sin duplicar."""
    archivo = Path(ruta) if ruta else datos() / 'historial' / 'REGISTRO_POSTULACIONES.md'
    sitio, encabezado, nuevas, omitidas = '', None, 0, 0
    limite = (datetime.date.today() - datetime.timedelta(days=ANTIGUEDAD_HISTORIAL)).isoformat()
    with closing(conexion()) as base, base:
        for linea in archivo.read_text(encoding='utf-8').splitlines():
            if linea.startswith('## '): sitio = linea[3:].split('(')[0].strip().lower(); continue
            if not linea.startswith('|'): encabezado = None; continue
            celdas = [celda.strip() for celda in linea.strip().strip('|').split('|')]
            if set(linea) <= set('|-: '): continue
            if encabezado is None: encabezado = celdas; continue
            if 'Cargo' not in encabezado or 'Estado' not in encabezado or len(celdas) != len(encabezado): continue
            fila = dict(zip(encabezado, celdas))
            cargo, empresa = fila['Cargo'].strip('*'), fila.get('Empresa', sitio.title()).strip('*')
            texto_estado = fila['Estado'].replace('**', '')
            hoja_cv = fila.get('CV usado') or fila.get('CV') or ''
            enlace = re.search(r'\((https?://[^)\s]+)\)', fila.get('Enlace', ''))
            url = enlace.group(1) if enlace else ''
            if similares(base, cargo, empresa, url): omitidas += 1; continue
            estado = _estado_historial(texto_estado)
            fecha = _fecha_historial(fila.get('Enviada') or fila.get('Fecha') or '')
            seguir = _dias_despues(fecha, CADENCIA[0]) if estado == 'enviada' and fecha >= limite else ''
            base.execute("insert into postulaciones (cargo,empresa,sitio,url,modalidad,cv,estado,nota,creada,actualizada,enviada_el,seguir_el,motivo,origen) values (?,?,?,?,?,?,?,?,?,?,?,?,?,'historial')",
                         (cargo, empresa, sitio, url, fila.get('Modalidad', ''), '' if hoja_cv == '—' else hoja_cv, estado, texto_estado[:300], fecha or ahora(), ahora(), fecha, seguir, texto_estado[:120] if estado == 'rechazada' else ''))
            nuevas += 1
    return {'importadas': nuevas, 'omitidas': omitidas}

def buscar_historial(texto, limite=30):
    """Líneas de los registros importados que contienen todas las palabras buscadas."""
    palabras = texto.lower().split()
    if not palabras: raise ValueError('Indica qué buscar.')
    encontradas = []
    for archivo in sorted((datos() / 'historial').glob('*.md')):
        for numero, linea in enumerate(archivo.read_text(encoding='utf-8').splitlines(), 1):
            if all(palabra in linea.lower() for palabra in palabras):
                encontradas.append({'archivo': archivo.name, 'linea': numero, 'texto': linea[:500]})
                if len(encontradas) >= limite: return encontradas
    return encontradas

def guardar_respuesta(pregunta, respuesta):
    with closing(conexion()) as base, base:
        base.execute('insert into respuestas values (?,?,?) on conflict(pregunta) do update set respuesta=excluded.respuesta, actualizada=excluded.actualizada',
                     (pregunta, respuesta, ahora()))
    return {'guardada': pregunta}

def buscar_respuestas(texto=''):
    with closing(conexion()) as base:
        return [dict(fila) for fila in base.execute('select * from respuestas where pregunta like ? or respuesta like ? order by pregunta', ('%' + texto + '%',) * 2)]

def _politicas():
    archivo = datos() / 'politicas.json'
    return json.loads(archivo.read_text(encoding='utf-8')) if archivo.is_file() else {}

def politicas(): return _politicas()

ALIAS = {'magneto': 'magneto365.com', 'torre': 'torre.ai'}
GENERICOS = {'http', 'https', 'www', 'com', 'co', 'net', 'org', 'gov', 'edu', 'io', 'ai', 'es', 'localhost'}

def host_de(url):
    return (urlsplit(url if '//' in url else '//' + url).hostname or '').lower().removeprefix('www.')

def clave_de_sitio(sitio):
    """Normaliza lo que escribe el usuario: «https://www.Empresa.com/x» queda «empresa.com»."""
    clave = host_de(sitio.strip()) if ('.' in sitio or '/' in sitio) else sitio.strip().lower()
    return ALIAS.get(clave, clave)

def coincide(url, sitio):
    """Dominio exacto o subdominio suyo; un nombre sin punto debe ser una parte completa del dominio, nunca un fragmento."""
    host, sitio = host_de(url), ALIAS.get(sitio, sitio)
    if not host or not sitio: return False
    if '.' in sitio: return host == sitio or host.endswith('.' + sitio)
    return sitio in host.split('.')[:-1]

def limitar(nivel):
    """El menos permisivo entre el nivel pedido y el tope del equipo."""
    tope = nivel_maximo()
    if nivel not in ORDEN_NIVELES: return tope
    return min(nivel, tope, key=ORDEN_NIVELES.index)

def niveles_permitidos(): return [nivel for nivel in NIVELES if ORDEN_NIVELES.index(nivel) <= ORDEN_NIVELES.index(nivel_maximo())]

def nivel_de_url(url):
    """El sitio configurado más específico que coincide con la página; si ninguno, el nivel por defecto. Nunca pasa del tope."""
    coincidencias = [(len(ALIAS.get(sitio, sitio)), nivel) for sitio, nivel in _politicas().items() if coincide(url, sitio)]
    return limitar(max(coincidencias)[1] if coincidencias else NIVEL_POR_DEFECTO)

def consultar_politica(sitio):
    clave = clave_de_sitio(sitio)
    configurado = _politicas().get(clave, NIVEL_POR_DEFECTO)
    respuesta = {'sitio': clave, 'nivel': limitar(configurado), 'tope': nivel_maximo()}
    if respuesta['nivel'] != configurado: respuesta['configurado'] = configurado
    aviso = ADVERTENCIAS.get(clave) or ADVERTENCIAS.get(clave.split('.')[0])
    if aviso: respuesta['advertencia'] = aviso
    return respuesta

def fijar_politica(sitio, nivel):
    """Solo la usa el usuario (panel o terminal); el agente no tiene herramienta para esto."""
    clave = clave_de_sitio(sitio)
    if not clave: raise ValueError('Indica el sitio, por ejemplo computrabajo.com.')
    if clave in GENERICOS:
        raise ValueError('«%s» es demasiado general: escribe el dominio del sitio, por ejemplo computrabajo.com.' % sitio.strip())
    if nivel not in NIVELES: raise ValueError('Nivel inválido; usa: ' + ', '.join(NIVELES))
    if nivel not in niveles_permitidos(): raise ValueError('El nivel %s está por encima del tope de este equipo (%s).' % (nivel, nivel_maximo()))
    politicas = _politicas()
    politicas[clave] = nivel
    datos().mkdir(parents=True, exist_ok=True)
    (datos() / 'politicas.json').write_text(json.dumps(politicas, ensure_ascii=False, indent=2), encoding='utf-8')
    return consultar_politica(sitio)
