"""Servidor MCP por stdio (JSON-RPC por líneas), sin dependencias: expone perfil, CV y registro a cualquier motor."""
import base64
import json
import sys
from pathlib import Path
from . import SKILL, __version__, actividad, aprobaciones, arranque, ats, busqueda, carreras, cv, datos, documentos, estricto, navegador, panel, perfil, portales, registro

TEXTO = {'type': 'string'}
ENTERO = {'type': 'integer'}
LISTA = {'type': 'array', 'items': {'type': 'object'}}
OBJETO = {'type': 'object'}
BOOLEANO = {'type': 'boolean'}

def _guia(nombre=''):
    if not nombre:
        return sorted(ruta.relative_to(SKILL).as_posix() for ruta in SKILL.rglob('*.md'))
    ruta = (SKILL / nombre).resolve()
    if not ruta.is_relative_to(SKILL.resolve()) or ruta.suffix != '.md' or not ruta.is_file(): raise FileNotFoundError('Guía inexistente: ' + nombre)
    return ruta.read_text(encoding='utf-8')

def _contexto():
    notas = datos() / 'notas.md'
    espera = registro.candado()
    return {'perfil_es': perfil.ruta('es').is_file(), 'perfil_en': perfil.ruta('en').is_file(), 'perfil_revisado': perfil.sello_vigente('es'),
            'notas': notas.read_text(encoding='utf-8') if notas.is_file() else '', 'cv': cv.listar(), 'navegador': navegador.activo(), 'busqueda': busqueda.leer(),
            'espera_envio': {'id': espera['id'], 'cargo': espera['cargo'], 'empresa': espera['empresa'], 'estado': espera['estado']} if espera else None}

def _registrar(**argumentos): return registro.registrar(actor='ia', **argumentos)
def _actualizar(**argumentos): return registro.actualizar(actor='ia', **argumentos)
def _seguimiento(**argumentos): return registro.seguimiento_hecho(actor='ia', **argumentos)
def _perfil_leer(idioma='es'): return perfil.leer(idioma, para_ia=True)
def _perfil_guardar(perfil_nuevo, idioma='es'): return perfil.guardar(perfil_nuevo, idioma, por='ia')
def _panel_abrir(): return panel.asegurar(abrir=True)

def _carrera_actual():
    try: return perfil.leer().get('carrera')
    except (OSError, ValueError): return None

def _generar(nombre, seleccion, idioma='es', motor='auto', plantilla='', ajustes=None):
    resultado = cv.generar(nombre, seleccion, idioma, motor, plantilla, ajustes)
    contenido = [{'type': 'text', 'text': json.dumps(resultado, ensure_ascii=False)}]
    imagen = Path(resultado['preview'])
    if imagen.is_file():
        contenido.append({'type': 'image', 'mimeType': 'image/png', 'data': base64.b64encode(imagen.read_bytes()).decode()})
    return contenido

def _plantilla_guardar(nombre, html):
    carpeta = datos() / 'plantillas'
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / (cv.slug(nombre) + '.html')
    ruta.write_text(html, encoding='utf-8')
    return {'plantilla': ruta.stem}

def _notas_agregar(texto):
    with (datos() / 'notas.md').open('a', encoding='utf-8') as archivo:
        archivo.write('\n- ' + texto.strip() + '\n')
    return {'guardada': True}

# nombre: (descripción, propiedades, requeridas, función)
HERRAMIENTAS = {
    'guia_leer': ('Lee una guía de la skill postulador. Sin nombre, lista las guías. Empieza por SKILL.md.', {'nombre': TEXTO}, [], _guia),
    'contexto_usuario': ('Estado del usuario: perfiles disponibles, notas personales, CV existentes, navegador y preferencias de búsqueda.', {}, [], _contexto),
    'diagnostico': ('Comprueba la instalación: carpeta de arranque, permisos, datos, versión y tope. Llámala al empezar cada sesión; si trae problemas, no busques ni rellenes.', {}, [], arranque.diagnostico),
    'perfil_leer': ('Lee el perfil verificado del usuario. Los campos sensibles llegan tapados: los escribe él en el panel.', {'idioma': TEXTO}, [], _perfil_leer),
    'perfil_guardar': ('Guarda el perfil completo, solo con hechos confirmados por el usuario. Después pídele que lo revise en el panel y pulse «Revisado».', {'perfil': OBJETO, 'idioma': TEXTO}, ['perfil'],
                       lambda perfil=None, idioma='es': _perfil_guardar(perfil, idioma)),
    'perfil_faltantes': ('Lo que falta en el perfil: datos base y campos obligatorios del paquete de carrera. Base de la entrevista.', {'idioma': TEXTO}, [], perfil.faltantes),
    'documentos_listar': ('Documentos que el usuario dejó en entrada/ y ya clasificó en el panel: id, tipo, nombre y si puedes leerlo. Nunca trae rutas.', {}, [], documentos.listar_para_ia),
    'documento_leer': ('Texto de un documento, solo si el usuario lo permitió en el panel (por ejemplo «Mi CV»). Los números de cédula llegan tapados.', {'id': ENTERO}, ['id'], documentos.leer),
    'notas_agregar': ('Añade a las notas personales un dato confirmado por el usuario.', {'texto': TEXTO}, ['texto'], _notas_agregar),
    'cv_listar': ('Lista los CV temáticos ya generados.', {}, [], cv.listar),
    'cv_leer_seleccion': ('Lee la selección de un CV existente, para partir de ella.', {'nombre': TEXTO}, ['nombre'], cv.leer_seleccion),
    'cv_generar': ('Genera un CV (una página, o hasta el tope del paquete de carrera del perfil) y devuelve rutas y vista previa. Exige el perfil revisado. Lee antes la guía referencias/cv.md.',
                   {'nombre': TEXTO, 'seleccion': OBJETO, 'idioma': TEXTO, 'motor': {'type': 'string', 'enum': ['auto', 'docx', 'html']}, 'plantilla': TEXTO, 'ajustes': OBJETO}, ['nombre', 'seleccion'], _generar),
    'cv_ajustar': ('Cambia diseño o aspecto de un CV sin tocar su contenido. cambios: plantilla, fuente, tamano, color, foto (ninguna, izquierda, derecha).', {'nombre': TEXTO, 'cambios': OBJETO}, ['nombre', 'cambios'], cv.ajustar),
    'cv_comentarios': ('Comentarios pendientes que el usuario dejó sobre sus CV en el panel.', {'nombre': TEXTO}, [], cv.comentarios_pendientes),
    'cv_comentario_resuelto': ('Marca un comentario como atendido y explica qué se hizo.', {'nombre': TEXTO, 'id': ENTERO, 'nota': TEXTO}, ['nombre', 'id'], cv.resolver_comentario),
    'plantilla_guardar': ('Guarda una plantilla HTML de CV con marcas {{nombre}}, {{resumen}}, etc.', {'nombre': TEXTO, 'html': TEXTO}, ['nombre', 'html'], _plantilla_guardar),
    'postulacion_registrar': ('Registra una postulación; avisa si ya existe una igual. Antes de rellenar un formulario, regístrala como preparada.',
                              {'cargo': TEXTO, 'empresa': TEXTO, 'sitio': TEXTO, 'estado': {'type': 'string', 'enum': list(registro.ESTADOS)}, 'url': TEXTO, 'modalidad': TEXTO, 'cv': TEXTO, 'nota': TEXTO, 'permitir_duplicado': BOOLEANO, 'idoneidad': ENTERO, 'ats_base': ENTERO, 'ats_adaptado': ENTERO, 'ats_techo': ENTERO},
                              ['cargo', 'empresa', 'sitio', 'estado'], _registrar),
    'postulacion_actualizar': ('Cambia el estado de una postulación. En rechazos y descartes indica motivo. Si ves la confirmación del portal, usa reportada: el usuario la confirma en el panel.', {'id': ENTERO, 'estado': {'type': 'string', 'enum': list(registro.ESTADOS)}, 'nota': TEXTO, 'motivo': TEXTO}, ['id', 'estado'], _actualizar),
    'ats_evaluar': ('Calcula idoneidad en porcentaje y compara CV base, adaptado y techo del perfil. requisitos: lista de {texto (cita literal de la oferta), excluyente, estado: cumple|parcial|por_confirmar|brecha, evidencia (cita literal del perfil o notas)}.',
                    {'oferta': TEXTO, 'titulo': TEXTO, 'requisitos': LISTA, 'seleccion': OBJETO, 'idioma': TEXTO}, ['oferta', 'titulo', 'requisitos', 'seleccion'], ats.evaluar),
    'analisis_rechazos': ('Embudo y tasas de respuesta por sitio, CV e idoneidad, con motivos de rechazo.', {}, [], registro.analisis),
    'seguimientos_pendientes': ('Postulaciones enviadas a las que toca hacer seguimiento.', {'limite': ENTERO}, [], registro.seguimientos_pendientes),
    'seguimiento_hecho': ('Registra un seguimiento y programa el siguiente, si queda.', {'id': ENTERO, 'nota': TEXTO}, ['id'], _seguimiento),
    'postulaciones_listar': ('Consulta postulaciones por estado o texto.', {'estado': TEXTO, 'texto': TEXTO, 'limite': ENTERO}, [], registro.listar),
    'historial_buscar': ('Busca en los registros importados, para no repetir postulaciones ni contradecir respuestas.', {'texto': TEXTO, 'limite': ENTERO}, ['texto'], registro.buscar_historial),
    'respuesta_guardar': ('Guarda la respuesta del usuario a una pregunta de formulario para reutilizarla.', {'pregunta': TEXTO, 'respuesta': TEXTO}, ['pregunta', 'respuesta'], registro.guardar_respuesta),
    'respuestas_buscar': ('Busca respuestas ya dadas a preguntas de formularios.', {'texto': TEXTO}, [], registro.buscar_respuestas),
    'carta_generar': ('Genera una carta de presentación de una página junto al CV temático. texto: párrafos separados por línea en blanco.', {'nombre': TEXTO, 'texto': TEXTO, 'idioma': TEXTO}, ['nombre', 'texto'], cv.generar_carta),
    'busqueda_preferencias': ('Preferencias de búsqueda del usuario: antigüedad máxima en horas, modalidades, ubicaciones, cargos, palabras a excluir, salario mínimo e idiomas. Úsalas siempre al buscar. Solo el usuario las cambia, en Ajustes del panel.', {}, [], busqueda.leer),
    'linkedin_url': ('Dirección de resultados de LinkedIn con las preferencias del usuario (antigüedad y modalidad ya aplicadas), 10 ofertas por página.', {'palabras': TEXTO, 'ubicacion': TEXTO, 'pagina': ENTERO}, ['palabras'], busqueda.url_linkedin),
    'ofertas_tableros': ('Busca en los tableros públicos configurados de Greenhouse, Lever y Ashby.', {'texto': TEXTO, 'ubicacion': TEXTO, 'limite': ENTERO}, [], portales.buscar),
    'aprobacion_solicitar': ('Pide la firma del usuario para enviar una postulación. detalle: respuestas dadas y datos relevantes.', {'url': TEXTO, 'cargo': TEXTO, 'empresa': TEXTO, 'cv': TEXTO, 'detalle': TEXTO, 'idoneidad': ENTERO}, ['url', 'cargo', 'empresa'], aprobaciones.solicitar),
    'aprobacion_consultar': ('Estado de una solicitud: pendiente, aprobada, rechazada o usada.', {'id': ENTERO}, ['id'], aprobaciones.consultar),
    'aprobaciones_listar': ('Lista solicitudes por estado.', {'estado': TEXTO}, [], aprobaciones.listar),
    'informe_guardar': ('Deja un documento Markdown en datos_usuario/informes/, visible en el editor y en el panel.', {'titulo': TEXTO, 'contenido': TEXTO}, ['titulo', 'contenido'], actividad.guardar_informe),
    'panel_abrir': ('Abre el panel en el navegador normal del usuario (lo inicia si está cerrado) y devuelve su dirección.', {}, [], _panel_abrir),
    'politica_consultar': ('Nivel de autonomía efectivo de un sitio, ya limitado por el tope de este equipo. Obligatorio antes de enviar nada. Solo el usuario lo cambia, en Ajustes del panel.', {'sitio': TEXTO}, ['sitio'], registro.consultar_politica),
    'navegador_abrir': ('Abre el navegador dedicado y su servicio de control si están cerrados.', {}, [], navegador.asegurar_mcp),
    'navegador_disponibles': ('Lista los navegadores instalados. Solo el usuario elige cuál usar, en Ajustes del panel.', {}, [], navegador.disponibles),
}

# En el equipo de la persona (tope solo_rellenar o menos) no existen: la IA no aprueba envíos, no escribe plantillas
# HTML (podrían leer archivos locales al imprimirse) ni marca seguimientos.
OCULTAS_CON_TOPE = ('aprobacion_solicitar', 'aprobacion_consultar', 'aprobaciones_listar', 'plantilla_guardar', 'seguimiento_hecho')
OCULTAS_EN_DERECHO = ('ats_evaluar',)

def _disponibles():
    ocultas = set(OCULTAS_CON_TOPE) if estricto() else set()
    if _carrera_actual() == 'derecho': ocultas |= set(OCULTAS_EN_DERECHO)
    return [nombre for nombre in HERRAMIENTAS if nombre not in ocultas]

def _esquema(nombre, propiedades):
    if nombre in ('postulacion_registrar', 'postulacion_actualizar') and estricto():
        estados = registro.REGISTRO_IA if nombre == 'postulacion_registrar' else registro.ESTADOS_IA
        return dict(propiedades, estado={'type': 'string', 'enum': list(estados)})
    return propiedades

def _lista_herramientas():
    return [{'name': nombre, 'description': HERRAMIENTAS[nombre][0], 'inputSchema': {'type': 'object', 'properties': _esquema(nombre, HERRAMIENTAS[nombre][1]), 'required': HERRAMIENTAS[nombre][2]}}
            for nombre in _disponibles()]

def _llamar(nombre, argumentos):
    if nombre not in HERRAMIENTAS or nombre not in _disponibles(): return {'content': [{'type': 'text', 'text': 'Herramienta desconocida: ' + str(nombre)}], 'isError': True}
    sobrantes = sorted(set(argumentos) - set(HERRAMIENTAS[nombre][1]))
    if sobrantes: return {'content': [{'type': 'text', 'text': 'ValueError: argumento no permitido: ' + ', '.join(map(str, sobrantes))}], 'isError': True}
    try:
        resultado = HERRAMIENTAS[nombre][3](**argumentos)
        actividad.anotar(nombre)
    except Exception as error:
        actividad.anotar(nombre, error=True)
        return {'content': [{'type': 'text', 'text': '%s: %s' % (type(error).__name__, error)}], 'isError': True}
    if isinstance(resultado, list) and resultado and isinstance(resultado[0], dict) and 'type' in resultado[0]:
        return {'content': resultado}
    texto = resultado if isinstance(resultado, str) else json.dumps(resultado, ensure_ascii=False)
    return {'content': [{'type': 'text', 'text': texto}]}

def atender(mensaje):
    """Devuelve la respuesta JSON-RPC, o None si el mensaje es una notificación."""
    metodo, parametros = mensaje.get('method'), mensaje.get('params') or {}
    if 'id' not in mensaje: return None
    if metodo == 'initialize':
        resultado = {'protocolVersion': parametros.get('protocolVersion', '2025-06-18'), 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'postulador', 'version': __version__}}
    elif metodo == 'tools/list': resultado = {'tools': _lista_herramientas()}
    elif metodo == 'tools/call': resultado = _llamar(parametros.get('name'), parametros.get('arguments') or {})
    elif metodo == 'ping': resultado = {}
    else: return {'jsonrpc': '2.0', 'id': mensaje['id'], 'error': {'code': -32601, 'message': 'Método no disponible: %s' % metodo}}
    return {'jsonrpc': '2.0', 'id': mensaje['id'], 'result': resultado}

def main():
    if '--con-panel' in sys.argv: panel.asegurar()
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8', newline='\n')
    for linea in sys.stdin:
        if not linea.strip(): continue
        try:
            respuesta = atender(json.loads(linea))
        except ValueError:
            respuesta = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'JSON inválido.'}}
        if respuesta is not None:
            print(json.dumps(respuesta, ensure_ascii=False), flush=True)

if __name__ == '__main__': main()
