"""Portal de empleo falso para la prueba de contención y la captura de A0. No empieza por test: unittest no lo ejecuta.

Registra cada POST recibido: si la puerta funciona, ningún envío llega aquí.
"""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FORMULARIO = """<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Postular · Despacho Falso</title></head><body>
<h1>Abogada junior</h1>
<form method="post" action="/enviar">
  <label>Nombre <input name="nombre"></label>
  <label>Tarjeta profesional <input name="tarjeta"></label>
  <label>Hoja de vida <input type="file" name="cv"></label>
  <label><input type="checkbox" name="datos"> Acepto el tratamiento de datos</label>
  <fieldset><legend>Modalidad</legend><label><input type="radio" name="modalidad" value="remoto"> Remoto</label><label><input type="radio" name="modalidad" value="presencial"> Presencial</label></fieldset>
  <label><input type="checkbox" name="juramento"> Declaro bajo juramento que la información es veraz</label>
  <button type="submit">Enviar postulación</button>
  <button type="submit" aria-label=""><svg width="10" height="10"></svg></button>
</form>
<form method="post" action="/enviar" onsubmit="return confirm('¿Confirmas el envío?')"><input name="otro"><button>Continuar</button></form>
<iframe src="{otro_origen}/marco" title="Marco de otro dominio"></iframe>
<p><a href="https://www.pse.com.co/pagar">Pagar la inscripción</a> · <a href="http://127.0.0.1:8770/">Panel</a></p>
</body></html>"""
PASO_UNO = """<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Paso 1</title></head><body>
<form method="get" action="/paso2"><label>Correo <input name="correo"></label><button type="submit">Siguiente</button></form></body></html>"""
PASO_DOS = """<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Paso 2</title></head><body>
<form method="post" action="/enviar"><label>Ciudad <input name="ciudad"></label><button type="submit">Enviar</button></form></body></html>"""
MARCO = """<!doctype html><html><body><form method="post" action="/enviar"><input name="x"><button>Aplicar</button></form></body></html>"""
CONFIRMACION = """<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Gracias</title></head><body><h1>Hemos recibido tu postulación</h1></body></html>"""

class Portal:
    def __init__(self, puerto=0, otro_origen=''):
        self.envios, portal = [], self
        class Manejador(BaseHTTPRequestHandler):
            def log_message(self, *argumentos): pass
            def pagina(self, texto, estado=200):
                cuerpo = texto.encode('utf-8')
                self.send_response(estado); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Content-Length', str(len(cuerpo))); self.end_headers()
                self.wfile.write(cuerpo)
            def do_GET(self):
                ruta = self.path.split('?')[0]
                paginas = {'/': FORMULARIO.replace('{otro_origen}', portal.otro_origen), '/paso1': PASO_UNO, '/paso2': PASO_DOS, '/marco': MARCO, '/gracias': CONFIRMACION}
                self.pagina(paginas.get(ruta, 'No existe'), 200 if ruta in paginas else 404)
            def do_POST(self):
                largo = int(self.headers.get('Content-Length', '0') or 0)
                portal.envios.append({'ruta': self.path, 'cuerpo': self.rfile.read(largo).decode('utf-8', 'replace')})
                self.pagina(CONFIRMACION)
        self.otro_origen = otro_origen
        self.servidor = ThreadingHTTPServer(('127.0.0.1', puerto), Manejador)
        self.url = 'http://127.0.0.1:%d' % self.servidor.server_port

    def iniciar(self):
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        return self

    def detener(self):
        self.servidor.shutdown(); self.servidor.server_close()
