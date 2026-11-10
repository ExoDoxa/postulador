"""Panel local: lo que espera su envío, comprobantes, resultados, perfil, documentos y ajustes. Solo escucha en 127.0.0.1.

Lo usa la persona, no la IA: la puerta no deja que el navegador del asistente abra direcciones locales.
"""
import json
import mimetypes
import os
import re
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from . import RAIZ, actividad, aprobaciones, busqueda, carreras, comprobantes, cv, datos, documentos, estricto, navegador, nivel_maximo, perfil, registro

WEB = Path(__file__).parent / 'web'
PUERTO = 8770
DIRECCION = 'http://127.0.0.1:%d' % PUERTO
ESTATICOS = {'/': 'index.html', '/app.js': 'app.js', '/styles.css': 'styles.css'}
ARCHIVO_CV = re.compile(r'[\w.\-]+\.(pdf|png|docx)', re.A)
TIPOS_DOCUMENTO = {'.pdf': 'application/pdf', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.txt': 'text/plain; charset=utf-8'}

def ajustes():
    configuracion = navegador.configuracion()
    return {'navegador': configuracion.get('navegador'), 'disponibles': navegador.disponibles(), 'activo': navegador.activo(), 'niveles': registro.niveles_permitidos(),
            'nivel_por_defecto': registro.limitar(registro.NIVEL_POR_DEFECTO), 'nivel_maximo': nivel_maximo(), 'estricto': estricto(),
            'politicas': [registro.consultar_politica(sitio) for sitio in sorted(set(registro.politicas()) | set(registro.ADVERTENCIAS))],
            'busqueda': busqueda.leer(), 'antiguedades': busqueda.ANTIGUEDADES, 'modalidades': busqueda.MODALIDADES, 'idiomas': busqueda.IDIOMAS}

def abrir_carpeta(nombre):
    carpeta = cv.carpeta_cv() / cv.slug(nombre)
    if not carpeta.is_dir(): raise FileNotFoundError('No existe ese CV.')
    if os.name == 'nt': os.startfile(carpeta)
    else: subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(carpeta)])
    return {'abierta': str(carpeta)}

def perfil_carrera():
    """Paquete y valores sin tapar: el panel es de ella."""
    try: actual = perfil.leer()
    except FileNotFoundError: return {'perfil': False, 'carreras': carreras.disponibles()}
    paquete = carreras.de_perfil(actual)
    return {'perfil': True, 'carrera': actual.get('carrera') or None, 'carreras': carreras.disponibles(), 'paquete': paquete,
            'valores': actual.get('campos_carrera') or {}, 'formacion': [{'id': item.get('id'), 'titulo': item.get('title', '')} for item in actual.get('education', [])],
            'nombre': actual.get('name', '')}

def guardar_carrera(dato):
    actual = perfil.leer()
    if dato.get('carrera'): actual['carrera'] = carreras.cargar(dato['carrera'])['id']
    if not actual.get('carrera'): raise ValueError('Elige la carrera primero.')
    valores = dato.get('valores') or {}
    if not isinstance(valores, dict): raise ValueError('Valores inválidos.')
    actual['campos_carrera'] = {clave: ' '.join(str(valor).split())[:300] for clave, valor in valores.items() if str(valor).strip()}
    return perfil.guardar(actual, por='persona')

def documentos_panel():
    try: carrera = perfil.leer().get('carrera')
    except (OSError, ValueError): carrera = None
    try: formacion = [{'id': item.get('id'), 'titulo': item.get('title', '')} for item in perfil.leer().get('education', []) if item.get('id')]
    except (OSError, ValueError): formacion = []
    return {'documentos': documentos.listar_para_panel(), 'tipos': carreras.tipos_documento(carrera), 'formacion': formacion,
            'entrada': str(documentos.entrada()) if documentos.entrada() else None}

def crear_servidor(puerto=PUERTO):
    token = secrets.token_urlsafe(32)
    class Manejador(BaseHTTPRequestHandler):
        def log_message(self, *argumentos): pass

        def responder(self, estado, dato, tipo='application/json; charset=utf-8', descarga=None):
            cuerpo = dato if isinstance(dato, bytes) else json.dumps(dato, ensure_ascii=False).encode('utf-8')
            self.send_response(estado)
            self.send_header('Content-Type', tipo); self.send_header('Content-Length', str(len(cuerpo)))
            self.send_header('Cache-Control', 'no-store'); self.send_header('X-Content-Type-Options', 'nosniff')
            if descarga: self.send_header('Content-Disposition', 'attachment; filename="%s"' % descarga)
            self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors vscode-webview: vscode-file: https://*.vscode-cdn.net; form-action 'none'")
            self.end_headers(); self.wfile.write(cuerpo)

        def confiable(self, escritura=False):
            permitidos = {'127.0.0.1:%d' % self.server.server_port, 'localhost:%d' % self.server.server_port}
            if self.headers.get('Host') not in permitidos: return False
            origen = self.headers.get('Origin')
            if origen and origen not in {'http://' + host for host in permitidos}: return False
            return not escritura or secrets.compare_digest(self.headers.get('X-Panel-Token', ''), token)

        def do_GET(self):
            if not self.confiable(): return self.responder(403, {'error': 'Origen no permitido.'})
            ruta = urlsplit(self.path); partes = ruta.path.strip('/').split('/'); consulta = parse_qs(ruta.query)
            campo = lambda nombre: consulta.get(nombre, [''])[0]
            try:
                if ruta.path in ESTATICOS:
                    archivo = WEB / ESTATICOS[ruta.path]
                    return self.responder(200, archivo.read_bytes(), (mimetypes.guess_type(archivo.name)[0] or 'text/plain') + '; charset=utf-8')
                if ruta.path == '/api/sesion': return self.responder(200, {'token': token})
                if ruta.path == '/api/resumen': return self.responder(200, registro.analisis())
                if ruta.path == '/api/aprobaciones': return self.responder(200, [] if estricto() else aprobaciones.listar())
                if ruta.path == '/api/postulaciones': return self.responder(200, registro.listar(campo('estado'), campo('texto'), 200))
                if ruta.path == '/api/olvidadas': return self.responder(200, registro.olvidadas())
                if ruta.path == '/api/seguimientos': return self.responder(200, registro.seguimientos_pendientes(50))
                if ruta.path == '/api/vivo': return self.responder(200, {'actividad': actividad.recientes(), 'pestanas': navegador.pestanas()})
                if ruta.path == '/api/informes': return self.responder(200, actividad.informes())
                if len(partes) == 3 and partes[:2] == ['api', 'informes']: return self.responder(200, actividad.leer_informe(partes[2]))
                if len(partes) == 3 and partes[:2] == ['api', 'comprobantes']: return self.responder(200, comprobantes.para_panel(int(partes[2])))
                if len(partes) == 4 and partes[:2] == ['api', 'comprobantes'] and partes[3] == 'imagen':
                    return self.responder(200, comprobantes.ruta_imagen(int(partes[2])).read_bytes(), 'image/png')
                if ruta.path == '/api/documentos': return self.responder(200, documentos_panel())
                if len(partes) == 4 and partes[:2] == ['api', 'documentos'] and partes[3] == 'archivo':
                    archivo = documentos.ruta(int(partes[2]))
                    tipo = TIPOS_DOCUMENTO.get(archivo.suffix.lower())
                    return self.responder(200, archivo.read_bytes(), tipo or 'application/octet-stream', None if tipo else archivo.name)
                if ruta.path == '/api/perfil/carrera': return self.responder(200, perfil_carrera())
                if ruta.path == '/api/perfil/cambios': return self.responder(200, perfil.cambios())
                if ruta.path == '/api/cv': return self.responder(200, {'cv': cv.listar(), 'pendientes': len(cv.comentarios_pendientes())})
                if len(partes) == 3 and partes[:2] == ['api', 'cv']: return self.responder(200, cv.detalle(partes[2]))
                if ruta.path == '/api/ajustes': return self.responder(200, ajustes())
                if len(partes) == 3 and partes[0] == 'cv' and ARCHIVO_CV.fullmatch(partes[2]):
                    archivo = cv.carpeta_cv() / cv.slug(partes[1]) / partes[2]
                    return self.responder(200, archivo.read_bytes(), mimetypes.guess_type(archivo.name)[0] or 'application/octet-stream', partes[2] if campo('descargar') else None)
                return self.responder(404, {'error': 'No encontrado.'})
            except (ValueError, OSError): return self.responder(404, {'error': 'No encontrado.'})

        def do_POST(self):
            if not self.confiable(True): return self.responder(403, {'error': 'Sesión no válida.'})
            partes = urlsplit(self.path).path.strip('/').split('/')
            try:
                largo = int(self.headers.get('Content-Length', '0'))
                if partes == ['api', 'foto']:
                    if not 0 < largo <= cv.TAMANO_FOTO: raise ValueError('La foto supera 5 MB.')
                    return self.responder(200, cv.guardar_foto(self.rfile.read(largo)))
                if not 0 < largo <= 100000: raise ValueError('Cuerpo inválido.')
                dato = json.loads(self.rfile.read(largo))
                if not isinstance(dato, dict): raise ValueError('Cuerpo inválido.')
                if len(partes) == 3 and partes[:2] == ['api', 'aprobaciones']:
                    if estricto(): raise ValueError('En este equipo no hay aprobaciones: el envío lo haces tú.')
                    return self.responder(200, aprobaciones.resolver(int(partes[2]), dato.get('aprobar') is True))
                if len(partes) == 3 and partes[:2] == ['api', 'postulaciones']: return self.responder(200, registro.accion_persona(int(partes[2]), dato.get('accion', ''), str(dato.get('motivo', ''))[:300]))
                if len(partes) == 3 and partes[:2] == ['api', 'seguimientos']: return self.responder(200, registro.seguimiento_hecho(int(partes[2]), str(dato.get('nota', 'Marcado desde el panel'))[:300], actor='persona'))
                if len(partes) == 3 and partes[:2] == ['api', 'documentos']:
                    return self.responder(200, documentos.clasificar(int(partes[2]), dato.get('tipo', ''), dato.get('nombre', ''), dato.get('ia_puede_leer') is True, dato.get('vinculo', '')))
                if partes == ['api', 'perfil', 'carrera']: return self.responder(200, guardar_carrera(dato))
                if partes == ['api', 'perfil', 'revisado']: return self.responder(200, perfil.marcar_revisado())
                if len(partes) == 4 and partes[:2] == ['api', 'cv']:
                    if partes[3] == 'ajustes': return self.responder(200, cv.ajustar(partes[2], dato))
                    if partes[3] == 'comentarios': return self.responder(201, cv.comentar(partes[2], dato.get('texto', '')))
                    if partes[3] == 'abrir': return self.responder(200, abrir_carpeta(partes[2]))
                if partes == ['api', 'navegador']: return self.responder(200, navegador.elegir(dato.get('navegador', '')))
                if partes == ['api', 'busqueda']: return self.responder(200, busqueda.guardar(dato))
                if partes == ['api', 'politica']: return self.responder(200, registro.fijar_politica(dato.get('sitio', ''), dato.get('nivel', '')))
                return self.responder(404, {'error': 'Ruta no encontrada.'})
            except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error: return self.responder(400, {'error': str(error)})
    return ThreadingHTTPServer(('127.0.0.1', puerto), Manejador)

def _responde(puerto=PUERTO):
    try:
        with urllib.request.urlopen('http://127.0.0.1:%d/api/resumen' % puerto, timeout=1) as respuesta: return respuesta.status == 200
    except (OSError, ValueError): return False

def _ocupado(puerto=PUERTO):
    with socket.socket() as conexion:
        conexion.settimeout(.5)
        return conexion.connect_ex(('127.0.0.1', puerto)) == 0

def abrir_en_navegador(direccion=DIRECCION):
    if os.name == 'nt': os.startfile(direccion)
    else: webbrowser.open(direccion)

def asegurar(abrir=False):
    """Deja el panel corriendo aparte, para que sobreviva al chat que lo inició. Con abrir=True lo muestra en el navegador normal."""
    if not _ocupado():
        banderas = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        subprocess.Popen([sys.executable, '-m', 'postulador', 'panel'], cwd=RAIZ, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=banderas, start_new_session=sys.platform != 'win32')
    for _ in range(25):
        if _responde(): break
        time.sleep(.2)
    if abrir: abrir_en_navegador()
    return {'panel': DIRECCION, 'abierto_en_su_navegador': bool(abrir)}

def main(puerto=PUERTO, abrir=False):
    if _ocupado(puerto):
        # Ya hay un panel: el acceso directo solo lo muestra.
        if abrir: abrir_en_navegador('http://127.0.0.1:%d' % puerto)
        return
    servidor = crear_servidor(puerto)
    print('Panel en http://127.0.0.1:%d' % servidor.server_port, flush=True)
    if abrir: abrir_en_navegador('http://127.0.0.1:%d' % servidor.server_port)
    try: servidor.serve_forever()
    except KeyboardInterrupt: pass
    finally: servidor.server_close()
