"""Abre el navegador Chromium elegido por el usuario, con perfil exclusivo y control local por CDP."""
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from . import datos

PUERTO = 9222
PUERTO_MCP = 8931
URL_MCP = 'http://127.0.0.1:%d/mcp' % PUERTO_MCP
PLAYWRIGHT_MCP = '@playwright/mcp@0.0.84'
UBICACIONES = {
    'brave': (r'%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe', r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe',
              '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser', 'brave-browser', 'brave'),
    'chrome': (r'%ProgramFiles%\Google\Chrome\Application\chrome.exe', r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe', r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe',
               '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'google-chrome'),
    'edge': (r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe', r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe',
             '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', 'microsoft-edge'),
    'chromium': ('/Applications/Chromium.app/Contents/MacOS/Chromium', 'chromium', 'chromium-browser'),
}

def _localizar(nombre):
    for candidato in UBICACIONES[nombre]:
        ruta = Path(os.path.expandvars(candidato))
        if ruta.is_absolute() and ruta.is_file(): return str(ruta)
        if not ruta.is_absolute() and shutil.which(candidato): return shutil.which(candidato)
    return None

def disponibles():
    encontrados = {nombre: _localizar(nombre) for nombre in UBICACIONES}
    return {nombre: ruta for nombre, ruta in encontrados.items() if ruta}

def configuracion():
    archivo = datos() / 'config.json'
    return json.loads(archivo.read_text(encoding='utf-8')) if archivo.is_file() else {}

def guardar_configuracion(**cambios):
    datos().mkdir(parents=True, exist_ok=True)
    (datos() / 'config.json').write_text(json.dumps(dict(configuracion(), **cambios), ensure_ascii=False, indent=2), encoding='utf-8')

def elegir(navegador):
    """Acepta un nombre conocido o la ruta a cualquier ejecutable basado en Chromium."""
    if navegador in UBICACIONES:
        if not _localizar(navegador): raise FileNotFoundError('%s no está instalado. Disponibles: %s' % (navegador, ', '.join(disponibles()) or 'ninguno'))
    elif not Path(navegador).is_file():
        raise FileNotFoundError('Usa %s o la ruta a un ejecutable.' % ', '.join(UBICACIONES))
    guardar_configuracion(navegador=navegador)
    return {'navegador': navegador, 'nota': 'Se usará la próxima vez que se abra; cierra el actual para cambiarlo.'}

def ejecutable():
    elegido = configuracion().get('navegador')
    if elegido: return _localizar(elegido) if elegido in UBICACIONES else elegido
    return next(iter(disponibles().values()), None)

def impresor():
    """Brave se cuelga con --print-to-pdf en modo headless, así que solo se usa si no hay otro."""
    opciones = disponibles()
    return next((ruta for nombre, ruta in opciones.items() if nombre != 'brave'), None) or ejecutable()

def perfil_navegador():
    base = os.environ.get('LOCALAPPDATA') or Path.home()
    return configuracion().get('perfil_navegador') or str(Path(base) / 'PostuladorNavegador')

def activo():
    try:
        with urllib.request.urlopen('http://127.0.0.1:%d/json/version' % PUERTO, timeout=2) as respuesta:
            return json.load(respuesta).get('Browser')
    except OSError:
        return None

def pestanas():
    """Páginas abiertas en el navegador dedicado, para mostrarlas en el panel."""
    try:
        with urllib.request.urlopen('http://127.0.0.1:%d/json/list' % PUERTO, timeout=2) as respuesta:
            return [{'titulo': item.get('title', ''), 'url': item.get('url', '')} for item in json.load(respuesta) if item.get('type') == 'page']
    except OSError:
        return []

def abrir():
    version = activo()
    if version: return {'navegador': version, 'abierto_ahora': False}
    programa = ejecutable()
    if not programa: raise FileNotFoundError('Instala Brave, Chrome o Edge, o elige uno con: python -m postulador navegador RUTA')
    subprocess.Popen([programa, '--remote-debugging-port=%d' % PUERTO, '--user-data-dir=' + perfil_navegador(),
                      '--no-first-run', '--no-default-browser-check', 'about:blank'],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        time.sleep(.25)
        version = activo()
        if version: return {'navegador': version, 'abierto_ahora': True}
    raise TimeoutError('El navegador no abrió el puerto %d. Ciérralo y reintenta.' % PUERTO)

def mcp_activo():
    with socket.socket() as conexion:
        conexion.settimeout(.5)
        return conexion.connect_ex(('127.0.0.1', PUERTO_MCP)) == 0

def carpeta_mcp():
    """Carpeta de trabajo de Playwright MCP. Solo deja subir archivos de ahí adentro (A0, 0.0.84): la de los CV."""
    carpeta = datos() / 'cv'
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta

def comando_mcp(npx, puerto=PUERTO_MCP, *extra):
    return [npx, '-y', PLAYWRIGHT_MCP, '--host', '127.0.0.1', '--port', str(puerto), '--output-dir', str(datos() / 'playwright'), *extra]

def asegurar_mcp():
    """Deja el navegador y Playwright MCP corriendo como servicio: un motor no espera a un MCP lento al arrancar."""
    resultado = abrir()
    if mcp_activo(): return dict(resultado, mcp=URL_MCP)
    npx = shutil.which('npx')
    if not npx: raise FileNotFoundError('Falta Node.js: instálalo para controlar el navegador.')
    datos().mkdir(parents=True, exist_ok=True)
    banderas = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    with (datos() / 'playwright.log').open('ab') as registro:
        subprocess.Popen(comando_mcp(npx, PUERTO_MCP, '--cdp-endpoint', 'http://127.0.0.1:%d' % PUERTO), cwd=carpeta_mcp(),
                         stdin=subprocess.DEVNULL, stdout=registro, stderr=registro, creationflags=banderas, start_new_session=os.name != 'nt')
    for _ in range(120):
        time.sleep(.5)
        if mcp_activo(): return dict(resultado, mcp=URL_MCP)
    raise TimeoutError('Playwright MCP no arrancó; revisa datos_usuario/playwright.log.')
