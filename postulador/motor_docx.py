"""CV en DOCX: rellena una plantilla etiquetada desde el perfil y la convierte con Word o LibreOffice."""
import copy
import os
import re
import shutil
import subprocess
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

# Textos de encabezado con que se localizan las secciones de la plantilla en cada idioma.
LANGUAGES = {
    'es': {'skills': 'HABILIDADES', 'languages': 'IDIOMAS', 'tools': 'HERRAMIENTAS',
           'sections': (('education', 'FORMACIÓN ACADÉMICA', 'EXPERIENCIA'), ('experiences', 'EXPERIENCIA', 'INVESTIGACIÓN'), ('publications', 'INVESTIGACIÓN', 'PROYECTOS'), ('projects', 'PROYECTOS', 'INTERESES'))},
    'en': {'skills': 'SKILLS', 'languages': 'LANGUAGES', 'tools': 'TOOLS',
           'sections': (('education', 'EDUCATION', 'EXPERIENCE'), ('experiences', 'EXPERIENCE', 'RESEARCH'), ('publications', 'RESEARCH', 'PROJECTS'), ('projects', 'PROJECTS', 'INTERESTS'))},
}
TOOLS_PER_LINE, MAX_TOOLS = 3, 6
WNS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'
LIMITS = {'experiences': (2, 5), 'publications': (1, 3), 'projects': (1, 3), 'skills': (3, 5)}
SOURCES = {'experiences': 'experience', 'publications': 'publications', 'projects': 'projects'}

# Medidas de la plantilla en twips (1/20 pt): interlineados exactos de cada tipo de párrafo.
TITLE, META, BULLET, PAD = 226, 204, 208, 40
GAP, GAP_LAST = 180, 140
COLUMN_PT = 375
BULLET_INDENT = 154
# La plantilla original llena la página exacta: su propio contenido es el tope de cada columna
# (medido renderizando con Word; una línea más ya desplaza la ilustración del pie).
CAPACITY = 9370
SUMMARY_CHARS, SUMMARY_LINE, SKILL_LINE = 42, 188, 246
SIDEBAR_CAPACITY = 6 * SUMMARY_LINE + 5 * SKILL_LINE

def w(tag):
    return '{%s}%s' % (WNS, tag)

# Anchos aproximados de Arial (milésimas de em) para prever saltos de línea sin renderizar.
_WIDTHS = {}
for _width, _chars in ((222, "ijl'"), (278, ' .,:;!|/ftI'), (333, 'r-()·"“”'), (350, '•'), (500, 'cksvxyzJ'),
                       (611, 'FTZ'), (667, 'ABEKPSVXY&'), (722, 'CDHNRUw'), (778, 'GOQ'), (833, 'mM'), (944, 'W'), (1000, '—')):
    for _char in _chars:
        _WIDTHS[_char] = _width

def text_width(text, size, bold=False):
    plain = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    return sum(_WIDTHS.get(c, 556) for c in plain) * size / 1000 * (1.07 if bold else 1)

def line_count(text, size, bold=False, width=COLUMN_PT):
    lines, current = 1, ''
    for word in text.split(' '):
        candidate = (current + ' ' + word) if current else word
        if current and text_width(candidate, size, bold) > width * .97:
            lines += 1; current = word
        else:
            current = candidate
    return lines

def chosen(selection, profile, key):
    """Entradas elegidas en el orden del perfil (cronológico), no en el de prioridad."""
    return [item for item in profile[SOURCES[key]] if item['id'] in selection[key]]

def bullets_for(selection, item):
    indexes = selection.get('bullets', {}).get(item['id'], item.get('cv_bullets', list(range(len(item['bullets'])))))
    return [item['bullets'][index] for index in indexes]

def entries(selection, profile):
    """Texto final de cada sección: listas de (título, línea secundaria, viñetas)."""
    line = lambda item: item['organization'] + '  |  ' + item['date']
    return {
        'education': [(item['title'], line(item), []) for item in profile['education']],
        'experiences': [(item['title'], line(item), bullets_for(selection, item)) for item in chosen(selection, profile, 'experiences')],
        'publications': [(item['cv_title'], item['cv_citation'], []) for item in chosen(selection, profile, 'publications')],
        'projects': [(item['cv_title'], item['cv_description'], []) for item in chosen(selection, profile, 'projects')],
    }

def overflow(selection, profile):
    """Twips que sobran (>0) respecto de una página; es una estimación, el render es la medida real."""
    used = 0
    for key, items in entries(selection, profile).items():
        for index, (title, meta, bullets) in enumerate(items):
            used += line_count(title, 9.5, True) * TITLE + PAD + line_count(meta, 8.5) * META + PAD
            used += sum(line_count('•  ' + text, 8.5, width=COLUMN_PT - BULLET_INDENT / 20) for text in bullets) * BULLET
            used += GAP if key == 'experiences' and index < len(items) - 1 else GAP_LAST
    return used - CAPACITY

def summary_lines(text):
    lines, used = 1, 0
    for word in text.split():
        if used and used + 1 + len(word) > SUMMARY_CHARS:
            lines += 1; used = len(word)
        else:
            used += len(word) + bool(used)
    return lines

def sidebar_overflow(selection):
    """La columna lateral crece con el resumen y las habilidades; un resumen largo admite menos habilidades."""
    return summary_lines(selection['summary']) * SUMMARY_LINE + len(selection['skills']) * SKILL_LINE - SIDEBAR_CAPACITY

def validate(selection, profile):
    if selection.get('summary') not in profile['cv_summaries'].values():
        raise ValueError('Resumen no verificado')
    for key, (minimum, maximum) in LIMITS.items():
        values = selection.get(key)
        allowed = profile['skills'] if key == 'skills' else {item['id'] for item in profile[SOURCES[key]]}
        if not isinstance(values, list) or not minimum <= len(values) <= maximum or len(values) != len(set(values)) or any(value not in allowed for value in values):
            raise ValueError(key + ' inválido')
    chosen_bullets = selection.get('bullets', {})
    if not isinstance(chosen_bullets, dict) or any(key not in selection['experiences'] for key in chosen_bullets):
        raise ValueError('bullets inválido')
    tools = selection.get('tools', [])
    if not isinstance(tools, list) or len(tools) > MAX_TOOLS or len(tools) != len(set(tools)) or any(tool not in profile.get('cv_tool_labels', []) for tool in tools):
        raise ValueError('tools inválido')
    pools = {item['id']: len(item['bullets']) for item in profile['experience']}
    for key, indexes in chosen_bullets.items():
        if not isinstance(indexes, list) or not 1 <= len(indexes) <= 3 or len(indexes) != len(set(indexes)) or any(not isinstance(i, int) or isinstance(i, bool) or not 0 <= i < pools[key] for i in indexes):
            raise ValueError('bullets inválido')
    if sidebar_overflow(selection) > 0:
        raise ValueError('La columna lateral excede la página: usa un resumen más corto o menos habilidades.')
    extra = overflow(selection, profile)
    if extra > 0:
        raise ValueError('El contenido excede una página por unas %d líneas; quita viñetas, proyectos, publicaciones o experiencias.' % -(-extra // BULLET))
    return selection

def fit(selection, profile):
    """Recorta lo menos prioritario (lo último de cada lista) hasta que la estimación quepa."""
    selection = copy.deepcopy(selection)
    by_id = {item['id']: item for item in profile['experience']}
    while sidebar_overflow(selection) > 0:
        if len(selection['skills']) <= LIMITS['skills'][0]: raise ValueError('El resumen no cabe en la columna lateral.')
        selection['skills'].pop()
    while overflow(selection, profile) > 0:
        counts = {key: len(bullets_for(selection, by_id[key])) for key in selection['experiences']}
        longest = max(reversed(selection['experiences']), key=counts.get)
        if counts[longest] > 1:
            current = selection.setdefault('bullets', {}).get(longest, by_id[longest].get('cv_bullets', list(range(counts[longest]))))
            selection['bullets'][longest] = current[:-1]
        elif len(selection['projects']) > LIMITS['projects'][0]: selection['projects'].pop()
        elif len(selection['publications']) > LIMITS['publications'][0]: selection['publications'].pop()
        elif len(selection['experiences']) > LIMITS['experiences'][0]:
            selection.get('bullets', {}).pop(selection['experiences'].pop(), None)
        else: raise ValueError('El contenido mínimo no cabe en una página.')
    return selection

def para_text(paragraph):
    return ''.join(node.text or '' for node in paragraph.iter(w('t')))

def fill(prototype, text):
    """Copia un párrafo de la plantilla conservando su formato y deja un único run con el texto."""
    paragraph = copy.deepcopy(prototype)
    keep = next(run for run in paragraph.findall(w('r')) if run.find(w('t')) is not None)
    for child in list(paragraph):
        if child is not keep and child.tag != w('pPr'): paragraph.remove(child)
    for child in list(keep):
        if child.tag != w('rPr'): keep.remove(child)
    for index, line in enumerate(text.split('\n')):
        if index: ET.SubElement(keep, w('br'))
        node = ET.SubElement(keep, w('t')); node.text = line; node.set(XML_SPACE, 'preserve')
    return paragraph

def heading_index(children, marker):
    for index, child in enumerate(children):
        if child.tag == w('p') and marker in para_text(child) and child.find(w('pPr') + '/' + w('pBdr')) is not None:
            return index
    raise ValueError('La plantilla no contiene la sección ' + marker + '.')

def replace_block(cell, start, end, paragraphs):
    children = list(cell)
    for child in children[start:end]: cell.remove(child)
    for offset, paragraph in enumerate(paragraphs): cell.insert(start + offset, paragraph)

def rebuild_section(cell, marker, next_marker, items):
    children = list(cell)
    start, end = heading_index(children, marker) + 1, heading_index(children, next_marker)
    block = children[start:end]
    filled = [p for p in block if para_text(p).strip()]
    empty = [p for p in block if not para_text(p).strip()]
    title, meta = filled[0], filled[1]
    bullet = next((p for p in filled if para_text(p).lstrip().startswith('•')), None)
    if bullet is not None:
        # Sangría francesa para que una viñeta de dos líneas quede alineada con su texto.
        bullet = copy.deepcopy(bullet)
        ET.SubElement(bullet.find(w('pPr')), w('ind'), {w('left'): str(BULLET_INDENT), w('hanging'): str(BULLET_INDENT)})
    paragraphs = []
    for index, (heading, line, bullets) in enumerate(items):
        paragraphs += [fill(title, heading), fill(meta, line)] + [fill(bullet, '•  ' + text) for text in bullets]
        paragraphs.append(copy.deepcopy(empty[-1] if index == len(items) - 1 else empty[0]))
    replace_block(cell, start, end, paragraphs)

def rebuild_sidebar(cell, selection, profile, labels):
    children = list(cell)
    if selection.get('tools'):
        # La línea de herramientas es fija en la plantilla; solo se reemplaza cuando la selección la define.
        tools_at = heading_index(children, labels['tools']) + 1
        names = [tool.upper() for tool in selection['tools']]
        lines = ['  ·  '.join(names[index:index + TOOLS_PER_LINE]) for index in range(0, len(names), TOOLS_PER_LINE)]
        replace_block(cell, tools_at, tools_at + 1, [fill(children[tools_at], '\n'.join(lines))])
    skills_at, languages_at = heading_index(children, labels['skills']), heading_index(children, labels['languages'])
    replace_block(cell, skills_at + 1, languages_at, [fill(children[skills_at + 1], skill) for skill in selection['skills']])
    # Antes de HABILIDADES: foto, nombre, titular, resumen y líneas de contacto.
    texted = [index for index in range(skills_at) if para_text(children[index]).strip()]
    summary_at, contact_at = texted[2], texted[3]
    replace_block(cell, contact_at, skills_at, [fill(children[contact_at], line) for line in profile['contact']])
    replace_block(cell, summary_at, summary_at + 1, [fill(children[summary_at], selection['summary'])])

def write_docx(selection, path, profile, template, lang='es'):
    validate(selection, profile)
    labels = LANGUAGES[lang]
    with zipfile.ZipFile(template) as source:
        original = source.read('word/document.xml')
        # ElementTree descarta los prefijos sin uso que mc:Ignorable necesita: se conserva la etiqueta raíz
        # original y se le suman los espacios de nombres que ElementTree sube desde elementos internos.
        root_tag = re.search(rb'<w:document\b[^>]*>', original).group()
        for prefix, uri in re.findall(rb'xmlns:(\w+)="([^"]+)"', original):
            ET.register_namespace(prefix.decode(), uri.decode())
        document = ET.fromstring(original)
        left, right = document.find(w('body') + '/' + w('tbl') + '/' + w('tr')).findall(w('tc'))
        content = entries(selection, profile)
        rebuild_sidebar(left, selection, profile, labels)
        for key, marker, next_marker in labels['sections']:
            rebuild_section(right, marker, next_marker, content[key])
        changed = ET.tostring(document, encoding='unicode').encode('utf-8')
        declared = set(re.findall(rb'xmlns:\w+=', root_tag))
        extra = b''.join(b' ' + item for item in re.findall(rb'xmlns:\w+="[^"]+"', re.search(rb'<w:document\b[^>]*>', changed).group()) if item.split(b'"')[0] not in declared)
        changed = re.sub(rb'<w:document\b[^>]*>', lambda match: root_tag[:-1] + extra + b'>', changed, count=1)
        changed = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + changed
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as output:
            for item in source.infolist():
                output.writestr(item, changed if item.filename == 'word/document.xml' else source.read(item.filename))

# Word exporta el PDF, informa las páginas reales y entrega la primera como imagen para el panel.
EXPORT = '''param([string]$InputDocx,[string]$OutputPdf,[string]$OutputPng,[string]$OutputPages)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$app = $null
$document = $null
try {
  $app = New-Object -ComObject Word.Application
  $app.Visible = $false
  $app.DisplayAlerts = 0
  $document = $app.Documents.Open($InputDocx, $false, $true)
  $document.ExportAsFixedFormat($OutputPdf, 17)
  [IO.File]::WriteAllText($OutputPages, [string]$document.ComputeStatistics(2))
  $bytes = $document.Windows.Item(1).Panes.Item(1).Pages.Item(1).EnhMetaFileBits
  $stream = New-Object IO.MemoryStream(,$bytes)
  $metafile = New-Object Drawing.Imaging.Metafile($stream)
  $width = 1240
  $height = [int]($width * $metafile.Height / $metafile.Width)
  $bitmap = New-Object Drawing.Bitmap($width, $height)
  $graphics = [Drawing.Graphics]::FromImage($bitmap)
  $graphics.Clear([Drawing.Color]::White)
  $graphics.DrawImage($metafile, 0, 0, $width, $height)
  $bitmap.Save($OutputPng, [Drawing.Imaging.ImageFormat]::Png)
  $graphics.Dispose(); $bitmap.Dispose(); $metafile.Dispose(); $stream.Dispose()
} finally {
  if ($document) { $document.Close(0); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
  if ($app) { $app.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app) }
}
'''

def detect_renderer():
    if os.name=='nt':
        probe=subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',"if ([type]::GetTypeFromProgID('Word.Application')) { 'word' }"],capture_output=True,text=True,timeout=10)
        if 'word' in probe.stdout: return 'word'
    candidates=[shutil.which('soffice'),r'C:\Program Files\LibreOffice\program\soffice.exe']
    return next((item for item in candidates if item and Path(item).is_file()),None)

def convert(renderer,docx,folder):
    """Devuelve (pdf, png o None, páginas o None)."""
    pdf=folder/'preview.pdf'; png=None; pages=None
    if renderer=='word':
        # Pasar rutas como argumentos, sin interpolarlas en código PowerShell.
        script=folder/'export.ps1'; png=folder/'preview.png'; counter=folder/'pages.txt'
        script.write_text(EXPORT,encoding='utf-8-sig')
        subprocess.run(['powershell','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(script),str(docx),str(pdf),str(png),str(counter)],check=True,capture_output=True,timeout=90)
        pages=int(counter.read_text(encoding='utf-8-sig').strip())
        if not png.is_file() or png.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n': png=None
    else:
        profile=folder/'lo-profile'
        subprocess.run([renderer,'-env:UserInstallation='+profile.as_uri(),'--headless','--convert-to','pdf','--outdir',str(folder),str(docx)],check=True,capture_output=True,timeout=90)
        os.replace(folder/(docx.stem+'.pdf'),pdf)
    if not pdf.is_file() or not pdf.read_bytes()[:8].startswith(b'%PDF'): raise ValueError('El renderizador no produjo una vista válida.')
    if pages is None:
        pages=len(re.findall(rb'/Type\s*/Page\b',pdf.read_bytes())) or None
    return pdf,png,pages
