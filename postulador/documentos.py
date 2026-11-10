"""Documentos de la persona: diplomas, tarjeta profesional, certificados y su CV.

Ella los deja en `entrada/` de su carpeta de arranque. Al listar, el código copia lo nuevo (nunca lo mueve) a la
carpeta de datos con un nombre propio y lo registra. Ella elige en el panel el tipo, el nombre visible y si la IA
puede leerlo. La IA solo ve id, tipo y nombre de los ya clasificados, y lee el texto solo con permiso.
"""
import hashlib
import re
import shutil
import time
import zipfile
from contextlib import closing
from xml.etree import ElementTree as ET
from . import carpeta_arranque, carreras, datos, registro

RECIENTE = 10  # segundos: un archivo modificado hace menos puede estar a medio copiar
TAMANO_MAXIMO = 50 * 1024 * 1024
IGNORAR = re.compile(r'^(~\$|\.)|\.(tmp|part|crdownload|lnk|ini)$', re.I)
IMAGENES = {'.jpg', '.jpeg', '.png', '.heic', '.webp', '.tif', '.tiff', '.bmp', '.gif'}
CEDULA = re.compile(r'(?i)(c\.?\s?c\.?|c[ée]dula(?: de ciudadan[ií]a)?)([^\d\n]{0,15})([\d][\d.\s]{5,14}\d)')
NO_PDF = 'No puedo leer PDF en este equipo porque falta un componente. Dile al usuario que avise a quien le instaló Postulador.'

def carpeta(): return datos() / 'documentos'

def entrada():
    arranque = carpeta_arranque()
    return arranque / 'entrada' if arranque else None

def _hash(ruta):
    resumen = hashlib.sha256()
    with ruta.open('rb') as archivo:
        for bloque in iter(lambda: archivo.read(1 << 20), b''): resumen.update(bloque)
    return resumen.hexdigest()

def barrer():
    """Copia a documentos/ lo nuevo de entrada/. Devuelve cuántos archivos registró."""
    origen = entrada()
    if origen is None or not origen.is_dir(): return 0
    nuevos, ahora = 0, time.time()
    with closing(registro.conexion()) as base:
        for archivo in sorted(origen.iterdir()):
            try:
                if not archivo.is_file() or IGNORAR.search(archivo.name): continue
                estado = archivo.stat()
                if ahora - estado.st_mtime < RECIENTE or estado.st_size == 0 or estado.st_size > TAMANO_MAXIMO: continue
                huella = _hash(archivo)
                if base.execute('select 1 from documentos where huella=?', (huella,)).fetchone(): continue
                carpeta().mkdir(parents=True, exist_ok=True)
                relativa = 'documentos/%s-%s%s' % (time.strftime('%Y%m%d'), huella[:8], archivo.suffix.lower()[:8])
                shutil.copy2(archivo, datos() / relativa)
                with base:
                    base.execute('insert into documentos (huella,archivo,nombre_original,creado) values (?,?,?,?)', (huella, relativa, archivo.name, registro.ahora()))
                nuevos += 1
            except OSError:
                continue
    return nuevos

def listar_para_ia():
    """Solo los clasificados, sin rutas ni nombres originales: pueden traer la cédula."""
    barrer()
    with closing(registro.conexion()) as base:
        filas = base.execute("select id, tipo, nombre, ia_puede_leer from documentos where tipo<>'' order by id")
        return [{'id': fila['id'], 'tipo': fila['tipo'], 'nombre': fila['nombre'], 'puedes_leerlo': bool(fila['ia_puede_leer'])} for fila in filas]

def listar_para_panel():
    barrer()
    with closing(registro.conexion()) as base:
        return [dict(fila) for fila in base.execute("select * from documentos order by (tipo='') desc, id desc")]

def _tipos_validos():
    from . import perfil
    try: carrera = perfil.leer().get('carrera')
    except (OSError, ValueError): carrera = None
    return {tipo['clave'] for tipo in carreras.tipos_documento(carrera)}

def clasificar(id, tipo, nombre, ia_puede_leer=False, vinculo=''):
    """Lo hace la persona en el panel. «Mi CV» siempre se puede leer: de ahí parte la entrevista."""
    if tipo not in _tipos_validos(): raise ValueError('Tipo de documento inválido.')
    nombre = ' '.join(str(nombre or '').split())[:80]
    if not nombre: raise ValueError('Ponle un nombre visible al documento.')
    if vinculo and not re.fullmatch(r'[\w-]{1,40}', str(vinculo)): raise ValueError('Vínculo inválido.')
    with closing(registro.conexion()) as base, base:
        if not base.execute('select 1 from documentos where id=?', (id,)).fetchone(): raise ValueError('No existe el documento %s.' % id)
        base.execute('update documentos set tipo=?, nombre=?, ia_puede_leer=?, vinculo=?, clasificado_el=? where id=?',
                     (tipo, nombre, 1 if (tipo == 'mi_cv' or ia_puede_leer is True) else 0, vinculo or '', registro.ahora(), id))
    return {'id': id, 'tipo': tipo, 'nombre': nombre}

def _fila(id):
    with closing(registro.conexion()) as base:
        fila = base.execute('select * from documentos where id=?', (id,)).fetchone()
    if fila is None: raise ValueError('No existe el documento %s.' % id)
    return dict(fila)

def ruta(id):
    """Archivo del documento, siempre dentro de documentos/. Solo para el panel."""
    real = (datos() / _fila(id)['archivo']).resolve()
    if not real.is_relative_to(carpeta().resolve()) or not real.is_file(): raise FileNotFoundError('Documento no disponible.')
    return real

def tapar_cedula(texto):
    return CEDULA.sub(lambda m: m.group(1) + m.group(2) + '[número tapado]', texto)

def _texto_docx(archivo):
    from . import motor_docx
    with zipfile.ZipFile(archivo) as paquete:
        raiz = ET.fromstring(paquete.read('word/document.xml'))
    return '\n'.join(filter(None, (motor_docx.para_text(parrafo) for parrafo in raiz.iter(motor_docx.w('p')))))

def leer(id):
    """Texto del documento, solo si la persona lo permitió. Nunca lanza por un formato raro: lo explica."""
    fila = _fila(id)
    if not fila['tipo'] or not fila['ia_puede_leer']:
        raise PermissionError('El usuario no te dio permiso para leer este documento. Si lo necesitas, pídele que marque «La IA puede leerlo» en el panel, pestaña Documentos.')
    archivo = ruta(id)
    extension = archivo.suffix.lower()
    if extension in IMAGENES: return {'id': id, 'texto': '', 'aviso': 'Es una imagen escaneada: no puedo leer su texto. Pídele al usuario los datos que necesites.'}
    if extension == '.pdf':
        from . import ats
        try: texto = ats.extraer_pdf(archivo)
        except Exception: return {'id': id, 'texto': '', 'aviso': 'No pude leer este PDF. Si es un escaneo, pídele al usuario los datos.'}
        if texto is None: return {'id': id, 'texto': '', 'aviso': NO_PDF}
        if not texto.strip(): return {'id': id, 'texto': '', 'aviso': 'Este PDF no tiene texto: parece un escaneo. Pídele al usuario los datos que necesites.'}
    elif extension == '.docx':
        try: texto = _texto_docx(archivo)
        except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError): return {'id': id, 'texto': '', 'aviso': 'No pude abrir este documento de Word.'}
    elif extension in ('.txt', '.md'):
        texto = archivo.read_text(encoding='utf-8', errors='replace')
    else:
        return {'id': id, 'texto': '', 'aviso': 'No sé leer archivos %s. Pídele al usuario un PDF o un Word.' % extension}
    return {'id': id, 'tipo': fila['tipo'], 'nombre': fila['nombre'], 'texto': tapar_cedula(texto)[:60000]}
