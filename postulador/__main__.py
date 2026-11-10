"""Comandos: iniciar, doctor, conectar, navegador, abrir, ejecutar, migrar, importar-historial, reporte, panel, aprobar, rechazar, programar y vscode."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from . import RAIZ, DatosNoDisponibles, NIVELES, aprobaciones, arranque, datos, navegador, panel, registro, ubicacion

HERRAMIENTAS_CLAUDE = 'mcp__postulador,mcp__playwright'
TAREA_PROGRAMADA = 'Postulador'
INSTRUCCION = 'Antes de actuar, llama a guia_leer con nombre SKILL.md y síguela. Usa contexto_usuario para conocer al usuario. Tarea: '

def programa(nombre):
    ruta = shutil.which(nombre)
    if not ruta: sys.exit('No encontré %s. Instálalo y vuelve a intentar.' % nombre)
    return ruta

def entorno(credencial='suscripcion'):
    """Sin estas variables cada CLI usa el inicio de sesión del usuario y no factura por API."""
    if credencial == 'api': return dict(os.environ)
    return {clave: valor for clave, valor in os.environ.items() if clave not in ('ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'CODEX_API_KEY')}

def comando_claude():
    return [programa('claude'), '-p', '--mcp-config', str(RAIZ / '.mcp.json'), '--strict-mcp-config', '--allowedTools=' + HERRAMIENTAS_CLAUDE, '--output-format', 'stream-json', '--verbose']

def comando_codex():
    python = json.dumps(sys.executable)
    ajustes = ['mcp_servers.postulador.command=' + python,
               'mcp_servers.postulador.args=["-m","postulador.mcp_server","--con-panel"]',
               'mcp_servers.playwright.command=' + python,
               'mcp_servers.playwright.args=["-m","postulador.puerta"]']
    comando = [programa('codex'), 'exec', '--skip-git-repo-check', '--sandbox', 'read-only', '-C', str(RAIZ)]
    for ajuste in ajustes: comando += ['-c', ajuste]
    return comando + ['-']

def progreso(linea):
    """Traduce los eventos de Claude a una línea legible; lo demás se ignora."""
    try: evento = json.loads(linea)
    except ValueError: return linea.rstrip()
    if evento.get('type') == 'assistant':
        partes = [bloque for bloque in evento['message'].get('content', []) if bloque.get('type') == 'tool_use']
        return '\n'.join('→ ' + bloque['name'].replace('mcp__postulador__', '').replace('mcp__playwright__', '') for bloque in partes) or None
    if evento.get('type') == 'result': return evento.get('result') or 'Terminó con error: ' + str(evento.get('subtype'))
    return None

def ejecutar(motor, tarea, credencial='suscripcion'):
    navegador.asegurar_mcp()
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    comando = comando_claude() if motor == 'claude' else comando_codex()
    proceso = subprocess.Popen(comando, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=RAIZ, env=entorno(credencial))
    proceso.stdin.write((INSTRUCCION + tarea).encode('utf-8')); proceso.stdin.close()
    for linea in proceso.stdout:
        texto = linea.decode('utf-8', 'replace')
        salida = progreso(texto) if motor == 'claude' else texto.rstrip()
        if salida: print(salida)
    return proceso.wait()

def programar(hora, tarea, motor, quitar):
    """Tarea diaria del Programador de tareas de Windows, a nombre del usuario."""
    if os.name != 'nt': sys.exit('En Mac y Linux usa cron con: python -m postulador ejecutar "tarea"')
    if quitar: sys.exit(subprocess.call(['schtasks', '/Delete', '/TN', TAREA_PROGRAMADA, '/F']))
    if not tarea: sys.exit('Indica la tarea, por ejemplo: programar "Revisa novedades" --hora 08:00')
    # schtasks limita /TR a 261 caracteres: la orden completa vive en un archivo.
    arranque = datos() / 'programada.cmd'
    arranque.write_text('@cd /d "%s"\n@"%s" -m postulador ejecutar "%s" --motor %s >> "%s" 2>&1\n' % (RAIZ, sys.executable, re.sub(r'["%&|<>^]', '', tarea), motor, datos() / 'programada.log'), encoding='utf-8')
    sys.exit(subprocess.call(['schtasks', '/Create', '/F', '/SC', 'DAILY', '/ST', hora, '/TN', TAREA_PROGRAMADA, '/TR', '"%s"' % arranque]))

def iniciar():
    datos().mkdir(parents=True, exist_ok=True)
    for carpeta in ('cv', 'plantillas', 'historial', 'respaldos'): (datos() / carpeta).mkdir(exist_ok=True)
    notas = datos() / 'notas.md'
    if not notas.exists(): notas.write_text('# Notas personales\n', encoding='utf-8')
    print('Datos privados en', datos())
    print('Siguiente: python -m postulador conectar claude   (o codex)')

def conectar(motor):
    comando = [programa('claude'), 'auth', 'login'] if motor == 'claude' else [programa('codex'), 'login']
    sys.exit(subprocess.call(comando, env=entorno()))

def doctor():
    def estado(comando):
        try:
            salida = subprocess.run(comando, capture_output=True, text=True, encoding='utf-8', timeout=30, env=entorno())
            return (salida.stdout + salida.stderr).strip()
        except (OSError, subprocess.TimeoutExpired) as error:
            return 'no disponible: %s' % error
    try: print('Datos:', datos(), '(perfil listo)' if (datos() / 'perfil.json').is_file() else '(sin perfil)')
    except DatosNoDisponibles as error: print('Datos:', error)
    print('Navegador:', navegador.ejecutable() or 'no encontrado', '| activo:', navegador.activo() or 'no', '| PDF:', navegador.impresor() or 'no encontrado')
    print('Node (npx):', shutil.which('npx') or 'no encontrado')
    if shutil.which('claude'):
        print('Claude:', 'con sesión' if '"loggedIn": true' in estado([shutil.which('claude'), 'auth', 'status']) else 'sin sesión')
    else: print('Claude: no instalado')
    if shutil.which('codex'): print('Codex:', estado([shutil.which('codex'), 'login', 'status']))
    else: print('Codex: no instalado')
    print('Diagnóstico:', json.dumps(arranque.diagnostico(), ensure_ascii=False, indent=2))

def migrar(origen, perfil_navegador=''):
    """Copia los datos de un proyecto anterior con perfil.json, plantillas y registros."""
    origen = Path(origen)
    iniciar()
    copias = {'perfil.json': 'perfil.json', 'perfil_en.json': 'perfil_en.json', 'plantilla_CV.docx': 'plantillas/plantilla_CV.docx',
              'plantilla_CV_en.docx': 'plantillas/plantilla_CV_en.docx', 'REGISTRO_POSTULACIONES.md': 'historial/REGISTRO_POSTULACIONES.md',
              'EVALUACIONES.md': 'historial/EVALUACIONES.md', 'CUENTAS_CREADAS.md': 'historial/CUENTAS_CREADAS.md', 'tableros.json': 'tableros.json'}
    for desde, hasta in copias.items():
        if (origen / desde).is_file(): shutil.copy2(origen / desde, datos() / hasta); print('Copiado', desde)
    if (origen / 'salidas').is_dir():
        shutil.copytree(origen / 'salidas', datos() / 'cv', dirs_exist_ok=True); print('Copiado salidas/')
    if (datos() / 'historial' / 'REGISTRO_POSTULACIONES.md').is_file(): print(registro.importar_historial())
    if perfil_navegador:
        navegador.guardar_configuracion(perfil_navegador=perfil_navegador)

MANIFIESTO = """<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata><Identity Language="en-US" Id="panel" Version="0.1.0" Publisher="postulador"/><DisplayName>Postulador</DisplayName><Description>Panel de Postulador</Description></Metadata>
  <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>
  <Dependencies/>
  <Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets>
</PackageManifest>
"""
TIPOS = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="js" ContentType="application/javascript"/><Default Extension="vsixmanifest" ContentType="text/xml"/></Types>
"""

def instalar_vscode():
    """Empaqueta la extensión local como VSIX y la instala en el VS Code del usuario."""
    with tempfile.TemporaryDirectory(prefix='postulador-') as temporal:
        paquete = Path(temporal) / 'postulador.vsix'
        with zipfile.ZipFile(paquete, 'w', zipfile.ZIP_DEFLATED) as archivo:
            archivo.writestr('extension.vsixmanifest', MANIFIESTO)
            archivo.writestr('[Content_Types].xml', TIPOS)
            for nombre in ('package.json', 'extension.js'): archivo.write(RAIZ / 'vscode' / nombre, 'extension/' + nombre)
        sys.exit(subprocess.call([programa('code'), '--install-extension', str(paquete), '--force']))

def reporte():
    resultado = registro.analisis()
    print('Postulaciones registradas:', resultado['total'])
    print('Embudo:', ', '.join('%s %d' % par for par in sorted(resultado['embudo'].items(), key=lambda par: -par[1])))
    if resultado['mejora_ats_promedio'] is not None:
        print('Mejora ATS promedio al adaptar: %+.1f puntos en %d postulaciones' % (resultado['mejora_ats_promedio'], resultado['evaluadas']))
    for titulo, clave in (('Por sitio', 'por_sitio'), ('Por CV', 'por_cv'), ('Por idoneidad', 'por_idoneidad')):
        print('\n' + titulo + ':')
        for fila in resultado[clave][:10]:
            print('  %-28s %3d enviadas | respuesta %3d%% | avance %3d%%' % (fila['grupo'][:28], fila['enviadas'], fila['tasa_respuesta'], fila['tasa_avance']))
    if resultado['motivos']:
        print('\nMotivos de rechazo:')
        for motivo, cantidad in resultado['motivos']: print('  %d × %s' % (cantidad, motivo))
    print('\nSeguimientos pendientes:', resultado['seguimientos_pendientes'])
    for fila in registro.seguimientos_pendientes():
        print('  #%d %s · %s (enviada %s)' % (fila['id'], fila['cargo'][:40], fila['empresa'][:24], fila['enviada_el']))

def main():
    analizador = argparse.ArgumentParser(prog='postulador', description=__doc__)
    comandos = analizador.add_subparsers(dest='comando', required=True)
    comandos.add_parser('iniciar'); comandos.add_parser('doctor')
    del_panel = comandos.add_parser('panel'); del_panel.add_argument('--puerto', type=int, default=panel.PUERTO); del_panel.add_argument('--abrir', action='store_true')
    for nombre in ('aprobar', 'rechazar'): comandos.add_parser(nombre).add_argument('id', type=int)
    programacion = comandos.add_parser('programar'); programacion.add_argument('tarea', nargs='?', default=''); programacion.add_argument('--hora', default='08:00'); programacion.add_argument('--motor', choices=('claude', 'codex'), default='claude'); programacion.add_argument('--quitar', action='store_true')
    comandos.add_parser('vscode'); comandos.add_parser('abrir'); comandos.add_parser('reporte'); comandos.add_parser('importar-historial').add_argument('ruta', nargs='?')
    comandos.add_parser('conectar').add_argument('motor', choices=('claude', 'codex'))
    ejecucion = comandos.add_parser('ejecutar'); ejecucion.add_argument('tarea'); ejecucion.add_argument('--motor', choices=('claude', 'codex'), default='claude'); ejecucion.add_argument('--credencial', choices=('suscripcion', 'api'), default='suscripcion')
    comandos.add_parser('navegador').add_argument('elegido', nargs='?')
    del_arranque = comandos.add_parser('arranque'); del_arranque.add_argument('--carpeta', default='')
    del_arranque.add_argument('--nivel-maximo', choices=NIVELES, default='solo_rellenar', help='tope de autonomía del equipo; solo_rellenar para otras personas')
    comandos.add_parser('datos').add_argument('--mover', default='', metavar='CARPETA')
    migracion = comandos.add_parser('migrar'); migracion.add_argument('origen'); migracion.add_argument('--perfil-navegador', default='')
    args = analizador.parse_args()
    if args.comando == 'iniciar': iniciar()
    elif args.comando == 'doctor': doctor()
    elif args.comando == 'reporte': reporte()
    elif args.comando == 'vscode': instalar_vscode()
    elif args.comando == 'panel': panel.main(args.puerto, args.abrir)
    elif args.comando in ('aprobar', 'rechazar'): print(aprobaciones.resolver(args.id, args.comando == 'aprobar'))
    elif args.comando == 'programar': programar(args.hora, args.tarea, args.motor, args.quitar)
    elif args.comando == 'importar-historial': print(registro.importar_historial(args.ruta))
    elif args.comando == 'abrir': print(json.dumps(navegador.asegurar_mcp(), ensure_ascii=False))
    elif args.comando == 'conectar': conectar(args.motor)
    elif args.comando == 'navegador':
        print(json.dumps(navegador.elegir(args.elegido) if args.elegido else {'elegido': navegador.configuracion().get('navegador'), 'disponibles': navegador.disponibles()}, ensure_ascii=False, indent=2))
    elif args.comando == 'migrar': migrar(args.origen, args.perfil_navegador)
    elif args.comando == 'datos': print(json.dumps(ubicacion.mover(args.mover) if args.mover else ubicacion.donde(), ensure_ascii=False, indent=2))
    elif args.comando == 'arranque': print(json.dumps(arranque.crear(args.carpeta or None, args.nivel_maximo), ensure_ascii=False, indent=2))
    else: sys.exit(ejecutar(args.motor, args.tarea, args.credencial))

if __name__ == '__main__': main()
