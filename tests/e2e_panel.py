"""QA del panel en Chromium aislado con datos temporales, en el modo del equipo de la persona (tope solo_rellenar).

Opcional: python -m tests.e2e_panel (requiere `pip install playwright` y `playwright install chromium`).
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

carpeta = tempfile.mkdtemp(prefix='postulador-e2e-')
os.environ['POSTULADOR_DATOS'] = carpeta
if os.environ.get('LOCALAPPDATA'): os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(Path(os.environ['LOCALAPPDATA']) / 'ms-playwright'))
os.environ['LOCALAPPDATA'] = str(Path(carpeta) / 'local')  # equipo.json temporal: nunca el del equipo real
from playwright.sync_api import sync_playwright
from postulador import RAIZ, actividad, archivo_equipo, cv, documentos, panel, perfil, registro

PUERTO = 8775
URL = 'http://127.0.0.1:%d/' % PUERTO
VISTAS = ('mesa', 'postulaciones', 'perfil', 'documentos', 'cv', 'seguimientos', 'resumen', 'vivo', 'informes', 'ajustes')
MOVIL = {'width': 390, 'height': 844}
ESCRITORIO = {'width': 1200, 'height': 900}
OBJETIVO_MINIMO = 44
PNG = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082')
fallos = []

def comprobar(condicion, descripcion):
    print(('ok    ' if condicion else 'FALLA ') + descripcion)
    if not condicion: fallos.append(descripcion)

def sembrar():
    arranque = Path(carpeta) / 'arranque'; (arranque / 'entrada').mkdir(parents=True)
    archivo_equipo().parent.mkdir(parents=True, exist_ok=True)
    archivo_equipo().write_text(json.dumps({'version': 1, 'nivel_maximo': 'solo_rellenar', 'arranque': str(arranque)}), encoding='utf-8')
    ejemplo = json.loads((RAIZ / 'ejemplos' / 'perfil.json').read_text(encoding='utf-8'))
    ejemplo.update(carrera='derecho', campos_carrera={'tarjeta_profesional': '123456', 'areas_practica': 'Laboral', 'ciudad': 'Bogotá'})
    perfil.guardar(ejemplo); perfil.marcar_revisado()
    cv.generar('asesora', {'summary': ejemplo['cv_summaries']['general'], 'experiences': ['tienda'], 'projects': ['feria'], 'skills': ejemplo['skills'][:3]}, motor='html')
    cambiado = perfil.leer(); cambiado['headline'] = 'Abogada laboralista'; perfil.guardar(cambiado)
    enviada = registro.registrar('Abogada con un nombre de cargo extremadamente largo para probar el ajuste de línea', 'Firma con nombre larguísimo S.A.S.', 'computrabajo', 'enviada', url='https://ejemplo.com/1')
    with registro.closing(registro.conexion()) as base, base: base.execute("update postulaciones set seguir_el='2020-01-01' where id=?", (enviada['id'],))
    rechazada = registro.registrar('Asesora', 'Acme', 'elempleo', 'enviada', url='javascript:alert(1)')
    registro.accion_persona(rechazada['id'], 'rechazada', 'Pide inglés C1')
    lista = registro.registrar('Abogada <b>junior</b>', 'Despacho', 'portal.example', 'preparada', url='https://portal.example/f')
    # Comprobante de hace dos días, escrito a mano porque los disparadores no dejan cambiar la hora de uno ya creado.
    (Path(carpeta) / 'comprobantes').mkdir(); (Path(carpeta) / 'comprobantes' / 'c1.png').write_bytes(PNG)
    with registro.closing(registro.conexion()) as base, base:
        base.execute('insert into comprobantes (id,postulacion_id,url,inicio,fin,campos,clics,archivos,cv,imagen,imagen_sha256,envios_bloqueados,creado) values (1,?,?,?,?,?,?,?,?,?,?,?,?)',
                     (lista['id'], 'https://portal.example/f', '2020-01-01 10:00:00', '2020-01-01 10:05:00', json.dumps([{'campo': 'textbox Nombre', 'valor': 'Ana', 'hora': '10:00:01'}]),
                      json.dumps([{'elemento': 'checkbox Acepto el tratamiento de datos', 'hora': '10:00:02'}]), json.dumps([{'archivo': 'CV_Ana.pdf', 'cv': 'asesora', 'sha256': 'x', 'hora': '10:00:03'}]),
                      'asesora', 'comprobantes/c1.png', 'x', 1, '2020-01-01 10:05:00'))
        registro.cambiar(base, lista['id'], 'rellenada', 'puerta')
    documento = arranque / 'entrada' / 'Diploma.pdf'; documento.write_bytes(b'%PDF-1.4 diploma'); os.utime(documento, (1_700_000_000, 1_700_000_000))
    actividad.anotar('browser_click', 'https://ejemplo.com/form', bloqueada=True); actividad.guardar_informe('Revisión', 'Contenido del informe')
    return lista['id']

def desbordamiento(pagina):
    return pagina.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')

def objetivos_pequenos(pagina):
    return pagina.evaluate('''(minimo) => [...document.querySelectorAll('button, select, input:not([type=checkbox]), textarea, nav a')]
      .filter((n) => n.offsetParent && n.getBoundingClientRect().height < minimo).map((n) => n.tagName + ':' + (n.textContent || n.placeholder || '').trim().slice(0, 20))''', OBJETIVO_MINIMO)

def main():
    id_lista = sembrar()
    servidor = panel.crear_servidor(PUERTO)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    with sync_playwright() as motor:
        navegador = motor.chromium.launch()
        for tema, tamano, nombre in (('dark', ESCRITORIO, 'escritorio oscuro'), ('light', MOVIL, 'móvil claro')):
            contexto = navegador.new_context(viewport=tamano, color_scheme=tema)
            pagina = contexto.new_page(); errores = []
            pagina.on('console', lambda mensaje: errores.append(mensaje.text) if mensaje.type == 'error' and '404' not in mensaje.text else None)
            pagina.on('pageerror', lambda error: errores.append(str(error)))
            for vista in VISTAS:
                pagina.goto(URL + '#' + vista); pagina.wait_for_timeout(400)
                comprobar(desbordamiento(pagina) <= 0, '%s · %s sin desborde horizontal (%s px)' % (nombre, vista, desbordamiento(pagina)))
                pequenos = objetivos_pequenos(pagina)
                comprobar(not pequenos, '%s · %s objetivos ≥ %d px %s' % (nombre, vista, OBJETIVO_MINIMO, pequenos[:4]))
                comprobar('firmar' not in pagina.locator('body').inner_text().lower(), '%s · %s no dice «firmar»' % (nombre, vista))
            comprobar(not errores, '%s · consola limpia %s' % (nombre, errores[:2]))
            contexto.close()

        pagina = navegador.new_context(viewport=ESCRITORIO, color_scheme='light').new_page()
        pagina.goto(URL + '#mesa'); pagina.wait_for_selector('.expediente')
        comprobar(pagina.locator('h3', has_text='Abogada <b>junior</b>').count() == 1, 'el HTML de un cargo se muestra como texto')
        comprobar(pagina.locator('#cuenta-lista').inner_text() == '1', 'el contador de Lista para enviar cuenta la que espera')
        comprobar(pagina.locator('#olvidadas .olvidada').count() == 1, 'el aviso de olvidadas aparece arriba')
        comprobar('el asistente no puede seguir' in pagina.locator('#olvidadas').inner_text(), 'el aviso explica que el asistente espera')
        comprobar(pagina.locator('.expediente .acciones button').count() == 4, 'la postulación lista muestra los cuatro botones')

        boton = pagina.locator('.expediente .sellar').first; boton.focus()
        pagina.wait_for_timeout(6000)
        comprobar(pagina.evaluate("document.activeElement.classList.contains('sellar')"), 'el foco sobrevive al refresco de la lista')

        pagina.get_by_role('button', name='Lo que rellenó el asistente').click(); pagina.wait_for_selector('.imagen-pagina')
        texto = pagina.locator('main').inner_text()
        comprobar('textbox Nombre' in texto and 'Ana' in texto, 'el comprobante muestra los campos')
        comprobar('Acepto el tratamiento de datos' in texto, 'el comprobante muestra las casillas')
        comprobar('lo enviado puede ser distinto' in texto, 'el comprobante advierte que ella pudo cambiar algo')
        comprobar(pagina.locator('.imagen-pagina').evaluate('(n) => n.naturalWidth > 0'), 'se ve la imagen de la página')

        pagina.goto(URL + '#mesa'); pagina.wait_for_selector('.expediente .sellar')
        pagina.locator('.expediente .sellar').first.click(); pagina.wait_for_timeout(900)
        comprobar(registro.obtener(id_lista)['estado'] == 'enviada', '«La envié» la pasa a enviada')
        comprobar(pagina.locator('.expediente').count() == 0 and pagina.locator('#olvidadas .olvidada').count() == 0, 'sale de la lista y del aviso')

        pagina.goto(URL + '#perfil'); pagina.wait_for_selector('.aviso-perfil')
        comprobar('cambió tu perfil' in pagina.locator('.aviso-perfil').inner_text(), 'el perfil avisa de cambios sin revisar')
        comprobar('Abogada laboralista' in pagina.locator('.aviso-perfil').inner_text(), 'muestra el cambio antes y después')
        comprobar(pagina.get_by_label('Tarjeta profesional').input_value() == '123456', 'muestra los datos de abogada')
        pagina.get_by_role('button', name='Revisado').click(); pagina.wait_for_timeout(700)
        comprobar(perfil.sello_vigente(), '«Revisado» sella el perfil')
        pagina.get_by_label('Cédula de ciudadanía').fill('52.123.456'); pagina.get_by_role('button', name='Guardar datos').click(); pagina.wait_for_timeout(700)
        comprobar(perfil.leer()['campos_carrera'].get('cedula') == '52.123.456' and perfil.sello_vigente(), 'ella escribe un dato sensible sin perder el sello')
        comprobar(perfil.leer(para_ia=True)['campos_carrera']['cedula'] == perfil.TAPADO, 'la IA ve la cédula tapada')

        pagina.goto(URL + '#documentos'); pagina.wait_for_selector('.documento')
        comprobar(pagina.locator('#cuenta-docs').inner_text() == '1', 'el contador de Documentos cuenta los nuevos')
        pagina.get_by_label('Tipo').select_option('diploma_pregrado'); pagina.get_by_label('Nombre visible').fill('Diploma de abogada')
        pagina.get_by_role('button', name='Guardar').click(); pagina.wait_for_timeout(700)
        comprobar(documentos.listar_para_ia()[0]['nombre'] == 'Diploma de abogada', 'clasificar lo deja visible para la IA, sin ruta')

        pagina.goto(URL + '#cv'); pagina.wait_for_selector('.hoja-cv'); pagina.locator('.hoja-cv').first.click(); pagina.wait_for_selector('.editor')
        pagina.get_by_label('Comentario para el asistente').fill('Resalta mi experiencia')
        pagina.get_by_role('button', name='Guardar comentario').click(); pagina.wait_for_selector('.comentarios li')
        comprobar(cv.comentarios_pendientes()[0]['texto'] == 'Resalta mi experiencia', 'el comentario llega al asistente')
        comprobar(pagina.get_by_role('button', name='Pedir al agente').count() == 0, 'no hay botón que lance una IA oculta')
        with pagina.expect_download() as descarga:
            pagina.get_by_role('link', name='PDF').click()
        comprobar(descarga.value.suggested_filename.endswith('.pdf'), 'exportar descarga el PDF')

        pagina.goto(URL + '#postulaciones'); pagina.wait_for_selector('table')
        comprobar(pagina.locator('th[scope=col]').count() > 0, 'las tablas declaran sus encabezados')
        comprobar(pagina.locator('a[href^="javascript"]').count() == 0, 'un enlace javascript: no se vuelve clicable')
        pagina.goto(URL + '#seguimientos'); pagina.wait_for_selector('table')
        pagina.get_by_role('button', name='Hecho').first.click(); pagina.wait_for_timeout(600)
        comprobar(pagina.locator('.vacio').count() == 1, 'marcar un seguimiento actualiza la lista')
        pagina.goto(URL + '#vivo'); pagina.wait_for_selector('.bloqueo')
        comprobar(pagina.locator('.bloqueo').inner_text() == 'Bloqueada por la puerta', 'En vivo muestra un bloqueo')
        pagina.goto(URL + '#ajustes'); pagina.wait_for_selector('input')
        comprobar('Tope de este equipo: solo_rellenar' in pagina.locator('main').inner_text(), 'Ajustes muestra el tope')
        comprobar(pagina.get_by_label('Nivel').locator('option').all_inner_texts() == ['solo_rellenar', 'solo_preparar'], 'Ajustes no ofrece niveles por encima del tope')
        comprobar(pagina.get_by_role('button', name='Conectar claude').count() == 0, 'no hay botón Conectar')

        pagina.goto(URL + '#resumen'); pagina.wait_for_selector('.cifras')
        pagina.locator('nav a[href="#mesa"]').focus(); pagina.keyboard.press('Enter'); pagina.wait_for_timeout(500)
        comprobar(pagina.evaluate("document.activeElement.id === 'vista'"), 'al cambiar de sección el foco va al contenido')
        servidor.shutdown(); servidor.server_close()
        inicio = time.time()
        try: pagina.wait_for_selector('#desconectado:visible', timeout=15000)
        except Exception: pass
        print('aviso de desconexión tras %.1f s' % (time.time() - inicio))
        comprobar(pagina.locator('#desconectado').is_visible(), 'si el panel se apaga, lo avisa')
        comprobar('python' not in pagina.locator('#desconectado').inner_text(), 'el aviso no le pide comandos')
        navegador.close()
    shutil.rmtree(carpeta, ignore_errors=True)
    print('\n%d fallos' % len(fallos))
    sys.exit(1 if fallos else 0)

if __name__ == '__main__': main()
