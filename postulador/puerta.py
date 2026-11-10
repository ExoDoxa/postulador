"""Puerta MCP entre el motor y Playwright: el agente no puede pulsar «enviar» sin el permiso que fija el sitio.

Lee las referencias de cada captura de página, así que la etiqueta real del botón la da el navegador y no el
agente. Ante la duda bloquea: solo pasan las herramientas de una lista fija, el navegador no abre direcciones
del propio equipo (el panel donde se aprueba), no ejecuta código en la página, solo sube CV (`cv:<nombre>`), y
nunca paga ni marca declaraciones juradas, en ningún nivel.

En el equipo de la persona (tope solo_rellenar) suma tres reglas:
- mientras un formulario está a medio rellenar (hay borrador), bloquea todo clic sobre un botón, Enter, espacio y
  todo diálogo aceptado, salvo los pasos que el autor marque como seguros para ese sitio;
- `formulario_listo` guarda el comprobante de lo que rellenó el asistente y pasa la postulación a `rellenada`;
- candado: mientras alguna postulación espera que ella la envíe, solo deja leer. Se consulta en la base en cada
  acción, así que vale en una puerta recién arrancada y con dos chats a la vez.
Es una barrera fuerte, no absoluta: un elemento que no es botón y envía con JavaScript puede pasar.
"""
import base64
import hashlib
import ipaddress
import json
import re
import socket
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from . import actividad, aprobaciones, comprobantes, cv, datos, navegador, registro

ENVIO = re.compile(r'\b(enviar|env[ií]a|env[ií]o|enviar solicitud|enviar respuestas|enviar postulaci[oó]n|postular(?:me|se)?|inscribir(?:me|se)|radicar|confirmar inscripci[oó]n|'
                   r'submit|send application|send|finalizar postulaci[oó]n|finish application|confirmar postulaci[oó]n|completar postulaci[oó]n)\b', re.I)
ENVIO_POR_SITIO = {'magneto365.com': re.compile(r'\baplicar\b', re.I), 'torre.ai': re.compile(r'\b(aplicar|apply)\b', re.I)}
# Pagos y declaraciones juradas los hace siempre la persona: ninguna aprobación ni nivel lo desbloquea.
NUNCA = re.compile(r'juramento|juramentad|declaro bajo|\bpagar\b|realizar (?:el )?pago|\bpse\b|pay now|\bsworn\b|under penalty of perjury', re.I)
DOMINIOS_PAGO = ('pse.com.co', 'achcolombia.com.co')
PUERTOS_PROPIOS = {8770, navegador.PUERTO, navegador.PUERTO_MCP}
CAPTURA = re.compile(r'-\s+([\w-]+)(?:\s+"([^"\n]*)")?[^\n]*\[ref=(\w+)\]')
URL_PAGINA = re.compile(r'Page URL:\s*(\S+)|\(current\) \[[^\n]*\]\((\S+)\)')
ESCRITURA = ('browser_type', 'browser_fill_form', 'browser_select_option', 'browser_file_upload', 'browser_drop', 'browser_drag')
NAVEGACION = ('browser_navigate', 'browser_tabs', 'browser_navigate_back', 'browser_close')
LECTURA = ('browser_snapshot', 'browser_take_screenshot', 'browser_wait_for', 'browser_console_messages', 'browser_network_requests',
           'browser_network_request', 'browser_find', 'browser_hover', 'browser_resize')
# Lista fija para @playwright/mcp de navegador.PLAYWRIGHT_MCP. Una herramienta nueva o de código (evaluate, run_code) no pasa.
PERMITIDAS = frozenset(ESCRITURA + NAVEGACION + LECTURA + ('browser_click', 'browser_press_key', 'browser_handle_dialog'))
TECLAS_ENVIO = {'enter', 'numpadenter', ' ', 'space', 'spacebar'}
SIN_PERMISO = 'BLOQUEADO por la puerta de envío. Sitio en nivel %s: «%s». %s No intentes otra forma de enviar.'
PROHIBIDO = 'BLOQUEADO por la puerta de envío: %s. El asistente no puede hacerlo en ningún caso; si hace falta, dile al usuario qué paso le toca a él. No intentes otra forma.'
PEDIR = 'Deja el formulario listo, llama a aprobacion_solicitar con la URL y detén esta postulación hasta que el usuario apruebe.'
AVISAR = 'Deja el formulario listo, llama a formulario_listo con el id de la postulación y dile al usuario que revise el navegador y pulse Enviar él mismo.'
# Botones intermedios que no envían, por sitio ({dominio: expresión}). Vacío hasta la sesión con la persona: ella pulsa «Siguiente».
PASO_SEGURO_POR_SITIO = {}
# Un campo de archivo aparece en la lectura de la página como un botón (capturado en A0, Playwright MCP 0.0.84).
# Hay que pulsarlo para que browser_file_upload pueda subir el CV. Nunca vale si la etiqueta suena a envío.
BOTON_ARCHIVO = re.compile(r'\b(hoja de vida|curr[ií]cul\w*|\bcv\b|adjunt\w*|archivo|documento|subir|cargar|examinar|seleccionar|elegir|upload|attach|resume|browse|choose file)\b', re.I)
SOLO_LECTURA = ('browser_snapshot', 'browser_take_screenshot', 'browser_wait_for')
CANDADO = ('BLOQUEADO por la puerta: la postulación a «%s» en %s espera que el usuario la envíe. Mientras no la resuelva en el panel '
           '(«La envié», «No, ya no» o «Que el asistente la corrija»), solo puedes leer la página. Díselo y espera.')
UN_BORRADOR = ('BLOQUEADO por la puerta: hay un formulario a medio rellenar en %s. Termina con formulario_listo o, si la oferta no '
               'encaja, llama a formulario_abandonar antes de escribir en otra página.')
CLIC_CON_BORRADOR = ('BLOQUEADO por la puerta: mientras rellenas un formulario no puedes pulsar botones (%s). Si es «Siguiente» o '
                     '«Continuar», pídele al usuario que lo pulse y sigue en la página nueva. El envío siempre lo hace el usuario.')
SOLO_CV = 'solo puedes subir un CV con cv:<nombre> (el nombre exacto de cv_listar); los diplomas y otros documentos los sube el usuario'
CLICS = ('browser_click', 'browser_drag', 'browser_drop')
PROPIAS = [
    {'name': 'formulario_listo', 'description': 'Llámala cuando termines de rellenar un formulario. La puerta guarda el comprobante de lo que rellenaste, '
     'pasa la postulación a rellenada y no deja escribir más hasta que el usuario la envíe y la resuelva en el panel.',
     'inputSchema': {'type': 'object', 'properties': {'postulacion_id': {'type': 'integer'}}, 'required': ['postulacion_id']}},
    {'name': 'formulario_abandonar', 'description': 'Cierra el formulario a medio rellenar sin comprobante, por ejemplo si la oferta no encaja. '
     'Después pasa la postulación a incompleta o descartada con postulacion_actualizar.',
     'inputSchema': {'type': 'object', 'properties': {}}},
]

def es_envio(url, etiqueta):
    extra = next((patron for sitio, patron in ENVIO_POR_SITIO.items() if registro.coincide(url, sitio)), None)
    return bool(ENVIO.search(etiqueta) or (extra and extra.search(etiqueta)))

def _ip(host):
    """IP del host si es una dirección literal, también en formas abreviadas como 127.1 o 2130706433."""
    try: return ipaddress.ip_address(host)
    except ValueError: pass
    try: return ipaddress.ip_address(socket.inet_ntoa(socket.inet_aton(host)))
    except OSError: return None

def url_prohibida(url):
    """Motivo por el que el navegador del asistente no debe abrir esa dirección, o None."""
    url = (url or '').strip()
    if not url or url.lower() == 'about:blank': return None
    partes = urlsplit(url)
    if partes.scheme.lower() not in ('http', 'https'): return 'dirección %s: solo se abren páginas web' % (partes.scheme or 'sin esquema')
    host = (partes.hostname or '').lower()
    ip = _ip(host)
    try: puerto = partes.port
    except ValueError: return 'dirección mal formada'
    if not host or host == 'localhost' or host.endswith('.localhost') or (ip and (ip.is_loopback or ip.is_unspecified or ip.is_link_local)) or puerto in PUERTOS_PROPIOS:
        return 'dirección del propio equipo (%s): el panel y los servicios locales solo los usa el usuario' % (partes.netloc or url)
    if any(registro.coincide(url, dominio) for dominio in DOMINIOS_PAGO): return 'página de pago'
    return None

def ruta_ajena(ruta):
    """True si el archivo no está en la carpeta de CV del usuario."""
    try: real = Path(ruta).resolve()
    except (OSError, ValueError): return True
    return not real.is_relative_to((datos() / 'cv').resolve())

def host(url): return registro.host_de(url or '')

def paso_seguro(url, etiqueta):
    patron = next((patron for sitio, patron in PASO_SEGURO_POR_SITIO.items() if registro.coincide(url, sitio)), None)
    return bool(patron and patron.search(etiqueta))

def traducir_rutas(argumentos):
    """Cambia cada `cv:<nombre>` por la ruta real del PDF. Devuelve (argumentos, nombres de CV) o lanza ValueError."""
    if 'paths' not in argumentos: return argumentos, []
    rutas = argumentos['paths'] if isinstance(argumentos['paths'], list) else [argumentos['paths']]
    reales, nombres = [], []
    for ruta in rutas:
        encontrado = re.fullmatch(r'cv:(.+)', str(ruta))
        if not encontrado: raise ValueError(SOLO_CV)
        try: reales.append(str(cv.pdf_de(encontrado.group(1))))
        except (ValueError, FileNotFoundError) as error: raise ValueError('%s (%s)' % (SOLO_CV, error))
        nombres.append(encontrado.group(1))
    return dict(argumentos, paths=reales), nombres

class Puerta:
    def __init__(self):
        self.url, self.etiquetas, self.firma, self.recien_firmada = '', {}, None, False
        self.pestana_propia = False
        self.borrador = None

    def abrir_borrador(self):
        if self.borrador is None:
            self.borrador = {'url': self.url, 'host': host(self.url), 'inicio': registro.ahora_segundos(), 'campos': [], 'clics': [],
                             'archivos': [], 'cv': '', 'envios_bloqueados': 0}
        return self.borrador

    def nombre_de(self, ref, dicho=''):
        """Etiqueta del elemento según la lectura de la página; si no está, la que dio la IA, marcada."""
        if ref is not None and str(ref) in self.etiquetas: return self.etiquetas[str(ref)]
        return ('%s (etiqueta según la IA)' % dicho) if dicho else 'elemento sin identificar (etiqueta según la IA)'

    def anotar(self, herramienta, argumentos, archivos=()):
        """Tras una acción que pasó: la deja en el borrador. Las escrituras lo abren; los clics solo se anotan si ya hay uno."""
        if herramienta not in ESCRITURA and (herramienta not in CLICS or self.borrador is None): return
        borrador, hora = self.abrir_borrador(), time.strftime('%H:%M:%S')
        objetivo = argumentos.get('target') or argumentos.get('ref')
        if herramienta == 'browser_fill_form':
            for campo in argumentos.get('fields') or []:
                if isinstance(campo, dict):
                    borrador['campos'].append({'campo': self.nombre_de(campo.get('ref') or campo.get('target'), campo.get('name', '')), 'valor': str(campo.get('value', ''))[:2000], 'hora': hora})
        elif herramienta in ('browser_type', 'browser_select_option'):
            valor = argumentos.get('text') if herramienta == 'browser_type' else ', '.join(map(str, argumentos.get('values') or []))
            borrador['campos'].append({'campo': self.nombre_de(objetivo, argumentos.get('element', '')), 'valor': str(valor or '')[:2000], 'hora': hora})
        elif herramienta in CLICS:
            borrador['clics'].append({'elemento': self.nombre_de(objetivo or argumentos.get('startRef') or argumentos.get('endRef'), argumentos.get('element', '')), 'hora': hora})
        for nombre, ruta in archivos:
            try: huella = hashlib.sha256(Path(ruta).read_bytes()).hexdigest()
            except OSError: huella = ''
            borrador['archivos'].append({'archivo': Path(ruta).name, 'cv': nombre, 'sha256': huella, 'ruta': str(ruta), 'hora': hora})
            borrador['cv'] = borrador['cv'] or nombre

    def observar(self, texto):
        """Aprende de cada respuesta del navegador en qué página está y qué hay en ella."""
        pagina = URL_PAGINA.search(texto)
        if pagina: self.url = pagina.group(1) or pagina.group(2)
        encontradas = CAPTURA.findall(texto)
        if encontradas: self.etiquetas = {ref: (rol + ' ' + nombre).strip() for rol, nombre, ref in encontradas}

    def hay_envio(self):
        return any(es_envio(self.url, etiqueta) for etiqueta in self.etiquetas.values())

    def etiqueta(self, objetivo):
        return self.etiquetas.get(str(objetivo or ''), str(objetivo or ''))

    def prohibido(self, herramienta, argumentos):
        """Motivo de un bloqueo que ningún nivel ni aprobación levanta, o None."""
        if herramienta not in PERMITIDAS: return 'la herramienta %s no está permitida' % herramienta
        if url_prohibida(self.url) and herramienta not in NAVEGACION: return 'la página actual es una %s' % url_prohibida(self.url)
        if herramienta in ('browser_navigate', 'browser_tabs') and argumentos.get('url'):
            motivo = url_prohibida(str(argumentos['url']))
            if motivo: return motivo
        rutas = argumentos.get('paths') or []
        if any(ruta_ajena(ruta) for ruta in (rutas if isinstance(rutas, list) else [rutas])):
            return SOLO_CV
        textos = [self.etiqueta(argumentos.get('target') or argumentos.get('ref')), str(argumentos.get('element', ''))]
        textos += [str(valor) for valor in (argumentos.get('values') or [])]
        for campo in argumentos.get('fields') or []:
            if isinstance(campo, dict): textos += [str(campo.get('name', '')), self.etiqueta(campo.get('ref') or campo.get('target'))]
        if herramienta in ('browser_click', 'browser_fill_form', 'browser_select_option', 'browser_type', 'browser_press_key') and any(NUNCA.search(texto) for texto in textos):
            return 'pagos y declaraciones juradas los hace siempre el usuario'
        return None

    def riesgo(self, herramienta, argumentos):
        """Texto del envío que se intenta, o None si la acción no envía nada."""
        if herramienta == 'browser_click':
            objetivo = str(argumentos.get('target') or argumentos.get('ref') or '')
            etiqueta = ' '.join(filter(None, (self.etiqueta(objetivo), argumentos.get('element', ''))))
            if es_envio(self.url, etiqueta): return etiqueta
            if self.etiquetas.get(objetivo) == 'button': return 'botón sin nombre'
            # target también acepta selectores: lo que no se puede identificar no pasa si la página puede enviar.
            return 'clic sobre un selector sin identificar' if objetivo not in self.etiquetas and self.hay_envio() else None
        if herramienta == 'browser_press_key' and str(argumentos.get('key', '')).lower() in TECLAS_ENVIO and self.hay_envio(): return 'tecla que envía un formulario'
        if herramienta == 'browser_type' and argumentos.get('submit') and self.hay_envio(): return 'escritura con envío'
        if herramienta == 'browser_handle_dialog' and argumentos.get('accept') and self.hay_envio(): return 'aceptar un diálogo de confirmación'
        return None

    def boton(self, herramienta, argumentos):
        """Con un borrador abierto: qué clic o tecla podría enviar, o None. Solo pasan los pasos seguros del sitio."""
        if herramienta == 'browser_click':
            objetivo = str(argumentos.get('target') or argumentos.get('ref') or '')
            etiqueta = self.etiquetas.get(objetivo)
            if etiqueta is None: return 'clic sobre un elemento sin identificar'
            if etiqueta.split(' ', 1)[0] != 'button' or paso_seguro(self.url, etiqueta): return None
            nombre = etiqueta[7:]
            if nombre and BOTON_ARCHIVO.search(nombre) and not es_envio(self.url, etiqueta): return None
            return 'botón «%s»' % (nombre or 'sin nombre')
        if herramienta == 'browser_press_key' and str(argumentos.get('key', '')).lower() in TECLAS_ENVIO: return 'tecla %s' % argumentos.get('key')
        if herramienta == 'browser_type' and argumentos.get('submit'): return 'escritura con envío'
        if herramienta == 'browser_handle_dialog' and argumentos.get('accept'): return 'aceptar un diálogo'
        return None

    def decidir(self, herramienta, argumentos):
        """Devuelve el mensaje de bloqueo, o None si la acción puede pasar."""
        recien_firmada, self.recien_firmada = self.recien_firmada, False
        motivo = self.prohibido(herramienta, argumentos)
        if motivo: return PROHIBIDO % motivo
        espera = registro.candado()
        if espera and not (herramienta in SOLO_LECTURA or (herramienta == 'browser_tabs' and argumentos.get('action') == 'list')):
            return CANDADO % (espera['cargo'], espera['empresa'])
        if self.borrador and (herramienta in ESCRITURA or herramienta in CLICS) and host(self.url) != self.borrador['host']:
            return UN_BORRADOR % (self.borrador['host'] or 'otra página')
        # El diálogo «¿confirmas el envío?» que abre un envío ya aprobado no pide una segunda firma.
        if herramienta == 'browser_handle_dialog' and recien_firmada: return None
        nivel = registro.nivel_de_url(self.url)
        if self.borrador and nivel in ('solo_rellenar', 'solo_preparar'):
            intento = self.boton(herramienta, argumentos)
            if intento:
                self.borrador['envios_bloqueados'] += 1
                return CLIC_CON_BORRADOR % intento
        if nivel == 'enviar_solo': return None
        if nivel == 'solo_preparar' and herramienta in ESCRITURA:
            return SIN_PERMISO % (nivel, herramienta, 'En este sitio no se rellena nada: entrega el CV y las respuestas al usuario.')
        intento = self.riesgo(herramienta, argumentos)
        if intento is None: return None
        if nivel == 'aprobar':
            self.firma = aprobaciones.consumir(self.url)
            return None if self.firma else SIN_PERMISO % (nivel, intento, PEDIR)
        return SIN_PERMISO % (nivel, intento, AVISAR)

class Servicio:
    """Cliente mínimo de MCP por HTTP hacia el servicio de Playwright."""
    def __init__(self, url=navegador.URL_MCP):
        self.url, self.sesion, self.siguiente = url, None, 0

    def enviar(self, mensaje):
        cabeceras = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
        if self.sesion: cabeceras['Mcp-Session-Id'] = self.sesion
        peticion = urllib.request.Request(self.url, json.dumps(mensaje).encode('utf-8'), cabeceras)
        with urllib.request.urlopen(peticion, timeout=120) as respuesta:
            self.sesion = respuesta.headers.get('Mcp-Session-Id') or self.sesion
            if 'id' not in mensaje: return None
            if 'event-stream' not in respuesta.headers.get('Content-Type', ''): return json.load(respuesta)
            for linea in respuesta:
                if not linea.startswith(b'data:'): continue
                dato = json.loads(linea[5:])
                if dato.get('id') == mensaje['id']: return dato
        raise ConnectionError('El servicio del navegador no respondió.')

    def iniciar(self):
        self.enviar({'jsonrpc': '2.0', 'id': 'inicio', 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'postulador', 'version': '0.2.0'}}})
        self.enviar({'jsonrpc': '2.0', 'method': 'notifications/initialized'})

def texto_de(respuesta):
    contenido = (respuesta.get('result') or {}).get('content') or []
    return '\n'.join(parte.get('text', '') for parte in contenido if parte.get('type') == 'text')

HERRAMIENTAS_GUARDADAS = Path(__file__).with_name('playwright_herramientas.json')

def herramientas_guardadas():
    """Lista de herramientas de Playwright MCP guardada para navegador.PLAYWRIGHT_MCP, ya filtrada; None si no sirve."""
    try: guardado = json.loads(HERRAMIENTAS_GUARDADAS.read_text(encoding='utf-8'))
    except (OSError, ValueError): return None
    if guardado.get('version') != navegador.PLAYWRIGHT_MCP: return None
    return [herramienta for herramienta in guardado.get('tools') or [] if herramienta.get('name') in PERMITIDAS]

def _texto(identificador, texto, error=False):
    resultado = {'content': [{'type': 'text', 'text': texto}]}
    if error: resultado['isError'] = True
    return {'jsonrpc': '2.0', 'id': identificador, 'result': resultado}

def imagen_de(respuesta):
    """PNG de la respuesta de browser_take_screenshot: como contenido image en base64 o como archivo guardado."""
    for parte in (respuesta.get('result') or {}).get('content') or []:
        if parte.get('type') == 'image' and parte.get('data'):
            try: return base64.b64decode(parte['data'])
            except ValueError: continue
    for ruta in re.findall(r'([A-Za-z]:[\\/][^\s"\'`)\]]+\.png|/[^\s"\'`)\]]+\.png)', texto_de(respuesta)):
        try: return Path(ruta).read_bytes()
        except OSError: continue
    return None

def formulario_listo(puerta, servicio, argumentos):
    """Comprobante de lo que rellenó el asistente. Precondiciones: un borrador abierto y la postulación en `preparada`."""
    if puerta.borrador is None:
        return 'No hay un formulario rellenado en esta sesión de la puerta. Rellena el formulario primero; si ya lo rellenaste y la puerta se reinició, vuelve a escribir un campo.', True
    try:
        postulacion = registro.obtener(int(argumentos.get('postulacion_id')))
    except (TypeError, ValueError) as error:
        return 'Indica postulacion_id, el id que devolvió postulacion_registrar. (%s)' % error, True
    if postulacion['estado'] != 'preparada':
        return 'La postulación %s está %s: formulario_listo solo vale para una postulación preparada. Regístrala como preparada antes de rellenar.' % (postulacion['id'], postulacion['estado']), True
    captura = servicio.enviar({'jsonrpc': '2.0', 'id': 'comprobante', 'method': 'tools/call',
                               'params': {'name': 'browser_take_screenshot', 'arguments': {'type': 'png', 'fullPage': True}}})
    imagen = imagen_de(captura or {})
    borrador = puerta.borrador
    resultado = comprobantes.crear(postulacion['id'], puerta.url or borrador['url'], borrador['inicio'], borrador['campos'], borrador['clics'],
                                   borrador['archivos'], borrador['cv'], imagen, borrador['envios_bloqueados'])
    puerta.borrador = None
    actividad.anotar('formulario_listo', puerta.url)
    aviso = '' if imagen else ' No pude guardar la imagen de la página; el comprobante tiene los campos.'
    return ('Listo: guardé el comprobante %d y la postulación quedó lista para enviar.%s Dile al usuario: «Revisa la ventana del navegador, '
            'corrige lo que quieras y pulsa Enviar tú. Después márcalo en el panel». Hasta que lo resuelva, solo puedes leer.' % (resultado['comprobante'], aviso)), False

def formulario_abandonar(puerta):
    if puerta.borrador is None: return 'No hay un formulario a medio rellenar.', False
    actividad.anotar('formulario_abandonar', puerta.borrador['url'])
    puerta.borrador = None
    return 'Cerré el formulario sin comprobante. Pasa la postulación a incompleta o descartada con postulacion_actualizar.', False

def atender(mensaje, puerta, servicio):
    metodo, identificador = mensaje.get('method'), mensaje.get('id')
    if identificador is None: return None
    if metodo == 'initialize':
        version = (mensaje.get('params') or {}).get('protocolVersion', '2025-06-18')
        return {'jsonrpc': '2.0', 'id': identificador, 'result': {'protocolVersion': version, 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'playwright-con-puerta', 'version': '0.3.0'}}}
    if metodo == 'ping': return {'jsonrpc': '2.0', 'id': identificador, 'result': {}}
    if metodo == 'tools/list' and servicio.sesion is None:
        # Responde al instante con la lista guardada para la versión fija de Playwright: el navegador se abre en la
        # primera acción. Si no, el motor espera a que arranque y la IA cree que la puerta no existe.
        guardadas = herramientas_guardadas()
        if guardadas is not None: return {'jsonrpc': '2.0', 'id': identificador, 'result': {'tools': guardadas + PROPIAS}}
    parametros = mensaje.get('params') or {}
    nombre, argumentos = parametros.get('name', ''), parametros.get('arguments') or {}
    if metodo == 'tools/call' and nombre == 'formulario_abandonar': return _texto(identificador, *formulario_abandonar(puerta))
    if metodo == 'tools/call' and nombre == 'formulario_listo' and puerta.borrador is None: return _texto(identificador, *formulario_listo(puerta, servicio, argumentos))
    if servicio.sesion is None:
        navegador.asegurar_mcp()
        servicio.iniciar()
    subidos = []
    if metodo == 'tools/call':
        if nombre == 'formulario_listo': return _texto(identificador, *formulario_listo(puerta, servicio, argumentos))
        try: argumentos, nombres_cv = traducir_rutas(argumentos)
        except ValueError as error:
            actividad.anotar(nombre, puerta.url, bloqueada=True)
            return _texto(identificador, PROHIBIDO % error, True)
        motivo = puerta.decidir(nombre, argumentos)
        if motivo:
            actividad.anotar(nombre, puerta.url, bloqueada=True)
            return _texto(identificador, motivo, True)
        subidos = list(zip(nombres_cv, argumentos.get('paths') or []))
        mensaje = dict(mensaje, params=dict(parametros, arguments=argumentos))
        if nombre == 'browser_tabs' and argumentos.get('action') == 'new': puerta.pestana_propia = True
        elif nombre == 'browser_navigate' and not puerta.pestana_propia:
            # Nunca navegar en la pestaña que el usuario tenía abierta: la primera vez se abre una propia.
            servicio.enviar({'jsonrpc': '2.0', 'id': 'pestana-propia', 'method': 'tools/call', 'params': {'name': 'browser_tabs', 'arguments': {'action': 'new'}}})
            puerta.pestana_propia = True
    respuesta = servicio.enviar(mensaje)
    if metodo == 'tools/list' and isinstance((respuesta or {}).get('result'), dict):
        respuesta['result']['tools'] = [herramienta for herramienta in respuesta['result'].get('tools') or [] if herramienta.get('name') in PERMITIDAS] + PROPIAS
    if metodo == 'tools/call':
        fallo = bool((respuesta.get('result') or {}).get('isError') or 'error' in respuesta)
        if not fallo: puerta.anotar(nombre, argumentos, subidos)
        puerta.observar(texto_de(respuesta))
        actividad.anotar(nombre, puerta.url, error=fallo)
        if puerta.firma and fallo: aprobaciones.devolver(puerta.firma)
        puerta.recien_firmada = bool(puerta.firma and not fallo)
        puerta.firma = None
    return respuesta

def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8', newline='\n')
    puerta, servicio = Puerta(), Servicio()
    for linea in sys.stdin:
        if not linea.strip(): continue
        try:
            mensaje = json.loads(linea)
            respuesta = atender(mensaje, puerta, servicio)
        except Exception as error:
            respuesta = {'jsonrpc': '2.0', 'id': mensaje.get('id'), 'error': {'code': -32603, 'message': str(error)}}
        if respuesta is not None: print(json.dumps(respuesta, ensure_ascii=False), flush=True)

if __name__ == '__main__': main()
