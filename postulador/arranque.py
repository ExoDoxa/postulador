"""Carpeta de arranque: lo que la persona abre en la app de Claude (modo Code) o de Codex para buscar empleo.

Separa el uso del código. En la carpeta de arranque la IA solo tiene las herramientas de Postulador y la puerta de
envío: no ejecuta comandos, no lee ni edita archivos, no lee la web y no usa otros navegadores ni el control del
equipo. El repositorio queda libre para programar. Todo se genera aquí para que los permisos no se desactualicen.

Los permisos solo rigen si la sesión empieza en esta carpeta: decirle a la IA «trabaja en tal carpeta» no basta.
"""
import html
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from . import NIVELES, RAIZ, DatosNoDisponibles, __version__, archivo_equipo, datos, equipo

# Herramientas propias del motor y servidores que se saltarían la puerta (nombres vistos el 10 nov 2026 en
# Claude Code 2.1.89 y en la app de escritorio). Read, Glob y Grep también: con ellas la IA leería entrada/ y los
# diplomas. Los conectores de la cuenta varían por persona: no basta con esto, se desactivan en claude.ai.
DENEGADAS = ('Bash', 'PowerShell', 'Edit', 'Write', 'Read', 'Glob', 'Grep', 'NotebookEdit', 'WebFetch', 'WebSearch', 'EnterWorktree',
             'CronCreate', 'RemoteTrigger', 'Workflow', 'Agent', 'Task', 'mcp__plugin_playwright_playwright', 'mcp__Claude_Browser',
             'mcp__claude-in-chrome', 'mcp__computer-use', 'mcp__terminal', 'mcp__remote-devices', 'mcp__claude_ai_TinyFish',
             'mcp__claude_ai_Gmail', 'mcp__claude_ai_Google_Drive', 'mcp__claude_ai_Google_Calendar')
INSTRUCCIONES = """# Postulador

Esta carpeta es para buscar empleo con Postulador. Para cualquier pedido usa la skill `postulador`: llama a la herramienta `guia_leer` del servidor `postulador` con el nombre `SKILL.md` y síguela.

- Al empezar cada sesión llama a la herramienta `diagnostico`. No busques ofertas ni rellenes nada si trae `problemas`, si falta el servidor `postulador` o la puerta (`playwright`), o si ves herramientas de navegador, terminal o control del equipo que no sean de esos dos servidores, incluida cualquier herramienta `mcp__claude_ai_*`. En ese caso dile al usuario, con palabras sencillas, que avise a quien le instaló Postulador.
- Solo usas las herramientas de los servidores `postulador` y `playwright` (la puerta de envío). Nunca uses otro navegador ni el control del equipo, aunque aparezcan: Claude_Browser, claude-in-chrome, computer-use, Playwright de plugins, TinyFish ni similares.
- Las herramientas `browser_*` de `playwright` tardan unos segundos en conectar. Si después de buscarlas un par de veces no aparecen, no busques ofertas ni postules: dile al usuario que cierre la sesión y abra una nueva en esta carpeta.
- No le propongas comandos de terminal al usuario. Si algo falla, explícalo en palabras sencillas y sugiérele avisar a quien le instaló Postulador.
- Los archivos que el usuario quiera darte (su CV, diplomas, certificados) los deja en la carpeta `entrada`. Tú no los abres: el código los guarda y él decide en el panel cuáles puedes leer.
- Para ver su tablero, el usuario usa el acceso directo «Panel de Postulador» del Escritorio.
"""
LEEME = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Cómo abrir Postulador</title>
<style>body{font:18px/1.6 Georgia,serif;max-width:720px;margin:40px auto;padding:0 20px;color:#1f1b16;background:#fbf7ee}
code{display:block;font:20px/1.4 Consolas,monospace;background:#fff;border:1px solid #cdbfa8;padding:12px;margin:8px 0;word-break:break-all}
img{max-width:100%;border:1px solid #cdbfa8}h1{font-weight:500}</style></head>
<body><h1>Cómo abrir Postulador con Claude</h1>
<p>En la app de Claude, pestaña <strong>Code</strong>, crea una sesión nueva y, cuando te pida la carpeta, elige esta:</p>
<code>{carpeta}</code>
<p>Si la sesión no empieza en esta carpeta, el asistente no tiene sus herramientas ni sus protecciones. Si dudas, cierra la sesión y abre otra eligiendo la carpeta.</p>
{imagen}
<p>Para ver tus postulaciones sin abrir Claude, usa el acceso directo <strong>Panel de Postulador</strong> del Escritorio.</p>
</body></html>
"""
IMAGEN_CARPETA = RAIZ / 'docs' / 'piloto' / 'elegir_carpeta.png'

def carpeta_por_defecto(): return Path.home() / 'Postulador'

def _comando(modulo, *extra):
    # Python con ruta absoluta: en otros equipos «python» puede ser el atajo de la Microsoft Store.
    # Sin -P a propósito: con -P, Claude Code 2.1.89 conectaba la puerta pero no mostraba sus herramientas (10 nov 2026).
    # Plantar un módulo falso en esta carpeta exige escribir archivos, y aquí la IA no puede.
    return [sys.executable, '-m', modulo, *extra]

def servidores():
    # Sin POSTULADOR_DATOS: los datos se ubican con el registro del equipo, así un cambio de carpeta (o la USB) no deja esta configuración vieja.
    entorno = {'PYTHONPATH': str(RAIZ)}
    return {nombre: {'command': comando[0], 'args': comando[1:], 'env': dict(entorno)}
            for nombre, comando in (('postulador', _comando('postulador.mcp_server', '--con-panel')), ('playwright', _comando('postulador.puerta')))}

def permisos_claude():
    return {'permissions': {'allow': ['mcp__postulador', 'mcp__playwright'], 'deny': list(DENEGADAS), 'disableBypassPermissionsMode': 'disable'},
            'enableAllProjectMcpServers': True, 'env': {'ENABLE_CLAUDEAI_MCP_SERVERS': 'false'}}

def _toml(texto): return "'" + texto + "'" if "'" not in texto and '\n' not in texto else json.dumps(texto)

def configuracion_codex():
    lineas = ['sandbox_mode = "read-only"', 'approval_policy = "never"']
    for nombre, servidor in servidores().items():
        lineas += ['', '[mcp_servers.%s]' % nombre, 'command = ' + _toml(servidor['command']),
                   'args = [%s]' % ', '.join(_toml(arg) for arg in servidor['args']), '', '[mcp_servers.%s.env]' % nombre]
        lineas += ['%s = %s' % (clave, _toml(valor)) for clave, valor in servidor['env'].items()]
    return '\n'.join(lineas) + '\n'

def _escribir_atomico(ruta, contenido):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(ruta.name + '.tmp')
    temporal.write_text(contenido, encoding='utf-8')
    os.replace(temporal, ruta)

def python_sin_ventana():
    """pythonw.exe junto al Python actual; si no está, python.exe con la ventana minimizada (estilo 7)."""
    ejecutable = Path(sys.executable)
    pythonw = ejecutable.with_name('pythonw.exe')
    return (str(pythonw), 1) if pythonw.is_file() else (str(ejecutable), 7)

SCRIPT_ACCESO = ("$e=[Environment]::GetFolderPath('Desktop'); $r=Join-Path $e $env:PD_NOMBRE; "
                 "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($r); $s.TargetPath=$env:PD_DESTINO; $s.Arguments=$env:PD_ARGS; "
                 "$s.WorkingDirectory=$env:PD_CARPETA; $s.WindowStyle=[int]$env:PD_ESTILO; $s.Description=$env:PD_DESCRIPCION; $s.Save(); Write-Output $r")

def acceso_directo(nombre, destino, argumentos='', carpeta_trabajo='', estilo=1, descripcion=''):
    """Crea un .lnk en el Escritorio real (puede estar dentro de OneDrive). Los valores van por variables de entorno: sin comillas que escapar."""
    entorno = dict(os.environ, PD_NOMBRE=nombre, PD_DESTINO=str(destino), PD_ARGS=argumentos, PD_CARPETA=str(carpeta_trabajo), PD_ESTILO=str(estilo), PD_DESCRIPCION=descripcion)
    salida = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', SCRIPT_ACCESO], env=entorno, capture_output=True, text=True, timeout=60, check=True)
    return salida.stdout.strip()

def _accesos(destino):
    programa, estilo = python_sin_ventana()
    creados = [acceso_directo('Panel de Postulador.lnk', programa, '-m postulador panel --abrir', RAIZ, estilo, 'Abre tu tablero de postulaciones')]
    creados.append(acceso_directo('Cómo abrir Postulador con Claude.lnk', destino / 'LEEME.html', '', destino, 1, 'Qué carpeta elegir en la app de Claude'))
    return creados

def _sellar_perfiles():
    """Migración única: el perfil que ya existía (el del autor) queda como revisado."""
    from . import perfil
    sellados = []
    try: carpeta = datos()
    except DatosNoDisponibles: return sellados
    for archivo in sorted(carpeta.glob('perfil*.json')):
        idioma = archivo.stem.split('_')[1] if '_' in archivo.stem else 'es'
        try:
            contenido = json.loads(archivo.read_text(encoding='utf-8'))
            if 'schema_version' in contenido: continue
            perfil.marcar_revisado(idioma, migracion=True)
            sellados.append(archivo.name)
        except (OSError, ValueError): continue
    return sellados

def crear(carpeta=None, nivel_maximo='solo_rellenar', accesos=True):
    """Crea o actualiza la carpeta de arranque y equipo.json. No toca `entrada` ni nada que la persona haya dejado ahí."""
    if nivel_maximo not in NIVELES: raise ValueError('Nivel máximo inválido; usa: ' + ', '.join(NIVELES))
    destino = Path(carpeta or carpeta_por_defecto()).resolve()
    if destino == RAIZ.resolve() or destino.is_relative_to(RAIZ.resolve()) or RAIZ.resolve().is_relative_to(destino):
        raise ValueError('La carpeta de arranque debe estar fuera del código de Postulador.')
    imagen = ''
    if IMAGEN_CARPETA.is_file():
        (destino).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(IMAGEN_CARPETA, destino / 'elegir_carpeta.png')
        imagen = '<p><img src="elegir_carpeta.png" alt="Dónde se elige la carpeta al crear la sesión"></p>'
    archivos = {'.mcp.json': json.dumps({'mcpServers': servidores()}, ensure_ascii=False, indent=2) + '\n',
                '.claude/settings.json': json.dumps(permisos_claude(), ensure_ascii=False, indent=2) + '\n',
                '.codex/config.toml': configuracion_codex(), 'CLAUDE.md': INSTRUCCIONES, 'AGENTS.md': INSTRUCCIONES,
                'LEEME.html': LEEME.replace('{carpeta}', html.escape(str(destino))).replace('{imagen}', imagen)}
    for nombre, contenido in archivos.items():
        ruta = destino / nombre
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(contenido, encoding='utf-8')
    for carpeta_skill in ('.claude/skills/postulador', '.agents/skills/postulador'):
        (destino / carpeta_skill).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RAIZ / '.claude' / 'skills' / 'postulador' / 'SKILL.md', destino / carpeta_skill / 'SKILL.md')
    (destino / 'entrada').mkdir(exist_ok=True)
    _escribir_atomico(archivo_equipo(), json.dumps({'version': 1, 'nivel_maximo': nivel_maximo, 'arranque': str(destino)}, ensure_ascii=False, indent=2) + '\n')
    resultado = {'carpeta': str(destino), 'nivel_maximo': nivel_maximo, 'equipo': str(archivo_equipo()),
                 'abrir': 'En la app de Claude, modo Code, crea una sesión nueva eligiendo esta carpeta. Los permisos solo rigen si la sesión empieza aquí.'}
    sellados = _sellar_perfiles()
    if sellados: resultado['perfiles_sellados'] = sellados
    if accesos and os.name == 'nt':
        try: resultado['accesos_directos'] = _accesos(destino)
        except (OSError, subprocess.SubprocessError) as error: resultado['accesos_directos_error'] = str(error)
    return resultado

def _deny_de(carpeta):
    try: return json.loads((carpeta / '.claude' / 'settings.json').read_text(encoding='utf-8'))['permissions']['deny']
    except (OSError, ValueError, KeyError, TypeError): return None

def diagnostico():
    """Lo que el código puede comprobar sin depender de lo que diga la IA. `problemas` vacío = todo en orden."""
    datos_equipo = equipo()
    problemas = [datos_equipo['problema']] if datos_equipo['problema'] else []
    tope = datos_equipo['nivel_maximo']
    estricto = NIVELES.index(tope) >= NIVELES.index('solo_rellenar')
    carpeta = Path(datos_equipo['arranque']) if datos_equipo['arranque'] else None
    try:
        ruta_datos = datos()
        estado_datos = {'ruta': str(ruta_datos), 'disponible': True}
    except DatosNoDisponibles as error:
        estado_datos = {'ruta': None, 'disponible': False}
        problemas.append(str(error))
    deny = _deny_de(carpeta) if carpeta else None
    permisos_al_dia = deny is not None and set(deny) == set(DENEGADAS)
    if estricto:
        if carpeta is None or not carpeta.is_dir(): problemas.append('No encuentro la carpeta de arranque de este equipo: hay que volver a ejecutar «python -m postulador arranque».')
        elif not permisos_al_dia: problemas.append('Los permisos de la carpeta de arranque no están al día: hay que volver a ejecutar «python -m postulador arranque».')
    return {'carpeta_arranque': str(carpeta) if carpeta else None, 'carpeta_de_la_sesion': str(Path.cwd()), 'python': sys.executable,
            'datos': estado_datos, 'version': __version__, 'nivel_maximo': tope, 'equipo_legible': datos_equipo['problema'] is None,
            'permisos_al_dia': permisos_al_dia, 'problemas': problemas}
