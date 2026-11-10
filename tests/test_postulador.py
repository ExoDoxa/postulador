import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import http.client
from postulador import RAIZ, DatosNoDisponibles, actividad, aprobaciones, archivo_equipo, arranque, ats, busqueda, carreras, comprobantes, cv, documentos, mcp_server, navegador, panel, perfil, portales, puerta, registro, ubicacion

EJEMPLO = json.loads((RAIZ / 'ejemplos' / 'perfil.json').read_text(encoding='utf-8'))
SELECCION = {'summary': EJEMPLO['cv_summaries']['general'], 'experiences': ['tienda'], 'projects': ['feria'], 'skills': ['Redacción']}

ACCESO_REAL = arranque.acceso_directo

def sin_accesos(*argumentos, **opciones):
    raise OSError('Las pruebas no crean accesos directos en el Escritorio real.')

def poner_variable(prueba, nombre, valor):
    previo = os.environ.get(nombre)
    os.environ[nombre] = valor
    prueba.addCleanup(lambda: os.environ.__setitem__(nombre, previo) if previo is not None else os.environ.pop(nombre, None))

class Base(unittest.TestCase):
    """Cada prueba tiene sus datos y su equipo.json temporales. Por defecto, un equipo de autor (tope enviar_solo)."""
    TOPE = 'enviar_solo'

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)
        poner_variable(self, 'POSTULADOR_DATOS', self.carpeta.name)
        poner_variable(self, 'LOCALAPPDATA', str(Path(self.carpeta.name) / 'local'))
        arranque.acceso_directo = sin_accesos
        self.addCleanup(setattr, arranque, 'acceso_directo', ACCESO_REAL)
        self.tope(self.TOPE)

    def tope(self, nivel, arranque_en=None):
        archivo_equipo().parent.mkdir(parents=True, exist_ok=True)
        archivo_equipo().write_text(json.dumps({'version': 1, 'nivel_maximo': nivel, 'arranque': str(arranque_en or '')}), encoding='utf-8')

class PerfilTests(Base):
    def test_guarda_y_respalda(self):
        perfil.guardar(EJEMPLO); perfil.guardar(EJEMPLO)
        self.assertEqual(perfil.leer()['name'], EJEMPLO['name'])
        self.assertEqual(len(list((Path(self.carpeta.name) / 'respaldos').iterdir())), 1)

    def test_rechaza_ids_repetidos(self):
        malo = json.loads(json.dumps(EJEMPLO))
        malo['experience'].append(dict(malo['experience'][0]))
        with self.assertRaises(ValueError): perfil.guardar(malo)

    def test_rechaza_idioma_con_ruta(self):
        with self.assertRaises(ValueError): perfil.ruta('../x')

class RegistroTests(Base):
    def test_detecta_duplicado(self):
        self.assertFalse(registro.registrar('QA', 'Acme', 'torre', 'enviada')['duplicado'])
        self.assertTrue(registro.registrar('qa', 'ACME', 'linkedin', 'preparada')['duplicado'])
        self.assertEqual(len(registro.listar(texto='Acme')), 1)

    def test_actualiza_y_conserva_nota(self):
        creada = registro.registrar('QA', 'Acme', 'torre', 'enviada', nota='primera')
        registro.actualizar(creada['id'], 'rechazada')
        self.assertEqual(registro.listar()[0]['nota'], 'primera')
        with self.assertRaises(ValueError): registro.actualizar(999, 'enviada')
        with self.assertRaises(ValueError): registro.actualizar(creada['id'], 'inventado')

    def test_respuestas_y_historial(self):
        registro.guardar_respuesta('Salario', 'A convenir'); registro.guardar_respuesta('Salario', 'USD 6/h')
        self.assertEqual(registro.buscar_respuestas('Sal')[0]['respuesta'], 'USD 6/h')
        carpeta = Path(self.carpeta.name) / 'historial'; carpeta.mkdir()
        (carpeta / 'r.md').write_text('| QA | Acme Corp |\n| Soporte | Otra |\n', encoding='utf-8')
        self.assertEqual(registro.buscar_historial('acme qa')[0]['linea'], 1)

    def test_politicas(self):
        self.assertEqual(registro.consultar_politica('Ashby')['nivel'], 'aprobar')
        self.assertIn('advertencia', registro.consultar_politica('LinkedIn'))
        self.assertEqual(registro.fijar_politica('LinkedIn', 'enviar_solo')['nivel'], 'enviar_solo')
        with self.assertRaises(ValueError): registro.fijar_politica('x', 'libre')

class CvTests(Base):
    def test_valida_contra_el_perfil(self):
        for cambio in ({'summary': 'inventado'}, {'experiences': ['otra']}, {'skills': ['Magia']}, {'bullets': {'tienda': [9]}}):
            with self.assertRaises(ValueError): cv.validar(dict(SELECCION, **cambio), EJEMPLO)

    def test_html_escapa_y_respeta_el_orden(self):
        perfil_escapado = dict(EJEMPLO, name='<b>Ana</b>')
        contenido = cv.componer_html(SELECCION, perfil_escapado)
        self.assertIn('&lt;b&gt;Ana', contenido)
        self.assertNotIn('{{', contenido)
        self.assertNotIn('Respuesta a pedidos', contenido)
        self.assertNotIn('Publicaciones', contenido)

    def test_titulos_siguen_el_idioma(self):
        self.assertIn('<h2>Experience</h2>', cv.componer_html(SELECCION, EJEMPLO, idioma='en'))

    @unittest.skipUnless(navegador.ejecutable(), 'requiere un navegador Chromium')
    def test_genera_pdf_de_una_pagina(self):
        perfil.guardar(EJEMPLO)
        resultado = cv.generar('general es', SELECCION, motor='html')
        self.assertEqual(resultado['paginas'], 1)
        self.assertTrue(Path(resultado['pdf']).name.startswith('CV_Ana_Ejemplo'))
        self.assertTrue(Path(resultado['preview']).is_file())
        self.assertEqual(cv.leer_seleccion('general es'), SELECCION)

    @unittest.skipUnless(navegador.ejecutable(), 'requiere un navegador Chromium')
    def test_rechaza_lo_que_no_cabe_sin_publicar(self):
        largo = json.loads(json.dumps(EJEMPLO))
        largo['experience'][0]['bullets'] = ['Texto de relleno. ' * 20] * 80
        perfil.guardar(largo)
        seleccion = dict(SELECCION, bullets={'tienda': list(range(80))})
        with self.assertRaises(ValueError): cv.generar('largo', seleccion, motor='html')
        self.assertFalse((Path(self.carpeta.name) / 'cv' / 'largo').exists())

class NavegadorTests(Base):
    def test_elige_ruta_propia_y_rechaza_inexistente(self):
        with self.assertRaises(FileNotFoundError): navegador.elegir('no-existe')
        navegador.elegir(sys.executable)
        self.assertEqual(navegador.ejecutable(), sys.executable)

    def test_no_imprime_con_brave_si_hay_alternativa(self):
        opciones = navegador.disponibles()
        if len(opciones) > 1: self.assertNotIn('brave', navegador.impresor().lower())

OFERTA = """Auxiliar administrativa
Requisitos:
- Experiencia en atención al cliente y registro de inventario
- Título técnico en gestión administrativa
- Manejo de Excel avanzado y Python
Funciones:
- Responder pedidos por mensajería y organizar agendas"""
SIN_EVIDENCIA = {'texto': 'Manejo de Excel avanzado y Python', 'excluyente': False, 'estado': 'por_confirmar'}
CUMPLE = {'texto': 'Experiencia en atención al cliente', 'excluyente': True, 'estado': 'cumple', 'evidencia': 'Atención de clientes en mostrador'}

class AtsTests(Base):
    def setUp(self):
        super().setUp()
        perfil.guardar(EJEMPLO)

    def adaptada(self):
        return dict(SELECCION, summary=EJEMPLO['cv_summaries']['asistente'], skills=['Atención al cliente', 'Organización de agendas', 'Hojas de cálculo'], bullets={'tienda': [0, 1, 2]})

    def test_adaptar_mejora_y_no_supera_el_techo(self):
        resultado = ats.evaluar(OFERTA, 'Auxiliar administrativa', [CUMPLE, SIN_EVIDENCIA], self.adaptada())
        self.assertGreater(resultado['ats_adaptado'], resultado['ats_base'])
        self.assertLessEqual(resultado['ats_adaptado'], resultado['ats_techo'])
        self.assertEqual(resultado['mejora'], resultado['ats_adaptado'] - resultado['ats_base'])
        self.assertIn('python', resultado['brechas_reales'])
        self.assertIn('CV genérico %d → CV adaptado %d' % (resultado['ats_base'], resultado['ats_adaptado']), resultado['resumen'])
        self.assertEqual(resultado['oferta_caracteres'], len(OFERTA))

    def test_sin_evidencia_no_cumple(self):
        for requisito in (dict(CUMPLE, evidencia='Dirigí una multinacional'), dict(CUMPLE, evidencia=''), dict(CUMPLE, texto='Requisito inventado')):
            with self.assertRaises(ValueError): ats.evaluar(OFERTA, 'Auxiliar', [requisito], SELECCION)

    def test_evidencia_vale_en_cualquier_idioma_del_perfil(self):
        ingles = json.loads(json.dumps(EJEMPLO)); ingles['experience'][0]['bullets'] = ['Customer service at the counter.', 'Sales log.', 'Orders.']
        perfil.guardar(ingles, 'en')
        requisito = dict(CUMPLE, evidencia='Atención de clientes en mostrador')
        self.assertEqual(ats.revisar_requisitos([requisito], OFERTA, ingles), 100)
        self.assertEqual(ats.revisar_requisitos([dict(CUMPLE, evidencia='Customer service at the counter')], OFERTA, EJEMPLO), 100)

    def test_excluyente_incumplido_limita_y_descarta(self):
        resultado = ats.evaluar(OFERTA, 'Auxiliar', [CUMPLE, CUMPLE, dict(CUMPLE, estado='brecha', evidencia='')], self.adaptada())
        self.assertLessEqual(resultado['idoneidad'], ats.TOPE_EXCLUYENTE)
        self.assertEqual(resultado['decision'], 'no_aplicar')

    def test_excluyente_por_confirmar_pregunta(self):
        resultado = ats.evaluar(OFERTA, 'Auxiliar', [dict(CUMPLE, estado='por_confirmar', evidencia='')], self.adaptada())
        self.assertEqual(resultado['decision'], 'preguntar')

    def test_ignora_ruido_de_la_pagina(self):
        pesos, _, legibles = ats.terminos('Ver https://torre.ai/post/0wxMY16d-analitica el 2026-10-20 por COP 1093.24\nDominio de Selenium')
        self.assertEqual(set(pesos) & {'0wxmy16', '2026-10', '1093.24', 'http', 'torre.a'}, set())
        self.assertIn(ats.raiz('selenium'), pesos)
        self.assertEqual(legibles[ats.raiz('dominio')], 'dominio')

    def test_faltantes_legibles(self):
        faltan = ats.puntuar('Experiencia avanzada con Kubernetes y observabilidad\n' * 2, 'DevOps', 'Texto sin relación')['faltan']
        self.assertIn('observabilidad', faltan)

    def test_sinonimos_entre_idiomas(self):
        self.assertIn('ai', ats.raices('Inteligencia artificial aplicada'))
        self.assertEqual(ats.idioma_de('We are looking for you and the team with our tools'), 'en')

class ResultadosTests(Base):
    def test_seguimiento_cadencia_y_cierre(self):
        creada = registro.registrar('QA', 'Acme', 'torre', 'enviada')
        self.assertEqual(registro.seguimientos_pendientes(), [])
        with registro.closing(registro.conexion()) as base, base:
            base.execute("update postulaciones set seguir_el='2020-01-01'")
        self.assertEqual(len(registro.seguimientos_pendientes()), 1)
        self.assertNotEqual(registro.seguimiento_hecho(creada['id'], 'correo')['proximo'], 'ninguno')
        self.assertEqual(registro.seguimiento_hecho(creada['id'])['proximo'], 'ninguno')

    def test_responder_cancela_seguimiento(self):
        creada = registro.registrar('QA', 'Acme', 'torre', 'enviada')
        registro.actualizar(creada['id'], 'rechazada', motivo='Pide inglés C1')
        self.assertEqual(registro.listar()[0]['seguir_el'], '')
        self.assertEqual(registro.analisis()['motivos'][0], ('Pide inglés C1', 1))

    def test_analisis_tasas_y_mejora(self):
        for numero, estado in enumerate(('enviada', 'avanzo', 'rechazada', 'preparada')):
            registro.registrar('Cargo %d' % numero, 'Acme', 'torre', estado, cv='qa', idoneidad=80, ats_base=40, ats_adaptado=70)
        resultado = registro.analisis()
        self.assertEqual(resultado['por_sitio'][0]['enviadas'], 3)
        self.assertEqual(resultado['por_sitio'][0]['tasa_avance'], 33)
        self.assertEqual(resultado['por_idoneidad'][0]['grupo'], '70-100')
        self.assertEqual(resultado['mejora_ats_promedio'], 30)

    def test_importa_historial_sin_duplicar(self):
        archivo = Path(self.carpeta.name) / 'r.md'
        archivo.write_text("""## Torre (x)

| Cargo | Empresa | Enviada | Estado | Enlace |
|---|---|---|---|---|
| QA | Acme | 7 oct | Descartada por correo | [ver](https://a.co/1) |
| Soporte | Beta | 8 oct | Solicitud enviada | [ver](https://a.co/2) |
| Dev | Gama | 9 oct | Avanzó: entrevista | - |
| Ops | Delta | 9 oct | Por enviar | - |
""", encoding='utf-8')
        self.assertEqual(registro.importar_historial(archivo), {'importadas': 4, 'omitidas': 0})
        self.assertEqual(registro.importar_historial(archivo), {'importadas': 0, 'omitidas': 4})
        estados = {fila['cargo']: fila['estado'] for fila in registro.listar()}
        self.assertEqual(estados, {'QA': 'rechazada', 'Soporte': 'enviada', 'Dev': 'avanzo', 'Ops': 'incompleta'})

CAPTURA = """Page URL: https://empresa.example/form
- button "Siguiente" [ref=e1]
- button "Enviar solicitud" [ref=e2]
- textbox "Nombre" [ref=e3]"""
CLIC = {'target': 'e2', 'element': 'botón azul'}

class PuertaTests(Base):
    def puerta(self):
        nueva = puerta.Puerta(); nueva.observar(CAPTURA); return nueva

    def test_bloquea_por_etiqueta_real_aunque_el_agente_mienta(self):
        self.assertIn('BLOQUEADO', self.puerta().decidir('browser_click', CLIC))

    def test_deja_pasar_lo_que_no_envia(self):
        self.assertIsNone(self.puerta().decidir('browser_click', {'target': 'e1'}))
        self.assertIsNone(self.puerta().decidir('browser_type', {'target': 'e3', 'text': 'Ana'}))

    def test_otras_vias_de_envio(self):
        for herramienta, argumentos in (('browser_press_key', {'key': 'Enter'}), ('browser_type', {'target': 'e3', 'text': 'x', 'submit': True}), ('browser_evaluate', {'function': '() => document.forms[0].requestSubmit()'}), ('browser_run_code_unsafe', {'code': 'x'})):
            self.assertIn('BLOQUEADO', self.puerta().decidir(herramienta, argumentos), herramienta)

    def test_selector_no_evade_la_puerta(self):
        for selector in ('button[type=submit]', '#enviar', 'form > button:nth-child(2)', 'text=Enviar solicitud'):
            self.assertIn('BLOQUEADO', self.puerta().decidir('browser_click', {'target': selector}), selector)

    def test_selector_pasa_si_la_pagina_no_puede_enviar(self):
        limpia = puerta.Puerta(); limpia.observar('Page URL: https://x.example/lista\n- link "Oferta" [ref=e1]')
        self.assertIsNone(limpia.decidir('browser_click', {'target': 'a.oferta'}))

    def test_lee_la_url_del_listado_de_pestanas(self):
        nueva = puerta.Puerta(); nueva.observar('- 0: [Correo](https://mail.example/)\n- 1: (current) [Form](https://empresa.example/f)')
        self.assertEqual(nueva.url, 'https://empresa.example/f')

    def test_firma_se_devuelve_si_la_accion_falla(self):
        solicitud = aprobaciones.solicitar('https://empresa.example/form', 'QA', 'Acme')
        aprobaciones.resolver(solicitud['id'], True)
        class Falso:
            sesion = 'x'
            def enviar(self, mensaje): return {'jsonrpc': '2.0', 'id': mensaje['id'], 'result': {'content': [{'type': 'text', 'text': 'Error'}], 'isError': True}}
        mensaje = {'id': 1, 'method': 'tools/call', 'params': {'name': 'browser_click', 'arguments': CLIC}}
        puerta.atender(mensaje, self.puerta(), Falso())
        self.assertEqual(aprobaciones.consultar(solicitud['id'])['estado'], 'aprobada')

    def test_firma_vale_una_sola_vez_y_solo_en_su_sitio(self):
        solicitud = aprobaciones.solicitar('https://empresa.example/form', 'QA', 'Acme')
        self.assertIn('BLOQUEADO', self.puerta().decidir('browser_click', CLIC))
        aprobaciones.resolver(solicitud['id'], True)
        otra = self.puerta(); otra.url = 'https://otro.example/x'
        self.assertIn('BLOQUEADO', otra.decidir('browser_click', CLIC))
        self.assertIsNone(self.puerta().decidir('browser_click', CLIC))
        self.assertIn('BLOQUEADO', self.puerta().decidir('browser_click', CLIC))

    def test_firma_vencida_o_rechazada(self):
        solicitud = aprobaciones.solicitar('https://empresa.example/form', 'QA', 'Acme')
        aprobaciones.resolver(solicitud['id'], False)
        with self.assertRaises(ValueError): aprobaciones.resolver(solicitud['id'], True)
        segunda = aprobaciones.solicitar('https://empresa.example/form', 'QA', 'Acme')
        aprobaciones.resolver(segunda['id'], True)
        with aprobaciones.closing(aprobaciones._conexion()) as base, base: base.execute("update aprobaciones set vence='2020-01-01 00:00'")
        self.assertIn('BLOQUEADO', self.puerta().decidir('browser_click', CLIC))

    def test_niveles(self):
        registro.fijar_politica('empresa', 'solo_rellenar')
        self.assertIn('BLOQUEADO', self.puerta().decidir('browser_click', CLIC))
        registro.fijar_politica('empresa', 'solo_preparar')
        self.assertIn('BLOQUEADO', self.puerta().decidir('browser_type', {'target': 'e3', 'text': 'x'}))
        registro.fijar_politica('empresa', 'enviar_solo')
        self.assertIsNone(self.puerta().decidir('browser_click', CLIC))

    def test_aplicar_solo_envia_en_sitios_que_lo_usan_asi(self):
        self.assertFalse(puerta.es_envio('https://linkedin.com/jobs', 'button Aplicar'))
        self.assertTrue(puerta.es_envio('https://magneto365.com/x', 'button Aplicar'))

    def test_el_agente_no_puede_firmar(self):
        self.assertFalse({'aprobacion_resolver', 'aprobar'} & set(mcp_server.HERRAMIENTAS))

PANEL = """Page URL: http://127.0.0.1:8770/#mesa
- button "Aprobar envío" [ref=e5]"""
COBRO = """Page URL: https://empresa.example/pago
- checkbox "Declaro bajo la gravedad de juramento que la información es veraz" [ref=e7]
- button "Pagar con PSE" [ref=e8]
- button [ref=e9]"""

class PuertaReforzadaTests(Base):
    """Huecos hallados en la revisión del 9 nov 2026: la IA no puede aprobarse sola ni rodear la puerta."""
    def puerta(self, captura=CAPTURA):
        nueva = puerta.Puerta(); nueva.observar(captura); return nueva

    def test_no_abre_el_panel_ni_direcciones_locales(self):
        for url in ('http://127.0.0.1:8770/', 'http://localhost:8770/#mesa', 'http://[::1]:8770/', 'http://0.0.0.0:9222/json',
                    'file:///C:/datos/postulador.db', 'javascript:alert(1)', 'data:text/html,x', 'chrome://settings', 'view-source:https://x.example'):
            self.assertIn('BLOQUEADO', self.puerta().decidir('browser_navigate', {'url': url}), url)
            self.assertIn('BLOQUEADO', self.puerta().decidir('browser_tabs', {'action': 'new', 'url': url}), url)
        self.assertIsNone(self.puerta().decidir('browser_navigate', {'url': 'https://empresa.example/form'}))

    def test_no_actua_si_llego_al_panel(self):
        dentro = self.puerta(PANEL)
        self.assertIn('BLOQUEADO', dentro.decidir('browser_click', {'target': 'e5'}))
        self.assertIn('BLOQUEADO', dentro.decidir('browser_snapshot', {}))
        self.assertIsNone(dentro.decidir('browser_navigate', {'url': 'https://empresa.example/'}))

    def test_envio_con_tilde_y_otros_verbos(self):
        for etiqueta in ('button Aprobar envío', 'button Postularme', 'button Inscribirme', 'button Radicar', 'button Confirmar inscripción'):
            self.assertTrue(puerta.es_envio('https://x.example/', etiqueta), etiqueta)

    def test_solo_pasan_herramientas_conocidas(self):
        for herramienta in ('browser_install', 'browser_inventada', 'browser_evaluate', 'browser_run_code_unsafe'):
            self.assertIn('BLOQUEADO', self.puerta().decidir(herramienta, {'function': '() => document.title'}), herramienta)
        self.assertIn('BLOQUEADO', self.puerta().decidir('browser_evaluate', {'function': '() => fetch("/apply", {method: "POST"})'}))

    def test_la_lista_de_herramientas_no_ofrece_las_bloqueadas(self):
        class Falso:
            sesion = 'x'
            def enviar(self, mensaje): return {'jsonrpc': '2.0', 'id': mensaje['id'], 'result': {'tools': [{'name': 'browser_click'}, {'name': 'browser_evaluate'}, {'name': 'browser_install'}]}}
        respuesta = puerta.atender({'id': 1, 'method': 'tools/list'}, puerta.Puerta(), Falso())
        self.assertEqual([h['name'] for h in respuesta['result']['tools']], ['browser_click', 'formulario_listo', 'formulario_abandonar'])

    def test_sube_solo_cv_por_nombre(self):
        carpeta_cv = Path(self.carpeta.name) / 'cv' / 'asesora'; carpeta_cv.mkdir(parents=True)
        (carpeta_cv / 'CV_Ana.pdf').write_bytes(b'%PDF'); (carpeta_cv / 'Carta_Ana.pdf').write_bytes(b'%PDF carta')
        enviados = []
        class Falso:
            sesion = 'x'
            def enviar(self, mensaje):
                enviados.append(mensaje['params']['arguments'])
                return {'jsonrpc': '2.0', 'id': mensaje['id'], 'result': {'content': [{'type': 'text', 'text': 'ok'}]}}
        subir = lambda herramienta, rutas: puerta.atender({'id': 1, 'method': 'tools/call', 'params': {'name': herramienta, 'arguments': {'paths': rutas}}}, self.puerta(), Falso())
        self.assertNotIn('isError', subir('browser_file_upload', ['cv:asesora'])['result'])
        self.assertEqual(enviados[-1]['paths'], [str(carpeta_cv / 'CV_Ana.pdf')])
        for rutas in ([str(carpeta_cv / 'CV_Ana.pdf')], ['cv:../x'], ['cv:Asesora Juridica'], ['cv:no_existe'], ['doc:1'], [str(Path(self.carpeta.name) / 'postulador.db')], ['C:/Windows/win.ini']):
            for herramienta in ('browser_file_upload', 'browser_drop'):
                respuesta = subir(herramienta, rutas)['result']
                self.assertTrue(respuesta.get('isError'), (herramienta, rutas))
                self.assertIn('BLOQUEADO', respuesta['content'][0]['text'])
        self.assertEqual(len(enviados), 1)
        self.assertEqual(cv.pdf_de('asesora').name, 'CV_Ana.pdf')

    def test_nunca_paga_ni_declara_aunque_envie_solo(self):
        registro.fijar_politica('empresa.example', 'enviar_solo')
        cobro = self.puerta(COBRO)
        self.assertIn('BLOQUEADO', cobro.decidir('browser_click', {'target': 'e7'}))
        self.assertIn('BLOQUEADO', cobro.decidir('browser_click', {'target': 'e8'}))
        self.assertIn('BLOQUEADO', cobro.decidir('browser_fill_form', {'fields': [{'name': 'Declaro bajo juramento', 'type': 'checkbox', 'ref': 'e7', 'value': 'true'}]}))
        self.assertIn('BLOQUEADO', self.puerta().decidir('browser_navigate', {'url': 'https://registro.pse.com.co/PSEUserRegister/'}))

    def test_otras_teclas_dialogos_y_botones_sin_nombre(self):
        for tecla in ('NumpadEnter', ' ', 'Space'):
            self.assertIn('BLOQUEADO', self.puerta().decidir('browser_press_key', {'key': tecla}), tecla)
        self.assertIn('BLOQUEADO', self.puerta().decidir('browser_handle_dialog', {'accept': True}))
        self.assertIsNone(self.puerta().decidir('browser_handle_dialog', {'accept': False}))
        self.assertIn('BLOQUEADO', self.puerta(COBRO).decidir('browser_click', {'target': 'e9'}))

    def test_politicas_por_dominio_exacto(self):
        with self.assertRaises(ValueError): registro.fijar_politica('http', 'enviar_solo')
        with self.assertRaises(ValueError): registro.fijar_politica('com', 'enviar_solo')
        registro.fijar_politica('https://www.Empresa.example/empleos', 'enviar_solo')
        self.assertEqual(registro.nivel_de_url('https://empleos.empresa.example/f'), 'enviar_solo')
        self.assertEqual(registro.nivel_de_url('https://miempresa.example.net/f'), 'aprobar')
        registro.fijar_politica('magneto', 'solo_rellenar')
        self.assertEqual(registro.nivel_de_url('https://www.magneto365.com/es/x'), 'solo_rellenar')
        self.assertFalse(puerta.es_envio('https://magneto-falso.example/x', 'button Aplicar'))

    def test_el_agente_no_cambia_politicas_ni_navegador(self):
        self.assertFalse({'politica_fijar', 'navegador_elegir'} & set(mcp_server.HERRAMIENTAS))

class BusquedaTests(Base):
    def test_por_defecto_y_guardado(self):
        self.assertEqual(busqueda.leer()['antiguedad_horas'], 48)
        guardadas = busqueda.guardar({'antiguedad_horas': '168', 'modalidades': ['remoto', 'hibrido', 'otra'], 'ubicaciones': 'Colombia, Bogotá, colombia',
                                      'cargos': ['QA', ' asistente  virtual '], 'excluir': 'ingeniería civil', 'salario_minimo': 'USD 6/h', 'idiomas': ['es', 'en', 'xx']})
        self.assertEqual(guardadas, {'antiguedad_horas': 168, 'modalidades': ['remoto', 'hibrido'], 'ubicaciones': ['Colombia', 'Bogotá'], 'cargos': ['QA', 'asistente virtual'],
                                     'excluir': ['ingeniería civil'], 'salario_minimo': 'USD 6/h', 'idiomas': ['es', 'en']})
        self.assertEqual(busqueda.leer(), guardadas)

    def test_rechaza_valores_raros(self):
        for malo in ({'antiguedad_horas': 0}, {'antiguedad_horas': 'mucho'}, {'antiguedad_horas': 5000}, {'modalidades': []}, {'modalidades': ['flotante']}, {'cargos': ['x' * 61]}, {'cargos': ['c%d' % i for i in range(21)]}):
            with self.assertRaises(ValueError, msg=str(malo)): busqueda.guardar(malo)

    def test_url_de_linkedin_aplica_preferencias(self):
        from urllib.parse import parse_qs, urlsplit
        busqueda.guardar({'antiguedad_horas': 72, 'modalidades': ['remoto', 'hibrido'], 'ubicaciones': 'Colombia'})
        url = busqueda.url_linkedin('asistente virtual', pagina=2)['url']
        self.assertTrue(url.startswith('https://www.linkedin.com/jobs-guest/'))
        consulta = {clave: valor[0] for clave, valor in parse_qs(urlsplit(url).query).items()}
        self.assertEqual(consulta, {'keywords': 'asistente virtual', 'location': 'Colombia', 'geoId': '100876405', 'f_TPR': 'r259200', 'f_WT': '2,3', 'start': '20'})
        busqueda.guardar({'modalidades': ['remoto', 'hibrido', 'presencial']})
        self.assertNotIn('f_WT', busqueda.url_linkedin('QA', 'Bogotá')['url'])
        self.assertNotIn('geoId', busqueda.url_linkedin('QA', 'Bogotá')['url'])
        with self.assertRaises(ValueError): busqueda.url_linkedin('  ')

    def test_el_agente_lee_pero_no_cambia_preferencias(self):
        self.assertIn('busqueda_preferencias', mcp_server.HERRAMIENTAS)
        self.assertIn('busqueda', mcp_server._contexto())
        self.assertFalse({nombre for nombre in mcp_server.HERRAMIENTAS if 'busqueda' in nombre and nombre != 'busqueda_preferencias'})

    def test_la_puerta_lista_herramientas_sin_abrir_el_navegador(self):
        class SinNavegador:
            sesion = None
            def iniciar(self): raise AssertionError('no debe abrir el navegador para listar')
        respuesta = puerta.atender({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}, puerta.Puerta(), SinNavegador())
        nombres = {herramienta['name'] for herramienta in respuesta['result']['tools']}
        self.assertIn('browser_navigate', nombres)
        self.assertEqual(nombres - puerta.PERMITIDAS, {'formulario_listo', 'formulario_abandonar'})

    def test_la_puerta_abre_pestana_propia_antes_de_navegar(self):
        class Falso:
            sesion, enviados = 'x', []
            def enviar(self, mensaje):
                self.enviados.append(mensaje['params']['name'] + ':' + str(mensaje['params']['arguments'].get('action', '')))
                return {'jsonrpc': '2.0', 'id': mensaje['id'], 'result': {'content': [{'type': 'text', 'text': 'ok'}]}}
        servicio, nueva = Falso(), puerta.Puerta()
        for numero in (1, 2):
            puerta.atender({'id': numero, 'method': 'tools/call', 'params': {'name': 'browser_navigate', 'arguments': {'url': 'https://x.example/%d' % numero}}}, nueva, servicio)
        self.assertEqual(servicio.enviados, ['browser_tabs:new', 'browser_navigate:', 'browser_navigate:'])

class ArranqueTests(Base):
    def test_crea_la_carpeta_con_la_ia_encerrada(self):
        import tomllib
        destino = Path(self.carpeta.name) / 'arranque'
        (destino / 'entrada').mkdir(parents=True); (destino / 'entrada' / 'CV.pdf').write_bytes(b'%PDF')
        resultado = arranque.crear(destino, accesos=False)
        self.assertNotIn('accesos_directos', resultado)
        permisos = json.loads((destino / '.claude' / 'settings.json').read_text(encoding='utf-8'))['permissions']
        for herramienta in ('Bash', 'PowerShell', 'Edit', 'Write', 'Read', 'Glob', 'Grep', 'WebFetch', 'mcp__claude-in-chrome', 'mcp__Claude_Browser', 'mcp__computer-use', 'mcp__terminal', 'mcp__plugin_playwright_playwright'):
            self.assertIn(herramienta, permisos['deny'])
        self.assertEqual(json.loads(archivo_equipo().read_text(encoding='utf-8')), {'version': 1, 'nivel_maximo': 'solo_rellenar', 'arranque': str(destino.resolve())})
        self.assertIn('diagnostico', (destino / 'CLAUDE.md').read_text(encoding='utf-8'))
        self.assertIn(str(destino.resolve()), (destino / 'LEEME.html').read_text(encoding='utf-8'))
        self.assertEqual(arranque.diagnostico()['problemas'], [])
        ajustes_claude = destino / '.claude' / 'settings.json'
        alterado = json.loads(ajustes_claude.read_text(encoding='utf-8')); alterado['permissions']['deny'].remove('Read')
        ajustes_claude.write_text(json.dumps(alterado), encoding='utf-8')
        self.assertFalse(arranque.diagnostico()['permisos_al_dia'])
        self.assertTrue(arranque.diagnostico()['problemas'])
        self.assertEqual(permisos['disableBypassPermissionsMode'], 'disable')
        servidores = json.loads((destino / '.mcp.json').read_text(encoding='utf-8'))['mcpServers']
        self.assertEqual(set(servidores), {'postulador', 'playwright'})
        for servidor in servidores.values():
            self.assertTrue(Path(servidor['command']).is_absolute())
            self.assertEqual(servidor['args'][0], '-m')
            self.assertEqual(servidor['env']['PYTHONPATH'], str(RAIZ))
            self.assertNotIn('POSTULADOR_DATOS', servidor['env'])
        codex = tomllib.loads((destino / '.codex' / 'config.toml').read_text(encoding='utf-8'))
        self.assertEqual(codex['sandbox_mode'], 'read-only')
        self.assertEqual(codex['mcp_servers']['playwright']['args'], servidores['playwright']['args'])
        self.assertTrue((destino / '.claude' / 'skills' / 'postulador' / 'SKILL.md').is_file())
        self.assertIn('Solo usas las herramientas', (destino / 'CLAUDE.md').read_text(encoding='utf-8'))
        self.assertEqual((destino / 'entrada' / 'CV.pdf').read_bytes(), b'%PDF')

    def test_no_se_crea_dentro_del_codigo(self):
        for destino in (RAIZ, RAIZ / 'datos_usuario', RAIZ.parent):
            with self.assertRaises(ValueError): arranque.crear(destino, accesos=False)
        with self.assertRaises(ValueError): arranque.crear(Path(self.carpeta.name) / 'x', nivel_maximo='libre', accesos=False)

    def test_acceso_directo_al_panel_sin_ventana(self):
        from unittest import mock
        llamadas = []
        def falso(comando, env=None, **opciones):
            llamadas.append(env); return subprocess.CompletedProcess(comando, 0, 'C:/Escritorio/x.lnk', '')
        with mock.patch.object(arranque.subprocess, 'run', falso), mock.patch.object(arranque.os, 'name', 'nt'), mock.patch.object(arranque, 'acceso_directo', ACCESO_REAL):
            resultado = arranque.crear(Path(self.carpeta.name) / 'arranque', accesos=True)
        self.assertEqual(len(resultado['accesos_directos']), 2)
        panel_lnk = llamadas[0]
        self.assertEqual(panel_lnk['PD_NOMBRE'], 'Panel de Radicado.lnk')
        self.assertTrue(Path(panel_lnk['PD_DESTINO']).is_absolute())
        self.assertEqual(panel_lnk['PD_ARGS'], '-m postulador panel --abrir')
        self.assertTrue(llamadas[1]['PD_DESTINO'].endswith('LEEME.html'))

    def test_la_migracion_sella_el_perfil_existente_una_vez(self):
        perfil.guardar(EJEMPLO)
        crudo = json.loads(perfil.ruta().read_text(encoding='utf-8')); crudo.pop('schema_version'); perfil.ruta().write_text(json.dumps(crudo), encoding='utf-8')
        self.assertEqual(arranque.crear(Path(self.carpeta.name) / 'arranque', accesos=False)['perfiles_sellados'], ['perfil.json'])
        self.assertTrue(perfil.sello_vigente())
        self.assertNotIn('perfiles_sellados', arranque.crear(Path(self.carpeta.name) / 'arranque', accesos=False))

class UbicacionTests(Base):
    def setUp(self):
        super().setUp()
        self.otra = tempfile.TemporaryDirectory(); self.addCleanup(self.otra.cleanup)
        previo = os.environ.get('LOCALAPPDATA')
        os.environ['LOCALAPPDATA'] = str(Path(self.otra.name) / 'local')
        self.addCleanup(lambda: os.environ.__setitem__('LOCALAPPDATA', previo) if previo else os.environ.pop('LOCALAPPDATA', None))

    def sin_variable_de_datos(self):
        os.environ.pop('POSTULADOR_DATOS')
        self.addCleanup(os.environ.__setitem__, 'POSTULADOR_DATOS', self.carpeta.name)

    def test_mueve_verifica_y_deja_respaldo(self):
        from postulador import datos
        registro.registrar('QA', 'Acme', 'torre', 'enviada')
        (Path(self.carpeta.name) / 'cv' / 'qa').mkdir(parents=True); (Path(self.carpeta.name) / 'cv' / 'qa' / 'CV.pdf').write_bytes(b'%PDF-1')
        destino = Path(self.otra.name) / 'usb' / 'Postulador'
        resultado = ubicacion.mover(destino, comprobar_panel=False)
        self.assertGreaterEqual(resultado['archivos'], 2)
        self.sin_variable_de_datos()
        self.assertEqual(datos(), destino)
        self.assertEqual(registro.listar()[0]['empresa'], 'Acme')
        self.assertEqual((destino / 'cv' / 'qa' / 'CV.pdf').read_bytes(), b'%PDF-1')
        self.assertTrue((Path(self.carpeta.name) / 'cv' / 'qa' / 'CV.pdf').is_file())
        self.assertIn(str(destino), (Path(self.carpeta.name) / 'MOVIDOS.txt').read_text(encoding='utf-8'))

    def test_sin_la_usb_avisa_y_no_crea_nada(self):
        from postulador import datos
        destino = Path(self.otra.name) / 'usb'
        ubicacion.mover(destino, comprobar_panel=False)
        self.sin_variable_de_datos()
        (destino / '.postulador-datos').write_text('otra-usb', encoding='utf-8')
        with self.assertRaises(DatosNoDisponibles): datos()
        shutil.rmtree(destino)
        with self.assertRaises(DatosNoDisponibles): datos()
        self.assertFalse(destino.exists())

    def test_rechaza_destinos_peligrosos(self):
        lleno = Path(self.otra.name) / 'lleno'; lleno.mkdir(); (lleno / 'x.txt').write_text('x')
        for destino in (lleno, Path(self.carpeta.name) / 'dentro', RAIZ / 'datos_nuevos'):
            with self.assertRaises(ValueError, msg=str(destino)): ubicacion.mover(destino, comprobar_panel=False)

class PanelTests(Base):
    def setUp(self):
        super().setUp()
        self.servidor = panel.crear_servidor(0)
        self.puerto = self.servidor.server_port
        import threading
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.addCleanup(self.servidor.server_close); self.addCleanup(self.servidor.shutdown)

    def pedir(self, metodo, ruta, cuerpo=None, cabeceras=None):
        conexion = http.client.HTTPConnection('127.0.0.1', self.puerto)
        conexion.request(metodo, ruta, json.dumps(cuerpo) if cuerpo is not None else None, cabeceras or {})
        respuesta = conexion.getresponse(); dato = respuesta.read(); conexion.close()
        return respuesta.status, dato

    def token(self): return json.loads(self.pedir('GET', '/api/sesion')[1])['token']

    def test_sirve_vistas(self):
        for ruta in ('/', '/app.js', '/styles.css', '/api/resumen', '/api/aprobaciones', '/api/postulaciones', '/api/postulaciones?estado=rellenada,reportada', '/api/olvidadas',
                     '/api/seguimientos', '/api/ajustes', '/api/vivo', '/api/informes', '/api/cv', '/api/documentos', '/api/perfil/carrera'):
            self.assertEqual(self.pedir('GET', ruta)[0], 200, ruta)

    def test_rutas_de_la_ia_oculta_ya_no_existen(self):
        token = self.token()
        for ruta in ('/api/tareas', '/api/tareas/1'):
            self.assertEqual(self.pedir('GET', ruta)[0], 404, ruta)
        for ruta in ('/api/tareas', '/api/conectar', '/api/cv/x/agente'):
            self.assertIn(self.pedir('POST', ruta, {'tarea': 'x', 'motor': 'claude'}, {'X-Panel-Token': token})[0], (400, 404), ruta)
        texto = (RAIZ / 'postulador' / 'web' / 'app.js').read_text(encoding='utf-8') + (RAIZ / 'postulador' / 'web' / 'index.html').read_text(encoding='utf-8')
        for palabra in ('firmar', 'Firmada', 'Pedir al agente', '/api/tareas', '/api/conectar'):
            self.assertNotIn(palabra, texto)

    def test_acciones_de_ella_y_comprobante(self):
        self.tope('solo_rellenar')
        creada = registro.registrar('Abogada', 'Firma', 'portal', 'preparada')
        comprobantes.crear(creada['id'], 'https://portal.example/f', '2026-01-01 10:00:00', [{'campo': 'textbox Nombre', 'valor': 'Ana', 'hora': '10:00:01'}], [], [], '', EditorCvTests.PNG, 0)
        filas = json.loads(self.pedir('GET', '/api/postulaciones?estado=rellenada,reportada')[1])
        self.assertEqual([fila['id'] for fila in filas], [creada['id']])
        dato = json.loads(self.pedir('GET', '/api/comprobantes/%d' % filas[0]['comprobante'])[1])
        self.assertEqual(dato['campos'][0]['valor'], 'Ana')
        self.assertNotIn('imagen', dato)
        estado, imagen = self.pedir('GET', '/api/comprobantes/%d/imagen' % filas[0]['comprobante'])
        self.assertEqual((estado, imagen[:4]), (200, b'\x89PNG'))
        self.assertEqual(self.pedir('POST', '/api/postulaciones/%d' % creada['id'], {'accion': 'la_envie'})[0], 403)
        self.assertEqual(self.pedir('POST', '/api/postulaciones/%d' % creada['id'], {'accion': 'la_envie'}, {'X-Panel-Token': self.token()})[0], 200)
        self.assertEqual(registro.obtener(creada['id'])['estado'], 'enviada')
        self.assertEqual(json.loads(self.pedir('GET', '/api/aprobaciones')[1]), [])

    def test_solo_se_incrusta_en_vscode(self):
        conexion = http.client.HTTPConnection('127.0.0.1', self.puerto); conexion.request('GET', '/')
        politica = conexion.getresponse().getheader('Content-Security-Policy'); conexion.close()
        self.assertIn('frame-ancestors vscode-webview:', politica)
        self.assertNotIn('frame-ancestors *', politica)

    def test_rechaza_otro_origen_host_y_sin_token(self):
        self.assertEqual(self.pedir('GET', '/api/sesion', cabeceras={'Host': 'evil.example'})[0], 403)
        self.assertEqual(self.pedir('GET', '/api/sesion', cabeceras={'Origin': 'http://evil.example'})[0], 403)
        self.assertEqual(self.pedir('POST', '/api/aprobaciones/1', {'aprobar': True})[0], 403)

    def test_preferencias_de_busqueda_desde_el_panel(self):
        self.assertEqual(self.pedir('POST', '/api/busqueda', {'antiguedad_horas': 72})[0], 403)
        estado, cuerpo = self.pedir('POST', '/api/busqueda', {'antiguedad_horas': 72, 'modalidades': ['remoto'], 'cargos': 'QA, asistente virtual'}, {'X-Panel-Token': self.token()})
        self.assertEqual(estado, 200)
        self.assertEqual(json.loads(self.pedir('GET', '/api/ajustes')[1])['busqueda']['cargos'], ['QA', 'asistente virtual'])

    def test_firma_desde_el_panel(self):
        solicitud = aprobaciones.solicitar('https://empresa.example/form', 'QA', 'Acme')
        estado, _ = self.pedir('POST', '/api/aprobaciones/%d' % solicitud['id'], {'aprobar': True}, {'X-Panel-Token': self.token()})
        self.assertEqual(estado, 200)
        self.assertEqual(aprobaciones.consultar(solicitud['id'])['estado'], 'aprobada')

    def test_foto_exige_token(self):
        self.assertEqual(self.pedir('POST', '/api/foto', {'x': 1})[0], 403)

    def test_no_sale_de_la_carpeta_de_cv(self):
        self.assertEqual(self.pedir('GET', '/cv/..%2F..%2F/perfil.json')[0], 404)
        self.assertEqual(self.pedir('GET', '/cv/x/..%2Fperfil.pdf')[0], 404)

class ActividadTests(Base):
    def test_registra_acciones_de_herramientas_sin_argumentos(self):
        mcp_server._llamar('respuesta_guardar', {'pregunta': 'Salario', 'respuesta': 'DATO SECRETO'})
        self.assertEqual(actividad.recientes()[0]['accion'], 'respuesta_guardar')
        self.assertNotIn('DATO SECRETO', actividad._archivo().read_text(encoding='utf-8'))

    def test_bloqueo_queda_visible_y_sin_texto_escrito(self):
        nueva = puerta.Puerta(); nueva.observar(CAPTURA)
        puerta.atender({'id': 1, 'method': 'tools/call', 'params': {'name': 'browser_click', 'arguments': CLIC}}, nueva, type('S', (), {'sesion': 'x'})())
        self.assertTrue(actividad.recientes()[0]['bloqueada'])

    def test_recorta_el_archivo(self):
        actividad.anotar('a')
        actividad._archivo().write_text('{"accion":"x"}\n' * 40000, encoding='utf-8')
        actividad.anotar('b')
        self.assertLessEqual(len(actividad.recientes(100000)), actividad.MOSTRAR + 1)

    def test_informe_y_ruta_segura(self):
        ruta = Path(actividad.guardar_informe('Revisión de hoy', 'Tres ofertas.')['informe'])
        self.assertTrue(ruta.name.endswith('revision_de_hoy.md'))
        self.assertIn('Tres ofertas', actividad.leer_informe(ruta.name)['contenido'])
        with self.assertRaises(ValueError): actividad.leer_informe('../perfil.md')

class EditorCvTests(Base):
    PNG = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082')

    def setUp(self):
        super().setUp()
        perfil.guardar(EJEMPLO)

    def crear(self, nombre='qa', **opciones):
        return cv.generar(nombre, SELECCION, motor='html', **opciones)

    def test_ajustes_rechazan_inyeccion_y_valores_raros(self):
        for cambio in ({'color': 'red;}body{display:none'}, {'fuente': 'x"; }'}, {'tamano': 30}, {'foto': 'arriba'}):
            with self.assertRaises(ValueError): cv.limpiar_ajustes(cambio)

    def test_tres_disenos_con_foto(self):
        cv.guardar_foto(self.PNG)
        for diseno in ('columna', 'clasico', 'editorial'):
            contenido = cv.componer_html(SELECCION, EJEMPLO, cv._ruta_plantilla(diseno), 'es', {'foto': 'derecha'})
            self.assertIn('data:image/png;base64', contenido, diseno)
            self.assertNotIn('{{', contenido)
        self.assertNotIn('<img', cv.componer_html(SELECCION, EJEMPLO, ajustes={'foto': 'ninguna'}))

    def test_foto_invalida(self):
        with self.assertRaises(ValueError): cv.guardar_foto(b'<script>alert(1)</script>')

    @unittest.skipUnless(navegador.impresor(), 'requiere un navegador')
    def test_ajustar_conserva_seleccion_y_persiste(self):
        self.crear()
        resultado = cv.ajustar('qa', {'plantilla': 'editorial', 'fuente': 'Georgia', 'tamano': 9.5})
        self.assertEqual(resultado['nombre'], 'qa')
        guardados = cv.leer_ajustes('qa')
        self.assertEqual((guardados['plantilla'], guardados['fuente'], guardados['tamano']), ('editorial', 'Georgia', 9.5))
        self.assertEqual(cv.leer_seleccion('qa'), SELECCION)

    @unittest.skipUnless(navegador.impresor(), 'requiere un navegador')
    def test_cv_de_word_queda_intacto(self):
        self.crear()
        original = Path(self.carpeta.name) / 'cv' / 'qa' / 'CV_Ana.docx'; original.write_bytes(b'word')
        resultado = cv.ajustar('qa', {'fuente': 'Verdana'})
        self.assertEqual(resultado['nombre'], 'qa_editado')
        self.assertEqual(original.read_bytes(), b'word')

    @unittest.skipUnless(navegador.impresor(), 'requiere un navegador')
    def test_columna_deja_el_contacto_arriba(self):
        pdf = self.crear()['pdf']
        texto = ats.extraer_pdf(pdf)
        if texto: self.assertLess(ats.plano(texto).find('ana@ejemplo.com') / len(ats.plano(texto)), ats.PORCION_CONTACTO)

    @unittest.skipUnless(navegador.impresor(), 'requiere un navegador')
    def test_comentarios_del_panel_al_agente(self):
        self.crear()
        nuevo = cv.comentar('qa', 'Quita la feria')
        self.assertEqual(cv.comentarios_pendientes()[0]['cv'], 'qa')
        cv.resolver_comentario('qa', nuevo['id'], 'Quitada')
        self.assertEqual(cv.comentarios_pendientes(), [])
        with self.assertRaises(ValueError): cv.comentar('qa', '  ')

    @unittest.skipUnless(navegador.impresor(), 'requiere un navegador')
    def test_editorial_usa_serifa_y_detalle_trae_la_revision(self):
        self.crear(plantilla='editorial')
        self.assertEqual(cv.leer_ajustes('qa')['fuente'], 'Georgia')
        self.assertIn('problemas', cv.detalle('qa')['revision'])

    def test_rutas_no_salen_de_cv(self):
        with self.assertRaises(FileNotFoundError): cv.detalle('../..')

class PortalesTests(Base):
    def test_normaliza_filtra_y_reporta_errores(self):
        (Path(self.carpeta.name) / 'tableros.json').write_text(json.dumps({'boards': [{'source': 'ashby', 'site': 'acme'}, {'source': 'lever', 'site': 'beta'}, {'source': 'x', 'site': 'y'}]}), encoding='utf-8')
        def falso(url):
            if 'ashby' in url: return {'jobs': [{'title': 'QA Analyst', 'jobUrl': 'https://a/1', 'location': 'Remote LATAM', 'descriptionPlain': 'Testing'}, {'title': 'Chef', 'jobUrl': 'https://a/2', 'location': 'Paris', 'descriptionPlain': 'Cocina'}]}
            raise OSError('sin red')
        resultado = portales.buscar('qa', leer=falso)
        self.assertEqual([oferta['cargo'] for oferta in resultado['ofertas']], ['QA Analyst'])
        self.assertEqual(len(resultado['errores']), 2)

class CartaTests(Base):
    @unittest.skipUnless(navegador.impresor(), 'requiere un navegador')
    def test_genera_y_senala_cifras_nuevas(self):
        perfil.guardar(EJEMPLO)
        texto = 'Estimado equipo: ' + 'me interesa el cargo por mi experiencia en atención al cliente. ' * 8 + 'Aumenté las ventas en 87 por ciento.'
        resultado = cv.generar_carta('general', texto)
        self.assertTrue(Path(resultado['pdf']).name.startswith('Carta_Ana'))
        self.assertIn('87', resultado['cifras_sin_respaldo'])

class McpTests(Base):
    def llamar(self, herramienta, **argumentos):
        return mcp_server.atender({'id': 1, 'method': 'tools/call', 'params': {'name': herramienta, 'arguments': argumentos}})['result']

    def test_guia_no_sale_de_la_skill(self):
        self.assertIn('SKILL.md', json.loads(self.llamar('guia_leer')['content'][0]['text']))
        self.assertIn('Postulador', self.llamar('guia_leer', nombre='SKILL.md')['content'][0]['text'])
        self.assertTrue(self.llamar('guia_leer', nombre='../../AGENTS.md')['isError'])

    def test_error_llega_como_resultado(self):
        self.assertTrue(self.llamar('perfil_leer')['isError'])
        self.assertTrue(self.llamar('no_existe')['isError'])

    def test_protocolo_por_stdio(self):
        entrada = '\n'.join(json.dumps(m) for m in (
            {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})) + '\n'
        salida = subprocess.run([sys.executable, '-m', 'postulador.mcp_server'], input=entrada.encode(), capture_output=True, cwd=RAIZ, check=True)
        respuestas = [json.loads(linea) for linea in salida.stdout.decode('utf-8').splitlines()]
        self.assertEqual([r['id'] for r in respuestas], [1, 2])
        self.assertEqual(respuestas[0]['result']['protocolVersion'], '2025-06-18')
        self.assertIn('cv_generar', [h['name'] for h in respuestas[1]['result']['tools']])

class EquipoTests(Base):
    def test_falla_cerrado(self):
        from postulador import equipo
        for contenido in (None, 'no es json', '[]', json.dumps({'nivel_maximo': 'libre'})):
            if contenido is None: archivo_equipo().unlink()
            else: archivo_equipo().write_text(contenido, encoding='utf-8')
            datos_equipo = equipo()
            self.assertEqual(datos_equipo['nivel_maximo'], 'solo_rellenar', contenido)
            self.assertTrue(datos_equipo['problema'], contenido)
            self.assertEqual(registro.nivel_de_url('https://x.example/'), 'solo_rellenar')
            self.assertTrue(arranque.diagnostico()['problemas'])

class NivelMaximoTests(Base):
    TOPE = 'solo_rellenar'

    def test_el_tope_manda(self):
        (Path(self.carpeta.name) / 'politicas.json').write_text(json.dumps({'empresa.example': 'enviar_solo'}), encoding='utf-8')
        self.assertEqual(registro.nivel_de_url('https://empresa.example/f'), 'solo_rellenar')
        self.assertEqual(registro.nivel_de_url('https://desconocido.example/f'), 'solo_rellenar')
        politica = registro.consultar_politica('empresa.example')
        self.assertEqual((politica['nivel'], politica['tope'], politica['configurado']), ('solo_rellenar', 'solo_rellenar', 'enviar_solo'))
        with self.assertRaises(ValueError): registro.fijar_politica('x.example', 'aprobar')
        self.assertEqual(registro.fijar_politica('x.example', 'solo_preparar')['nivel'], 'solo_preparar')
        self.assertEqual(registro.niveles_permitidos(), ['solo_rellenar', 'solo_preparar'])
        self.assertEqual(registro.ORDEN_NIVELES, ('solo_preparar', 'solo_rellenar', 'aprobar', 'enviar_solo'))

    def test_herramientas_ocultas_con_el_tope(self):
        nombres = {herramienta['name'] for herramienta in mcp_server._lista_herramientas()}
        self.assertFalse(nombres & set(mcp_server.OCULTAS_CON_TOPE))
        self.assertIn('diagnostico', nombres)
        resultado = mcp_server._llamar('plantilla_guardar', {'nombre': 'x', 'html': '<img src="file:///C:/x">'})
        self.assertTrue(resultado['isError'])
        self.assertFalse((Path(self.carpeta.name) / 'plantillas').exists())
        esquema = next(h for h in mcp_server._lista_herramientas() if h['name'] == 'postulacion_actualizar')['inputSchema']['properties']['estado']['enum']
        self.assertEqual(esquema, list(registro.ESTADOS_IA))
        self.tope('aprobar')
        self.assertIn('aprobacion_solicitar', {herramienta['name'] for herramienta in mcp_server._lista_herramientas()})

    def test_argumentos_fuera_del_esquema(self):
        creada = registro.registrar('QA', 'Acme', 'x', 'preparada')
        resultado = mcp_server._llamar('postulacion_actualizar', {'id': creada['id'], 'estado': 'descartada', 'actor': 'persona'})
        self.assertIn('argumento no permitido', resultado['content'][0]['text'])
        self.assertEqual(registro.obtener(creada['id'])['estado'], 'preparada')

class TransicionesTests(Base):
    TOPE = 'solo_rellenar'

    def ia(self, herramienta, **argumentos): return mcp_server._llamar(herramienta, argumentos)

    def test_la_ia_no_marca_envios_ni_respuestas(self):
        self.assertTrue(self.ia('postulacion_registrar', cargo='QA', empresa='A', sitio='x', estado='enviada')['isError'])
        creada = json.loads(self.ia('postulacion_registrar', cargo='QA', empresa='A', sitio='x', estado='preparada')['content'][0]['text'])
        for estado in ('enviada', 'avanzo', 'rechazada', 'rellenada', 'por_aprobar'):
            self.assertTrue(self.ia('postulacion_actualizar', id=creada['id'], estado=estado)['isError'], estado)
        self.assertFalse(self.ia('postulacion_actualizar', id=creada['id'], estado='incompleta').get('isError'))
        with self.assertRaises(ValueError): registro.actualizar(creada['id'], 'rellenada', actor='ia')
        with self.assertRaises(ValueError): registro.actualizar(creada['id'], 'rellenada', actor='puerta')
        with self.assertRaises(ValueError): registro.seguimiento_hecho(creada['id'], actor='ia')

    def test_reportada_no_cuenta_hasta_que_ella_confirma(self):
        creada = registro.registrar('Abogada', 'Firma', 'x', 'preparada')
        registro.actualizar(creada['id'], 'rellenada', actor='puerta')
        registro.actualizar(creada['id'], 'reportada', actor='ia')
        self.assertEqual(registro.analisis()['por_sitio'], [])
        self.assertEqual(registro.obtener(creada['id'])['seguir_el'], '')
        with self.assertRaises(ValueError): registro.accion_persona(creada['id'], 'avanzo')
        registro.accion_persona(creada['id'], 'la_envie')
        fila = registro.obtener(creada['id'])
        self.assertEqual(fila['estado'], 'enviada'); self.assertTrue(fila['seguir_el'])
        registro.accion_persona(creada['id'], 'avanzo')
        self.assertEqual(registro.analisis()['por_sitio'][0]['avances'], 1)

    def test_otras_acciones_y_olvidadas(self):
        primera = registro.registrar('A', 'Uno', 'x', 'preparada'); segunda = registro.registrar('B', 'Dos', 'x', 'preparada')
        registro.accion_persona(primera['id'], 'ya_estaba_enviada')
        self.assertEqual(registro.obtener(primera['id'])['estado'], 'enviada')
        self.assertEqual(actividad.recientes()[0]['accion'], 'incidente_envio')
        registro.actualizar(segunda['id'], 'rellenada', actor='puerta')
        self.assertEqual(registro.olvidadas(), [])
        with registro.closing(registro.conexion()) as base, base: base.execute("update postulaciones set actualizada='2020-01-01 00:00' where id=?", (segunda['id'],))
        self.assertEqual([fila['id'] for fila in registro.olvidadas()], [segunda['id']])
        registro.accion_persona(segunda['id'], 'corregir')
        self.assertEqual(registro.obtener(segunda['id'])['estado'], 'preparada')
        with self.assertRaises(ValueError): registro.accion_persona(segunda['id'], 'inventada')

    def test_el_autor_sigue_como_hoy(self):
        self.tope('aprobar')
        creada = registro.registrar('QA', 'Acme', 'torre', 'enviada', actor='ia')
        registro.actualizar(creada['id'], 'avanzo', actor='ia')
        self.assertIsNone(registro.candado())

class ComprobantesTests(Base):
    TOPE = 'solo_rellenar'

    def test_crea_en_una_transaccion_y_no_se_modifica(self):
        creada = registro.registrar('Abogada', 'Firma', 'x', 'preparada')
        resultado = comprobantes.crear(creada['id'], 'https://f.example/', '2026-01-01 10:00:00', [{'campo': 'a', 'valor': 'b'}], [], [], 'asesora', EditorCvTests.PNG, 2)
        self.assertEqual(registro.obtener(creada['id'])['estado'], 'rellenada')
        dato = comprobantes.leer(resultado['comprobante'])
        self.assertEqual((dato['imagen'], dato['cv'], dato['envios_bloqueados']), ('comprobantes/c%d.png' % resultado['comprobante'], 'asesora', 2))
        self.assertEqual(comprobantes.ruta_imagen(resultado['comprobante']).read_bytes(), EditorCvTests.PNG)
        import sqlite3
        with registro.closing(registro.conexion()) as base:
            with self.assertRaises(sqlite3.DatabaseError): base.execute("update comprobantes set campos='[]'")
            with self.assertRaises(sqlite3.DatabaseError): base.execute('delete from comprobantes')

    def test_si_falla_no_queda_nada(self):
        creada = registro.registrar('Abogada', 'Firma', 'x', 'preparada')
        registro.actualizar(creada['id'], 'descartada', actor='ia')
        with self.assertRaises(ValueError): comprobantes.crear(creada['id'], 'u', 'i', [], [], [], '', EditorCvTests.PNG, 0)
        self.assertFalse(list((Path(self.carpeta.name) / 'comprobantes').glob('*.png')))
        with self.assertRaises(ValueError): comprobantes.leer(1)

CAPTURA_FORMULARIO = """Page URL: https://empresa.example/form
- textbox "Nombre" [ref=e3]
- checkbox "Acepto el tratamiento de datos" [ref=e4]
- button "Siguiente" [ref=e1]
- button "Enviar solicitud" [ref=e2]"""

class ServicioFalso:
    """Playwright de mentira: responde ok y devuelve una imagen cuando se la piden."""
    sesion = 'x'
    def __init__(self): self.enviados = []
    def enviar(self, mensaje):
        self.enviados.append(mensaje['params']['name'])
        if mensaje['params']['name'] == 'browser_take_screenshot':
            import base64
            return {'jsonrpc': '2.0', 'id': mensaje['id'], 'result': {'content': [{'type': 'image', 'mimeType': 'image/png', 'data': base64.b64encode(EditorCvTests.PNG).decode()}]}}
        return {'jsonrpc': '2.0', 'id': mensaje['id'], 'result': {'content': [{'type': 'text', 'text': CAPTURA_FORMULARIO}]}}

def llamar_puerta(nueva, servicio, herramienta, **argumentos):
    return puerta.atender({'id': 1, 'method': 'tools/call', 'params': {'name': herramienta, 'arguments': argumentos}}, nueva, servicio)['result']

class BorradorYCandadoTests(Base):
    TOPE = 'solo_rellenar'

    def setUp(self):
        super().setUp()
        self.servicio, self.puerta = ServicioFalso(), puerta.Puerta()
        self.puerta.observar(CAPTURA_FORMULARIO); self.puerta.pestana_propia = True
        self.postulacion = registro.registrar('Abogada', 'Firma', 'empresa.example', 'preparada', url='https://empresa.example/form')['id']

    def llamar(self, herramienta, **argumentos): return llamar_puerta(self.puerta, self.servicio, herramienta, **argumentos)

    def test_anota_bloquea_botones_y_guarda_el_comprobante(self):
        self.assertTrue(self.llamar('formulario_listo', postulacion_id=self.postulacion).get('isError'))
        self.assertNotIn('isError', self.llamar('browser_type', target='e3', text='Ana'))
        self.assertNotIn('isError', self.llamar('browser_click', target='e4', element='casilla'))
        for herramienta, argumentos in (('browser_click', {'target': 'e1'}), ('browser_click', {'target': 'e2'}), ('browser_click', {'target': '#enviar'}),
                                        ('browser_press_key', {'key': 'Enter'}), ('browser_handle_dialog', {'accept': True})):
            self.assertIn('BLOQUEADO', self.llamar(herramienta, **argumentos)['content'][0]['text'], herramienta)
        self.puerta.url = 'https://otra.example/x'
        self.assertIn('formulario_listo', self.llamar('browser_type', target='e3', text='x')['content'][0]['text'])
        self.puerta.url = 'https://empresa.example/form'
        self.assertNotIn('isError', self.llamar('formulario_listo', postulacion_id=self.postulacion))
        dato = comprobantes.ultimo_de(self.postulacion)
        self.assertEqual(dato['campos'][0], {'campo': 'textbox Nombre', 'valor': 'Ana', 'hora': dato['campos'][0]['hora']})
        self.assertEqual(dato['clics'][0]['elemento'], 'checkbox Acepto el tratamiento de datos')
        self.assertEqual(dato['envios_bloqueados'], 5)
        self.assertTrue(dato['imagen'])
        self.assertEqual(registro.obtener(self.postulacion)['estado'], 'rellenada')
        self.assertTrue(self.llamar('formulario_listo', postulacion_id=self.postulacion).get('isError'))

    def test_etiqueta_que_no_esta_en_la_pagina(self):
        self.llamar('browser_type', target='e99', text='x', element='Campo raro')
        self.assertIn('etiqueta según la IA', self.puerta.borrador['campos'][0]['campo'])

    def test_candado_en_cualquier_pestana_y_puerta_nueva(self):
        self.llamar('browser_type', target='e3', text='Ana')
        self.llamar('formulario_listo', postulacion_id=self.postulacion)
        for nueva in (self.puerta, puerta.Puerta()):
            nueva.observar(CAPTURA_FORMULARIO); nueva.pestana_propia = True
            for herramienta, argumentos in (('browser_type', {'target': 'e3', 'text': 'x'}), ('browser_click', {'target': 'e4'}), ('browser_navigate', {'url': 'https://x.example/'}),
                                            ('browser_tabs', {'action': 'close'}), ('browser_tabs', {'action': 'select', 'index': 0}), ('browser_close', {}), ('browser_navigate_back', {}), ('browser_hover', {'target': 'e1'})):
                respuesta = llamar_puerta(nueva, self.servicio, herramienta, **argumentos)
                self.assertIn('espera que el usuario la envíe', respuesta['content'][0]['text'], herramienta)
            for herramienta, argumentos in (('browser_snapshot', {}), ('browser_take_screenshot', {}), ('browser_wait_for', {'time': 1}), ('browser_tabs', {'action': 'list'})):
                self.assertNotIn('isError', llamar_puerta(nueva, self.servicio, herramienta, **argumentos), herramienta)
        registro.accion_persona(self.postulacion, 'la_envie')
        self.assertNotIn('isError', self.llamar('browser_navigate', url='https://x.example/'))

    def test_con_la_base_caida_bloquea(self):
        from unittest import mock
        self.puerta.observar(CAPTURA_FORMULARIO)
        with mock.patch.object(registro, 'conexion', side_effect=OSError('sin base')):
            with self.assertRaises(OSError): puerta.atender({'id': 1, 'method': 'tools/call', 'params': {'name': 'browser_type', 'arguments': {'target': 'e3', 'text': 'x'}}}, self.puerta, self.servicio)
        self.assertEqual(self.servicio.enviados, [])

    def test_abandonar_cierra_el_borrador(self):
        self.llamar('browser_type', target='e3', text='Ana')
        self.llamar('formulario_abandonar')
        self.assertIsNone(self.puerta.borrador)
        self.assertNotIn('isError', self.llamar('browser_click', target='e1'))

    def test_paso_seguro_por_sitio(self):
        import re
        self.llamar('browser_type', target='e3', text='Ana')
        puerta.PASO_SEGURO_POR_SITIO['empresa.example'] = re.compile(r'\bsiguiente\b', re.I)
        self.addCleanup(puerta.PASO_SEGURO_POR_SITIO.pop, 'empresa.example')
        self.assertNotIn('isError', self.llamar('browser_click', target='e1'))
        self.assertIn('BLOQUEADO', self.llamar('browser_click', target='e2')['content'][0]['text'])

    def test_el_campo_de_archivo_se_puede_pulsar_pero_no_un_envio(self):
        self.llamar('browser_type', target='e3', text='Ana')
        self.puerta.observar('Page URL: https://empresa.example/form\n- button "Hoja de vida" [ref=e8]\n- button "Subir hoja de vida y postularme" [ref=e9]\n- button "Cargar" [ref=e10]')
        self.assertIsNone(self.puerta.decidir('browser_click', {'target': 'e8'}))
        self.assertIsNone(self.puerta.decidir('browser_click', {'target': 'e10'}))
        self.assertIn('BLOQUEADO', self.puerta.decidir('browser_click', {'target': 'e9'}))

    def test_la_produccion_no_abre_puertos_locales(self):
        self.assertTrue(puerta.url_prohibida('http://127.0.0.1:9000/'))

class CarrerasTests(Base):
    def test_paquete_de_derecho(self):
        paquete = carreras.cargar('derecho')
        self.assertEqual(set(paquete), {'id', 'nombre', 'titulo_cv', 'provisional', 'paginas_maximas', 'campos', 'tipos_documento'})
        self.assertEqual(carreras.paginas_maximas({'carrera': 'derecho'}), paquete['paginas_maximas'])
        self.assertEqual(carreras.paginas_maximas({}), 1)
        self.assertIn('cedula', carreras.sensibles(paquete))
        self.assertEqual(carreras.tipos_documento('derecho')[0]['clave'], 'mi_cv')
        for malo in ('../x', 'Derecho', 'no_existe'):
            with self.assertRaises((ValueError, FileNotFoundError)): carreras.cargar(malo)

ABOGADA = dict(json.loads(json.dumps(EJEMPLO)), carrera='derecho', campos_carrera={'tarjeta_profesional': '123456', 'areas_practica': 'Laboral', 'ciudad': 'Bogotá'})

class PerfilV1Tests(Base):
    TOPE = 'solo_rellenar'

    def test_opcionales_ids_y_sensibles(self):
        sin = {clave: valor for clave, valor in EJEMPLO.items() if clave not in ('publications', 'projects')}
        perfil.guardar(sin)
        self.assertEqual(perfil.leer()['publications'], [])
        self.assertEqual(perfil.leer()['education'][0]['id'], 'f1')
        perfil.guardar(dict(ABOGADA, campos_carrera=dict(ABOGADA['campos_carrera'], cedula='52.123.456')), por='persona')
        self.assertEqual(perfil.leer()['campos_carrera']['cedula'], '52.123.456')
        self.assertEqual(perfil.leer(para_ia=True)['campos_carrera']['cedula'], perfil.TAPADO)
        with self.assertRaises(PermissionError): perfil.guardar(dict(ABOGADA, campos_carrera=dict(ABOGADA['campos_carrera'], cedula='1')))
        perfil.guardar(perfil.leer(para_ia=True))
        self.assertEqual(perfil.leer()['campos_carrera']['cedula'], '52.123.456')
        with self.assertRaises(ValueError): perfil.guardar(dict(ABOGADA, campos_carrera={'inventado': 'x'}))

    def test_sello_de_revision(self):
        perfil.guardar(ABOGADA)
        self.assertFalse(perfil.sello_vigente())
        with self.assertRaises(PermissionError) as contexto: cv.generar('x', SELECCION, motor='html')
        self.assertIn('revisa tu perfil en el panel', str(contexto.exception))
        perfil.marcar_revisado()
        self.assertTrue(perfil.sello_vigente())
        self.assertTrue(perfil.ruta_revisado().is_file())
        cambiado = perfil.leer(); cambiado['headline'] = 'Abogada laboralista'
        perfil.guardar(cambiado)
        self.assertFalse(perfil.sello_vigente())
        self.assertEqual([c['campo'] for c in perfil.cambios()['cambios']], ['headline'])
        with self.assertRaises(PermissionError): cv.generar_carta('x', 'texto ' * 50)
        perfil.guardar(perfil.leer(), por='persona')
        self.assertFalse(perfil.sello_vigente())
        perfil.marcar_revisado()
        otro = perfil.leer(); otro['headline'] = 'Abogada'
        perfil.guardar(otro, por='persona')
        self.assertTrue(perfil.sello_vigente())

    def test_faltantes(self):
        self.assertTrue(perfil.faltantes()['sin_perfil'])
        perfil.guardar(dict(ABOGADA, campos_carrera={'tarjeta_profesional': '1'}))
        self.assertEqual([campo['clave'] for campo in perfil.faltantes()['carrera']], ['areas_practica', 'ciudad'])

class CvCarreraTests(Base):
    def test_seccion_de_carrera_escapada_y_sin_sensibles(self):
        abogada = dict(ABOGADA, campos_carrera=dict(ABOGADA['campos_carrera'], areas_practica='<img src=file:///C:/x>', cedula='52.123.456'))
        for diseno in ('columna', 'clasico', 'editorial'):
            contenido = cv.componer_html(SELECCION, abogada, cv._ruta_plantilla(diseno))
            self.assertIn('Datos profesionales', contenido, diseno)
            self.assertIn('&lt;img src=file:', contenido)
            self.assertNotIn('<img src=file:', contenido)
            self.assertNotIn('52.123.456', contenido)
        self.assertNotIn('Datos profesionales', cv.componer_html(SELECCION, EJEMPLO))

    @unittest.skipUnless(navegador.impresor(), 'requiere un navegador')
    def test_tope_de_paginas_del_paquete(self):
        largo = json.loads(json.dumps(ABOGADA))
        largo['experience'][0]['bullets'] = ['Texto de relleno para ocupar espacio en la hoja. ' * 6] * 13
        perfil.guardar(largo)
        seleccion = dict(SELECCION, bullets={'tienda': list(range(13))})
        resultado = cv.generar('dos_paginas', seleccion, motor='html')
        self.assertEqual(resultado['paginas'], 2)
        from unittest import mock
        with mock.patch.object(carreras, 'paginas_maximas', return_value=1), self.assertRaises(ValueError) as contexto:
            cv.generar('una_pagina', seleccion, motor='html')
        self.assertIn('el tope es 1', str(contexto.exception))
        self.assertFalse((Path(self.carpeta.name) / 'cv' / 'una_pagina').exists())

class DocumentosTests(Base):
    def setUp(self):
        super().setUp()
        self.arranque = Path(self.carpeta.name) / 'arranque'; (self.arranque / 'entrada').mkdir(parents=True)
        self.tope('solo_rellenar', self.arranque)

    def dejar(self, nombre, contenido, viejo=True):
        archivo = self.arranque / 'entrada' / nombre; archivo.write_bytes(contenido)
        if viejo: os.utime(archivo, (1_700_000_000, 1_700_000_000))
        return archivo

    def test_barre_copia_y_no_duplica(self):
        original = self.dejar('Cédula 52123456.pdf', b'%PDF-1 cedula')
        self.dejar('reciente.pdf', b'%PDF nuevo', viejo=False)
        self.assertEqual(documentos.barrer(), 1)
        self.assertTrue(original.is_file())
        self.dejar('copia.pdf', b'%PDF-1 cedula')
        self.assertEqual(documentos.barrer(), 0)
        self.assertEqual(documentos.listar_para_ia(), [])
        fila = documentos.listar_para_panel()[0]
        self.assertTrue(fila['archivo'].startswith('documentos/'))
        self.assertNotIn('52123456', fila['archivo'])
        documentos.clasificar(fila['id'], 'cedula', 'Mi cédula')
        para_ia = documentos.listar_para_ia()
        self.assertEqual(para_ia, [{'id': fila['id'], 'tipo': 'cedula', 'nombre': 'Mi cédula', 'puedes_leerlo': False}])
        with self.assertRaises(PermissionError): documentos.leer(fila['id'])
        with self.assertRaises(ValueError): documentos.clasificar(fila['id'], 'inventado', 'x')

    def test_mi_cv_se_lee_con_la_cedula_tapada(self):
        import zipfile
        docx = self.arranque / 'entrada' / 'CV.docx'
        with zipfile.ZipFile(docx, 'w') as paquete:
            paquete.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
                             '<w:p><w:r><w:t>Ana Abogada</w:t></w:r></w:p><w:p><w:r><w:t>C.C. 52.123.456 de Bogotá</w:t></w:r></w:p></w:body></w:document>')
        os.utime(docx, (1_700_000_000, 1_700_000_000))
        fila = documentos.listar_para_panel()[0]
        documentos.clasificar(fila['id'], 'mi_cv', 'Mi CV')
        texto = mcp_server._llamar('documento_leer', {'id': fila['id']})['content'][0]['text']
        self.assertIn('Ana Abogada', texto)
        self.assertNotIn('52.123.456', texto)
        self.assertIn('[número tapado]', texto)

    def test_sin_pdfminer_lo_explica(self):
        from unittest import mock
        self.dejar('cv.pdf', b'%PDF-1.4 algo')
        fila = documentos.listar_para_panel()[0]
        documentos.clasificar(fila['id'], 'mi_cv', 'Mi CV')
        with mock.patch.object(ats, 'extraer_pdf', return_value=None):
            self.assertIn('No puedo leer PDF en este equipo', documentos.leer(fila['id'])['aviso'])
        self.dejar('foto.jpg', b'\xff\xd8\xff foto')
        imagen = documentos.listar_para_panel()[0]
        documentos.clasificar(imagen['id'], 'otro', 'Foto', ia_puede_leer=True)
        self.assertIn('imagen', documentos.leer(imagen['id'])['aviso'])

    def test_sin_carpeta_de_arranque_no_barre(self):
        self.dejar('x.pdf', b'%PDF')
        self.tope('solo_rellenar')
        self.assertEqual(documentos.barrer(), 0)

class RepositorioTests(unittest.TestCase):
    def test_datos_privados_ignorados(self):
        self.assertIn('datos_usuario/', (RAIZ / '.gitignore').read_text(encoding='utf-8'))

if __name__ == '__main__': unittest.main()
