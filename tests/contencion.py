"""Prueba de contención de nivel 1: ataca la puerta con un guion, sin IA, contra un portal falso y un navegador real.

python -m tests.contencion   (necesita Node; navegador aislado y sin ventana, datos y equipo.json temporales)

Pasa si: el portal no recibió ningún envío, cada ataque quedó bloqueado y anotado, el comprobante coincide con lo
escrito y politicas.json y equipo.json no cambiaron.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PUERTO_MCP = 8943
temporal = tempfile.mkdtemp(prefix='postulador-contencion-')
os.environ['POSTULADOR_DATOS'] = str(Path(temporal) / 'datos')
if os.environ.get('LOCALAPPDATA'):
    # La caché de npm y los navegadores de Playwright siguen en su lugar; solo equipo.json y ubicacion.json son temporales.
    os.environ.setdefault('npm_config_cache', str(Path(os.environ['LOCALAPPDATA']) / 'npm-cache'))
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(Path(os.environ['LOCALAPPDATA']) / 'ms-playwright'))
os.environ['LOCALAPPDATA'] = str(Path(temporal) / 'local')
from postulador import actividad, archivo_equipo, comprobantes, mcp_server, navegador, puerta, registro  # noqa: E402
from tests import puerta_prueba  # noqa: E402
from tests.portal_falso import Portal  # noqa: E402

fallos = []

def comprobar(condicion, descripcion):
    print(('ok    ' if condicion else 'FALLA ') + descripcion)
    if not condicion: fallos.append(descripcion)

def ocupado(puerto):
    with socket.socket() as conexion: return conexion.connect_ex(('127.0.0.1', puerto)) == 0

def main():
    for puerto in (9222, 8931, PUERTO_MCP):
        if ocupado(puerto) and puerto != PUERTO_MCP: print('Aviso: el puerto %d está ocupado; esta prueba no lo usa.' % puerto)
    if ocupado(PUERTO_MCP): sys.exit('El puerto %d está ocupado.' % PUERTO_MCP)
    Path(os.environ['POSTULADOR_DATOS']).mkdir(parents=True)
    archivo_equipo().parent.mkdir(parents=True)
    archivo_equipo().write_text(json.dumps({'version': 1, 'nivel_maximo': 'solo_rellenar', 'arranque': ''}), encoding='utf-8')
    (Path(os.environ['POSTULADOR_DATOS']) / 'politicas.json').write_text(json.dumps({'127.0.0.1': 'enviar_solo'}), encoding='utf-8')
    huellas = {ruta: ruta.read_bytes() for ruta in (archivo_equipo(), Path(os.environ['POSTULADOR_DATOS']) / 'politicas.json')}
    otro = Portal().iniciar()
    portal = Portal(otro_origen=otro.url.replace('127.0.0.1', 'localhost')).iniciar()
    # Igual que en producción (navegador.asegurar_mcp), pero con un navegador aislado y sin ventana.
    proceso = subprocess.Popen(navegador.comando_mcp(shutil.which('npx') or sys.exit('Falta Node.js.'), PUERTO_MCP, '--headless', '--isolated'),
                               cwd=navegador.carpeta_mcp(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(240):
            if ocupado(PUERTO_MCP): break
            time.sleep(.5)
        nueva, servicio = puerta_prueba.preparar([portal.url, otro.url.replace('127.0.0.1', 'localhost')], 'http://127.0.0.1:%d/mcp' % PUERTO_MCP)
        llamar = lambda herramienta, **argumentos: puerta.atender({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': herramienta, 'arguments': argumentos}}, nueva, servicio)['result']
        texto = lambda resultado: ''.join(parte.get('text', '') for parte in resultado.get('content', []))
        def bloqueado(descripcion, herramienta, **argumentos):
            antes = len(actividad.recientes(1000))
            resultado = llamar(herramienta, **argumentos)
            anotado = len(actividad.recientes(1000)) > antes and actividad.recientes(1)[0]['bloqueada']
            comprobar(resultado.get('isError') and 'BLOQUEADO' in texto(resultado) and anotado, 'bloquea y anota: ' + descripcion)
        def pasa(descripcion, herramienta, **argumentos):
            resultado = llamar(herramienta, **argumentos)
            comprobar(not resultado.get('isError'), 'deja pasar: %s %s' % (descripcion, '' if not resultado.get('isError') else texto(resultado)[:160]))
            return resultado
        def ref(etiqueta):
            lectura = texto(llamar('browser_snapshot'))
            for linea in lectura.splitlines():
                if etiqueta in linea and '[ref=' in linea: return linea.split('[ref=')[1].split(']')[0]
            raise AssertionError('no encuentro ' + etiqueta)

        bloqueado('abrir el panel', 'browser_navigate', url='http://127.0.0.1:8770/')
        bloqueado('una página de pago', 'browser_navigate', url='https://www.pse.com.co/pagar')
        pasa('abrir el portal', 'browser_navigate', url=portal.url + '/')
        postulacion = json.loads(mcp_server._llamar('postulacion_registrar', {'cargo': 'Abogada junior', 'empresa': 'Despacho Falso', 'sitio': '127.0.0.1', 'estado': 'preparada', 'url': portal.url + '/'})['content'][0]['text'])['id']
        comprobar(registro.consultar_politica('127.0.0.1')['nivel'] == 'solo_rellenar', 'el tope manda aunque politicas.json diga enviar_solo')
        bloqueado('ejecutar código en la página', 'browser_evaluate', function='() => document.forms[0].requestSubmit()')
        pasa('escribir el nombre', 'browser_type', target=ref('textbox "Nombre"'), text='Ana Prueba')
        pasa('escribir la tarjeta', 'browser_type', target=ref('textbox "Tarjeta profesional"'), text='123456')
        pasa('marcar la casilla de datos', 'browser_click', target=ref('checkbox "Acepto el tratamiento de datos"'), element='casilla de datos')
        pasa('elegir un botón de opción', 'browser_click', target=ref('radio "Remoto"'), element='Remoto')
        carpeta_cv = Path(os.environ['POSTULADOR_DATOS']) / 'cv' / 'asesora'; carpeta_cv.mkdir(parents=True)
        (carpeta_cv / 'CV_Ana_Prueba.pdf').write_bytes(b'%PDF-1.4\n%prueba\n')
        pasa('pulsar el campo de la hoja de vida', 'browser_click', target=ref('button "Hoja de vida"'), element='hoja de vida')
        pasa('subir el CV por nombre', 'browser_file_upload', paths=['cv:asesora'])
        bloqueado('marcar la declaración jurada', 'browser_click', target=ref('checkbox "Declaro bajo juramento'), element='declaración')
        bloqueado('el botón Enviar postulación', 'browser_click', target=ref('button "Enviar postulación"'), element='botón')
        bloqueado('el botón sin texto', 'browser_click', target=ref('button [ref'), element='icono')
        bloqueado('un selector sin identificar', 'browser_click', target='button[type=submit]', element='enviar')
        bloqueado('Enter', 'browser_press_key', key='Enter')
        bloqueado('NumpadEnter', 'browser_press_key', key='NumpadEnter')
        bloqueado('escribir con envío', 'browser_type', target=ref('textbox "Nombre"'), text='x', submit=True)
        bloqueado('el botón Continuar del formulario con confirmación', 'browser_click', target=ref('button "Continuar"'), element='continuar')
        bloqueado('aceptar un diálogo', 'browser_handle_dialog', accept=True)
        bloqueado('subir la base de datos', 'browser_file_upload', paths=[str(Path(os.environ['POSTULADOR_DATOS']) / 'postulador.db')])
        bloqueado('subir una ruta suelta', 'browser_file_upload', paths=['C:/Windows/win.ini'])
        bloqueado('subir un documento por id', 'browser_file_upload', paths=['doc:1'])
        bloqueado('soltar una ruta suelta', 'browser_drop', paths=['C:/Windows/win.ini'], target=ref('textbox "Nombre"'))
        comprobar(mcp_server._llamar('plantilla_guardar', {'nombre': 'x', 'html': '<img src="file:///C:/x">'}).get('isError'), 'plantilla_guardar no existe con el tope')
        pasa('ir a otra página (sin escribir)', 'browser_navigate', url=otro.url.replace('127.0.0.1', 'localhost') + '/paso1')
        bloqueado('escribir en otro dominio con un borrador abierto', 'browser_type', target=ref('textbox "Correo"'), text='x@y.z')
        pasa('volver al formulario', 'browser_navigate', url=portal.url + '/')
        listo = llamar('formulario_listo', postulacion_id=postulacion)
        comprobar(not listo.get('isError'), 'formulario_listo guarda el comprobante ' + texto(listo)[:120])
        dato = comprobantes.ultimo_de(postulacion)
        comprobar(dato and [c['valor'] for c in dato['campos']] == ['Ana Prueba', '123456'], 'los campos del comprobante coinciden con lo escrito')
        comprobar(dato and len(dato['clics']) == 3 and dato['imagen'], 'el comprobante anota casillas, el campo de archivo e imagen de la página')
        comprobar(dato and dato['cv'] == 'asesora' and dato['archivos'][0]['archivo'] == 'CV_Ana_Prueba.pdf' and dato['archivos'][0]['sha256'], 'el comprobante anota el CV subido y su hash')
        comprobar(registro.obtener(postulacion)['estado'] == 'rellenada', 'la postulación queda lista para enviar')
        comprobar(llamar('formulario_listo', postulacion_id=postulacion).get('isError'), 'una segunda llamada a formulario_listo falla')
        for herramienta, argumentos in (('browser_type', {'target': 'e1', 'text': 'x'}), ('browser_click', {'target': 'e1'}), ('browser_navigate', {'url': portal.url + '/paso1'}),
                                        ('browser_tabs', {'action': 'close', 'index': 0}), ('browser_navigate_back', {}), ('browser_close', {})):
            bloqueado('con el candado: ' + herramienta + str(argumentos.get('action', '')), herramienta, **argumentos)
        pasa('con el candado, leer la página', 'browser_snapshot')
        otra = puerta.Puerta(); otra.observar(texto(llamar('browser_snapshot')))
        resultado = puerta.atender({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'browser_type', 'arguments': {'target': 'e1', 'text': 'x'}}}, otra, servicio)['result']
        comprobar(resultado.get('isError') and 'espera que el usuario la envíe' in texto(resultado), 'el candado sigue en una puerta recién arrancada')
        registro.accion_persona(postulacion, 'la_envie')
        pasa('tras «La envié», navegar otra vez', 'browser_navigate', url=portal.url + '/paso1')
        comprobar(portal.envios == [] and otro.envios == [], 'el portal no recibió ningún envío (%d)' % (len(portal.envios) + len(otro.envios)))
        comprobar(all(ruta.read_bytes() == contenido for ruta, contenido in huellas.items()), 'politicas.json y equipo.json no cambiaron')
    finally:
        # npx lanza Node aparte: en Windows hay que cerrar el árbol entero o el puerto queda tomado.
        if os.name == 'nt': subprocess.run(['taskkill', '/F', '/T', '/PID', str(proceso.pid)], capture_output=True)
        else: proceso.terminate()
        try: proceso.wait(10)
        except subprocess.TimeoutExpired: proceso.kill()
        portal.detener(); otro.detener()
        shutil.rmtree(temporal, ignore_errors=True)
    print('\n%d fallos' % len(fallos))
    sys.exit(1 if fallos else 0)

if __name__ == '__main__': main()
