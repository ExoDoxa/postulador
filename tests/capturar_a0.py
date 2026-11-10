"""Bloque A0: guarda las respuestas reales de Playwright MCP que la puerta lee, y comprueba Host y Origin.

python -m tests.capturar_a0   (necesita Node; usa un navegador aislado y sin ventana, en un puerto propio)
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from postulador import navegador, puerta
from tests.portal_falso import Portal

PUERTO = 8941
DESTINO = Path(__file__).parent / 'fixtures' / 'playwright_0_0_84'

def libre(puerto):
    with socket.socket() as conexion: return conexion.connect_ex(('127.0.0.1', puerto)) != 0

def peticion(cabeceras):
    """Status de un initialize con cabeceras extra: 200 si el servidor lo acepta."""
    cuerpo = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'a0', 'version': '1'}}}).encode()
    base = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    try:
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:%d/mcp' % PUERTO, cuerpo, dict(base, **cabeceras)), timeout=20) as respuesta: return respuesta.status
    except urllib.error.HTTPError as error: return error.code

def main():
    if not libre(PUERTO): sys.exit('El puerto %d está ocupado.' % PUERTO)
    npx = shutil.which('npx') or sys.exit('Falta Node.js.')
    DESTINO.mkdir(parents=True, exist_ok=True)
    portal = Portal().iniciar()
    proceso = subprocess.Popen([npx, '-y', navegador.PLAYWRIGHT_MCP, '--headless', '--isolated', '--host', '127.0.0.1', '--port', str(PUERTO)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(240):
            if not libre(PUERTO): break
            time.sleep(.5)
        servicio = puerta.Servicio('http://127.0.0.1:%d/mcp' % PUERTO)
        servicio.iniciar()
        def llamar(nombre, argumentos, archivo=None):
            respuesta = servicio.enviar({'jsonrpc': '2.0', 'id': nombre, 'method': 'tools/call', 'params': {'name': nombre, 'arguments': argumentos}})
            if archivo: (DESTINO / archivo).write_text(json.dumps(respuesta, ensure_ascii=False, indent=2), encoding='utf-8')
            return respuesta
        herramientas = servicio.enviar({'jsonrpc': '2.0', 'id': 'lista', 'method': 'tools/list'})
        (DESTINO / 'tools_list.json').write_text(json.dumps(herramientas, ensure_ascii=False, indent=2), encoding='utf-8')
        llamar('browser_navigate', {'url': portal.url + '/'}, 'navigate.json')
        llamar('browser_snapshot', {}, 'snapshot_formulario.json')
        llamar('browser_tabs', {'action': 'new'})
        llamar('browser_tabs', {'action': 'list'}, 'tabs_list_dos.json')
        llamar('browser_tabs', {'action': 'new'})
        llamar('browser_tabs', {'action': 'list'}, 'tabs_list_tres.json')
        llamar('browser_tabs', {'action': 'select', 'index': 0})
        captura = llamar('browser_take_screenshot', {'type': 'png', 'fullPage': True}, None)
        imagen = puerta.imagen_de(captura)
        resumen = json.loads(json.dumps(captura))
        for parte in (resumen.get('result') or {}).get('content') or []:
            if parte.get('type') == 'image': parte['data'] = '<%d caracteres en base64>' % len(parte['data'])
        (DESTINO / 'take_screenshot.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding='utf-8')
        host_ajeno, origen_ajeno, origen_propio = peticion({'Host': 'evil.example:%d' % PUERTO}), peticion({'Origin': 'http://evil.example'}), peticion({})
        esquema_captura = next((h['inputSchema'] for h in herramientas['result']['tools'] if h['name'] == 'browser_take_screenshot'), {})
        lineas = ['# Respuestas reales de %s' % navegador.PLAYWRIGHT_MCP, '',
                  'Capturadas con `python -m tests.capturar_a0` (navegador aislado y sin ventana, contra `tests/portal_falso.py`).', '',
                  '| Comprobación | Resultado |', '|---|---|',
                  '| La imagen de `browser_take_screenshot` llega como contenido `image` en base64 | %s |' % ('sí, %d bytes de PNG' % len(imagen) if imagen else 'no: revisar `puerta.imagen_de`'),
                  '| `browser_take_screenshot` acepta `fullPage` | %s |' % ('sí' if 'fullPage' in json.dumps(esquema_captura) else 'no'),
                  '| Petición con un `Host` ajeno | %s |' % ('rechazada (%d)' % host_ajeno if host_ajeno >= 400 else 'ACEPTADA (%d): anotar en la tabla de riesgos' % host_ajeno),
                  '| Petición con un `Origin` ajeno | %s |' % ('rechazada (%d)' % origen_ajeno if origen_ajeno >= 400 else 'ACEPTADA (%d): anotar en la tabla de riesgos' % origen_ajeno),
                  '| Petición sin cabeceras extra | %d |' % origen_propio,
                  '| El navegador dedicado se lanza sin `--remote-allow-origins=*` | %s |' % ('sí' if '--remote-allow-origins' not in Path(navegador.__file__).read_text(encoding='utf-8') else 'NO'), '']
        (DESTINO / 'LEEME.md').write_text('\n'.join(lineas), encoding='utf-8')
        print('\n'.join(lineas))
    finally:
        # npx lanza Node aparte: en Windows hay que cerrar el árbol entero o el puerto queda tomado.
        if os.name == 'nt': subprocess.run(['taskkill', '/F', '/T', '/PID', str(proceso.pid)], capture_output=True)
        else: proceso.terminate()
        try: proceso.wait(10)
        except subprocess.TimeoutExpired: proceso.kill()
        portal.detener()

if __name__ == '__main__': main()
