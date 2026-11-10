"""Genera CV desde el perfil: plantilla DOCX propia con Word o HTML con el navegador.

Una página, salvo que el paquete de carrera del perfil fije otro tope (paginas_maximas).
"""
import base64
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unicodedata
from pathlib import Path
from . import RAIZ, carreras, datos, motor_docx, navegador, perfil as perfiles

PLANTILLAS = RAIZ / 'postulador' / 'plantillas'
PLANTILLA_HTML = PLANTILLAS / 'columna.html'
DISENOS = {'columna': 'Una columna, la más legible para un ATS', 'clasico': 'Dos columnas con barra lateral', 'editorial': 'Serif elegante'}
FUENTES = ('Arial', 'Calibri', 'Verdana', 'Georgia', 'Cambria', 'Times New Roman')
POSICIONES_FOTO = ('ninguna', 'izquierda', 'derecha')
AJUSTES = {'fuente': 'Arial', 'tamano': 9.2, 'color': '#1f3a4d', 'foto': 'ninguna'}
TAMANOS = (8, 11)
FUENTE_DEL_DISENO = {'editorial': 'Georgia'}
TIPOS_FOTO = {b'\xff\xd8\xff': 'jpg', b'\x89PNG\r\n\x1a\n': 'png'}
TAMANO_FOTO = 5 * 1024 * 1024
PLANTILLA_CARTA = PLANTILLAS / 'carta.html'
CLAVES = {'experiences': 'experience', 'publications': 'publications', 'projects': 'projects'}
TITULOS = {
    'es': {'contacto': 'Contacto', 'habilidades': 'Habilidades', 'idiomas': 'Idiomas', 'experiencia': 'Experiencia', 'formacion': 'Formación', 'publicaciones': 'Publicaciones', 'proyectos': 'Proyectos'},
    'en': {'contacto': 'Contact', 'habilidades': 'Skills', 'idiomas': 'Languages', 'experiencia': 'Experience', 'formacion': 'Education', 'publicaciones': 'Publications', 'proyectos': 'Projects'},
}

def slug(texto):
    plano = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9]+', '_', plano).strip('_')

def carpeta_cv(): return datos() / 'cv'

def plantilla_docx(idioma):
    return datos() / 'plantillas' / ('plantilla_CV.docx' if idioma == 'es' else 'plantilla_CV_%s.docx' % idioma)

def validar(seleccion, perfil):
    if seleccion.get('summary') not in perfil['cv_summaries'].values(): raise ValueError('summary debe ser idéntico a un valor de cv_summaries.')
    for clave, fuente in CLAVES.items():
        ids = {item['id'] for item in perfil[fuente]}
        valores = seleccion.get(clave, [])
        if not isinstance(valores, list) or len(valores) != len(set(valores)) or set(valores) - ids: raise ValueError(clave + ' contiene ids inválidos.')
    if not seleccion.get('experiences'): raise ValueError('Selecciona al menos una experiencia.')
    habilidades = seleccion.get('skills', [])
    if not isinstance(habilidades, list) or set(habilidades) - set(perfil['skills']): raise ValueError('skills debe salir del perfil.')
    viñetas = {item['id']: len(item['bullets']) for item in perfil['experience']}
    for id_experiencia, indices in seleccion.get('bullets', {}).items():
        if id_experiencia not in seleccion['experiences'] or not isinstance(indices, list) or any(not isinstance(i, int) or not 0 <= i < viñetas[id_experiencia] for i in indices):
            raise ValueError('bullets inválido para ' + id_experiencia)

def _lista(valores): return ''.join('<li>%s</li>' % html.escape(str(valor)) for valor in valores)

def _texto_idioma(valor):
    return ' · '.join(str(v) for v in valor.values()) if isinstance(valor, dict) else str(valor)

def _entrada(titulo, detalle, viñetas=()):
    lista = '<ul>%s</ul>' % _lista(viñetas) if viñetas else ''
    return '<article><h3>%s</h3><p class="detalle">%s</p>%s</article>' % (html.escape(titulo), html.escape(detalle), lista)

def _seccion(perfil, seleccion, clave):
    """Mantiene el orden del perfil, que es cronológico inverso, no el de prioridad."""
    return [item for item in perfil[CLAVES[clave]] if item['id'] in seleccion.get(clave, [])]

def _linea(item): return '  |  '.join(filter(None, (item.get('organization', ''), item.get('date', ''))))

def _bloque(titulo, contenido, envoltura='%s'):
    """Una sección sin entradas desaparece junto con su título."""
    return '<h2>%s</h2>%s' % (html.escape(titulo), envoltura % contenido) if contenido else ''

def limpiar_ajustes(cambios):
    """Solo valores conocidos: estos datos terminan dentro de una hoja de estilos."""
    ajustes = dict(AJUSTES, **{clave: valor for clave, valor in (cambios or {}).items() if clave in AJUSTES})
    if ajustes['fuente'] not in FUENTES: raise ValueError('Letra no disponible.')
    if ajustes['foto'] not in POSICIONES_FOTO: raise ValueError('Posición de foto inválida.')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', str(ajustes['color'])): raise ValueError('Color inválido.')
    ajustes['tamano'] = float(ajustes['tamano'])
    if not TAMANOS[0] <= ajustes['tamano'] <= TAMANOS[1]: raise ValueError('El tamaño va de %d a %d puntos.' % TAMANOS)
    return ajustes

def archivo_foto():
    return next((ruta for ruta in (datos() / 'foto.jpg', datos() / 'foto.png') if ruta.is_file()), None)

def guardar_foto(contenido):
    tipo = next((extension for firma, extension in TIPOS_FOTO.items() if contenido.startswith(firma)), None)
    if tipo is None: raise ValueError('La foto debe ser JPG o PNG.')
    if len(contenido) > TAMANO_FOTO: raise ValueError('La foto supera 5 MB.')
    for anterior in ('foto.jpg', 'foto.png'): (datos() / anterior).unlink(missing_ok=True)
    (datos() / ('foto.' + tipo)).write_bytes(contenido)
    return {'foto': 'foto.' + tipo}

def _foto_html(ajustes):
    foto = archivo_foto()
    if ajustes['foto'] == 'ninguna' or foto is None: return ''
    tipo = 'jpeg' if foto.suffix == '.jpg' else 'png'
    return '<img class="foto" alt="" src="data:image/%s;base64,%s">' % (tipo, base64.b64encode(foto.read_bytes()).decode())

def componer_html(seleccion, perfil, plantilla=PLANTILLA_HTML, idioma='es', ajustes=None):
    ajustes = limpiar_ajustes(ajustes)
    titulos = TITULOS.get(idioma, TITULOS['en'])
    lista = {'contacto': perfil['contact'], 'habilidades': seleccion.get('skills', []), 'idiomas': map(_texto_idioma, perfil['languages'])}
    entradas = {
        'formacion': [_entrada(item['title'], _linea(item)) for item in perfil['education']],
        'experiencia': [_entrada(item['title'], _linea(item), motor_docx.bullets_for(seleccion, item)) for item in _seccion(perfil, seleccion, 'experiences')],
        'publicaciones': [_entrada(item.get('cv_title') or item['title'], item.get('cv_citation', '')) for item in _seccion(perfil, seleccion, 'publications')],
        'proyectos': [_entrada(item.get('cv_title') or item['title'], item.get('cv_description', '')) for item in _seccion(perfil, seleccion, 'projects')],
    }
    estilo = '<style>:root { --fuente: "%s"; --tamano: %.1fpt; --acento: %s }</style>' % (ajustes['fuente'], ajustes['tamano'], ajustes['color'])
    valores = {'estilo': estilo, 'foto': _foto_html(ajustes), 'clase_foto': 'foto-' + ajustes['foto'], 'idioma': html.escape(idioma), 'nombre': html.escape(perfil['name']), 'titular': html.escape(perfil.get('headline', '')), 'resumen': html.escape(seleccion['summary']),
               'carrera': _bloque_carrera(perfil)}
    valores.update({clave: _bloque(titulos[clave], _lista(items), '<ul>%s</ul>') for clave, items in lista.items()})
    valores.update({clave: _bloque(titulos[clave], ''.join(items)) for clave, items in entradas.items()})
    contenido = Path(plantilla).read_text(encoding='utf-8')
    return re.sub(r'\{\{(\w+)\}\}', lambda marca: valores[marca.group(1)], contenido)

def _bloque_carrera(perfil):
    """Una sola sección con el título del paquete y «etiqueta: valor», escapada como las demás marcas."""
    filas = carreras.para_cv(perfil)
    if not filas: return ''
    titulo = carreras.cargar(perfil['carrera']).get('titulo_cv') or carreras.cargar(perfil['carrera'])['nombre']
    return _bloque(titulo, ''.join('<li><strong>%s:</strong> %s</li>' % (html.escape(etiqueta), html.escape(valor)) for etiqueta, valor in filas), '<ul>%s</ul>')

def experiencias(seleccion, perfil): return _seccion(perfil, seleccion, 'experiences')

def texto_seleccion(seleccion, perfil):
    """Texto plano que quedaría en el CV, sin depender de un motor."""
    partes = [perfil['name'], perfil.get('headline', ''), seleccion['summary'], ' '.join(perfil['contact']), ' '.join(seleccion.get('skills', [])), ' '.join(seleccion.get('tools', [])), ' '.join(map(_texto_idioma, perfil['languages']))]
    partes += [' '.join((item['title'], _linea(item))) for item in perfil['education']]
    for item in experiencias(seleccion, perfil):
        partes += [item['title'], _linea(item)] + motor_docx.bullets_for(seleccion, item)
    for clave, detalle in (('publications', 'cv_citation'), ('projects', 'cv_description')):
        partes += [' '.join((item.get('cv_title') or item.get('title', ''), item.get(detalle, ''))) for item in _seccion(perfil, seleccion, clave)]
    return '\n'.join(filter(None, partes))

def seleccion_base(perfil):
    """CV genérico sin adaptar: el punto de comparación para medir cuánto aporta la adaptación."""
    resumen = perfil['cv_summaries'].get('general') or next(iter(perfil['cv_summaries'].values()))
    return {'summary': resumen, 'experiences': [item['id'] for item in perfil['experience'][:4]], 'publications': [item['id'] for item in perfil['publications'][:2]],
            'projects': [item['id'] for item in perfil['projects'][:2]], 'skills': perfil['skills'][:4]}

def texto_perfil(perfil):
    """Todo lo verificado: marca el techo que ninguna adaptación honesta puede superar."""
    todo = {'summary': next(iter(perfil['cv_summaries'].values())), 'experiences': [item['id'] for item in perfil['experience']], 'publications': [item['id'] for item in perfil['publications']],
            'projects': [item['id'] for item in perfil['projects']], 'skills': perfil['skills'], 'tools': perfil.get('cv_tool_labels', []),
            'bullets': {item['id']: list(range(len(item['bullets']))) for item in perfil['experience']}}
    return texto_seleccion(todo, perfil) + '\n' + '\n'.join(perfil['cv_summaries'].values())

def paginas_pdf(ruta):
    return len(re.findall(rb'/Type\s*/Page\b', Path(ruta).read_bytes()))

def imprimir_html(origen, pdf, png):
    programa = navegador.impresor()
    if not programa: raise FileNotFoundError('Instala Chrome o Edge para generar el PDF.')
    with tempfile.TemporaryDirectory(prefix='postulador-') as perfil_temporal:
        base = [programa, '--headless=new', '--disable-gpu', '--no-first-run', '--user-data-dir=' + perfil_temporal]
        subprocess.run(base + ['--no-pdf-header-footer', '--print-to-pdf=' + str(pdf), Path(origen).as_uri()], check=True, capture_output=True, timeout=60)
        subprocess.run(base + ['--window-size=794,1123', '--hide-scrollbars', '--screenshot=' + str(png), Path(origen).as_uri()], check=True, capture_output=True, timeout=60)

def render_docx(docx, carpeta):
    motor = motor_docx.detect_renderer()
    if motor is None: return None, None
    pdf, png, paginas = motor_docx.convert(motor, docx, carpeta)
    return png, paginas

def generar(nombre, seleccion, idioma='es', motor='auto', plantilla='', ajustes=None):
    """Publica en cv/<nombre>/ solo lo que cabe en el tope de páginas; si no cabe, deja intacto lo anterior."""
    perfiles.exigir_revision(idioma)
    perfil = perfiles.leer(idioma)
    maximo = carreras.paginas_maximas(perfil)
    carpeta_nombre = slug(nombre)
    if not carpeta_nombre: raise ValueError('Nombre de CV inválido.')
    if motor == 'auto': motor = 'docx' if not plantilla and not ajustes and not perfil.get('carrera') and plantilla_docx(idioma).is_file() else 'html'
    if motor not in ('docx', 'html'): raise ValueError('Motor inválido: usa auto, docx o html.')
    archivo = 'CV_' + slug(perfil['name'])
    destino = carpeta_cv() / carpeta_nombre
    with tempfile.TemporaryDirectory(prefix='postulador-') as temporal:
        trabajo = Path(temporal)
        pdf, png = trabajo / 'preview.pdf', trabajo / 'preview.png'
        if motor == 'docx':
            docx = trabajo / (archivo + '.docx')
            motor_docx.write_docx(seleccion, docx, perfil, plantilla_docx(idioma), idioma)
            png_real, paginas = render_docx(docx, trabajo)
            if png_real is None and paginas is None: raise RuntimeError('Sin Word ni LibreOffice no se puede verificar la página; usa motor html.')
        else:
            validar(seleccion, perfil)
            ruta_plantilla = _ruta_plantilla(plantilla)
            ajustes = limpiar_ajustes(dict({'fuente': FUENTE_DEL_DISENO.get(ruta_plantilla.stem, AJUSTES['fuente'])}, **(ajustes or {})))
            (trabajo / 'cv.html').write_text(componer_html(seleccion, perfil, ruta_plantilla, idioma, ajustes), encoding='utf-8')
            (trabajo / 'ajustes.json').write_text(json.dumps(dict(ajustes, plantilla=ruta_plantilla.stem, idioma=idioma), ensure_ascii=False, indent=2), encoding='utf-8')
            imprimir_html(trabajo / 'cv.html', pdf, png)
            paginas = paginas_pdf(pdf)
        if not paginas or paginas > maximo:
            raise ValueError('El CV ocupa %s páginas y el tope es %d; quita viñetas, proyectos o publicaciones.' % (paginas, maximo))
        (trabajo / 'seleccion.json').write_text(json.dumps(seleccion, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(pdf, trabajo / (archivo + '.pdf'))
        for residuo in ('export.ps1', 'pages.txt'): (trabajo / residuo).unlink(missing_ok=True)
        destino.mkdir(parents=True, exist_ok=True)
        shutil.copytree(trabajo, destino, dirs_exist_ok=True)
    from . import ats
    final = destino / (archivo + '.pdf')
    revision = ats.revisar_pdf(final, seleccion, idioma)
    (destino / 'revision.json').write_text(json.dumps(revision, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'carpeta': str(destino), 'pdf': str(final), 'preview': str(destino / 'preview.png'), 'paginas': paginas, 'motor': motor, 'revision_ats': revision}

def _ruta_plantilla(plantilla):
    if not plantilla: return PLANTILLA_HTML
    for carpeta in (datos() / 'plantillas', PLANTILLAS):
        ruta = carpeta / (slug(plantilla) + '.html')
        if ruta.is_file() and ruta.stem != 'carta': return ruta
    raise FileNotFoundError('No existe la plantilla ' + plantilla)

def disenos():
    propios = {ruta.stem: 'Plantilla propia' for ruta in (datos() / 'plantillas').glob('*.html')} if (datos() / 'plantillas').is_dir() else {}
    return dict(DISENOS, **propios)

def _carpeta(nombre):
    carpeta = carpeta_cv() / slug(nombre)
    if not slug(nombre) or not carpeta.is_dir(): raise FileNotFoundError('No existe el CV ' + nombre)
    return carpeta

def leer_ajustes(nombre):
    archivo = _carpeta(nombre) / 'ajustes.json'
    return json.loads(archivo.read_text(encoding='utf-8')) if archivo.is_file() else {}

def idioma_de(seleccion):
    for archivo in sorted(datos().glob('perfil*.json')):
        if seleccion.get('summary') in json.loads(archivo.read_text(encoding='utf-8')).get('cv_summaries', {}).values():
            return archivo.stem.split('_')[1] if '_' in archivo.stem else 'es'
    raise ValueError('El resumen de este CV ya no está en tu perfil.')

def ajustar(nombre, cambios):
    """Cambia el aspecto sin tocar el contenido. Un CV de Word se conserva y se trabaja sobre una copia."""
    carpeta = _carpeta(nombre)
    seleccion = leer_seleccion(nombre)
    previos = leer_ajustes(nombre)
    plantilla = cambios.get('plantilla') or previos.get('plantilla') or 'columna'
    ajustes = limpiar_ajustes(dict({clave: previos[clave] for clave in AJUSTES if clave in previos}, **cambios))
    destino = carpeta.name + '_editado' if any(carpeta.glob('*.docx')) else carpeta.name
    return dict(generar(destino, seleccion, previos.get('idioma') or idioma_de(seleccion), 'html', plantilla, ajustes), nombre=destino)

def _archivo_comentarios(nombre): return _carpeta(nombre) / 'comentarios.json'

def _comentarios(nombre):
    archivo = _archivo_comentarios(nombre)
    return json.loads(archivo.read_text(encoding='utf-8')) if archivo.is_file() else []

def comentar(nombre, texto):
    if not texto.strip(): raise ValueError('Escribe el comentario.')
    lista = _comentarios(nombre)
    nuevo = {'id': max((item['id'] for item in lista), default=0) + 1, 'texto': texto.strip(), 'estado': 'pendiente', 'creado': time.strftime('%Y-%m-%d %H:%M'), 'nota': ''}
    _archivo_comentarios(nombre).write_text(json.dumps(lista + [nuevo], ensure_ascii=False, indent=2), encoding='utf-8')
    return nuevo

def comentarios_pendientes(nombre=''):
    carpetas = [_carpeta(nombre)] if nombre else [item for item in sorted(carpeta_cv().iterdir()) if item.is_dir()] if carpeta_cv().is_dir() else []
    return [dict(item, cv=carpeta.name) for carpeta in carpetas for item in _comentarios(carpeta.name) if item['estado'] == 'pendiente']

def resolver_comentario(nombre, id, nota=''):
    lista = _comentarios(nombre)
    item = next((comentario for comentario in lista if comentario['id'] == id), None)
    if item is None: raise ValueError('No existe el comentario %s.' % id)
    item.update(estado='resuelto', nota=nota)
    _archivo_comentarios(nombre).write_text(json.dumps(lista, ensure_ascii=False, indent=2), encoding='utf-8')
    return item

def detalle(nombre):
    carpeta = _carpeta(nombre)
    revision = json.loads((carpeta / 'revision.json').read_text(encoding='utf-8')) if (carpeta / 'revision.json').is_file() else {}
    return dict(_resumen(carpeta), revision=revision, ajustes=dict(AJUSTES, **leer_ajustes(nombre)), comentarios=_comentarios(nombre), disenos=disenos(), fuentes=FUENTES, posiciones_foto=POSICIONES_FOTO, tamanos=TAMANOS, hay_foto=archivo_foto() is not None)

def _resumen(carpeta):
    archivos = [item.name for item in carpeta.iterdir() if item.is_file()]
    pdf = next((nombre for nombre in sorted(archivos) if nombre.endswith('.pdf') and nombre != 'preview.pdf' and not nombre.startswith('Carta_')), 'preview.pdf' if 'preview.pdf' in archivos else None)
    return {'nombre': carpeta.name, 'archivos': sorted(archivos), 'pdf': pdf, 'docx': next((nombre for nombre in archivos if nombre.endswith('.docx')), None), 'carta': next((nombre for nombre in archivos if nombre.startswith('Carta_')), None),
            'preview': 'preview.png' in archivos, 'pendientes': sum(item['estado'] == 'pendiente' for item in _comentarios(carpeta.name)), 'version': int(carpeta.stat().st_mtime)}

def pdf_de(nombre):
    """PDF del CV `cv:<nombre>` que sube la puerta. Nunca la carta ni la vista previa."""
    if not isinstance(nombre, str) or not nombre or nombre != slug(nombre): raise ValueError('Nombre de CV inválido: usa el nombre exacto de cv_listar.')
    carpeta = carpeta_cv() / nombre
    if not carpeta.is_dir(): raise FileNotFoundError('No existe el CV %s.' % nombre)
    pdf = _resumen(carpeta)['pdf']
    if not pdf or pdf == 'preview.pdf': raise FileNotFoundError('El CV %s no tiene PDF.' % nombre)
    return carpeta / pdf

def generar_carta(nombre, texto, idioma='es'):
    """Carta de una página junto al CV temático; las cifras que no están en el perfil se señalan."""
    from . import ats
    perfiles.exigir_revision(idioma)
    perfil = perfiles.leer(idioma)
    if len(texto.split()) < 40: raise ValueError('La carta es demasiado breve.')
    destino = carpeta_cv() / slug(nombre)
    destino.mkdir(parents=True, exist_ok=True)
    archivo = destino / ('Carta_' + slug(perfil['name']) + '.pdf')
    parrafos = ''.join('<p>%s</p>' % html.escape(parrafo.strip()) for parrafo in texto.split('\n\n') if parrafo.strip())
    contacto = html.escape(' · '.join(perfil['contact'][:3]))
    contenido = PLANTILLA_CARTA.read_text(encoding='utf-8').replace('{{idioma}}', html.escape(idioma)).replace('{{nombre}}', html.escape(perfil['name'])).replace('{{contacto}}', contacto).replace('{{cuerpo}}', parrafos)
    with tempfile.TemporaryDirectory(prefix='postulador-') as temporal:
        trabajo = Path(temporal)
        (trabajo / 'carta.html').write_text(contenido, encoding='utf-8')
        imprimir_html(trabajo / 'carta.html', trabajo / 'carta.pdf', trabajo / 'carta.png')
        paginas = paginas_pdf(trabajo / 'carta.pdf')
        if paginas != 1: raise ValueError('La carta ocupa %d páginas; acórtala.' % paginas)
        os.replace(trabajo / 'carta.pdf', archivo)
    return {'pdf': str(archivo), 'cifras_sin_respaldo': ats.cifras_sin_respaldo(texto, perfil)}

def listar():
    if not carpeta_cv().is_dir(): return []
    carpetas = sorted((item for item in carpeta_cv().iterdir() if item.is_dir() and (item / 'seleccion.json').is_file()), key=lambda item: -item.stat().st_mtime)
    return [_resumen(carpeta) for carpeta in carpetas]

def leer_seleccion(nombre):
    return json.loads((carpeta_cv() / slug(nombre) / 'seleccion.json').read_text(encoding='utf-8'))
