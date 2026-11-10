"""Preferencias de búsqueda: las edita el usuario en el panel y el agente solo las lee.

También arma la dirección de búsqueda de LinkedIn con esas preferencias. Se usa la vista pública de resultados
(`jobs-guest`), que respeta los filtros de antigüedad y modalidad, trae el número de cada oferta en su enlace y
es más corta de leer que el buscador normal. Desde código responde con un desafío anti-bots, así que se abre en el
navegador del usuario, a través de la puerta.
"""
from urllib.parse import urlencode
from . import navegador

ANTIGUEDADES = {24: 'Último día', 48: 'Últimos 2 días', 72: 'Últimos 3 días', 168: 'Última semana', 336: 'Últimas 2 semanas', 720: 'Último mes'}
MODALIDADES = ('remoto', 'hibrido', 'presencial')
IDIOMAS = ('es', 'en', 'pt', 'fr')
POR_DEFECTO = {'antiguedad_horas': 48, 'modalidades': list(MODALIDADES), 'ubicaciones': ['Colombia'], 'cargos': [],
               'excluir': [], 'salario_minimo': '', 'idiomas': ['es']}
LINKEDIN = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?'
LINKEDIN_MODALIDAD = {'presencial': '1', 'remoto': '2', 'hibrido': '3'}
LINKEDIN_PAIS = {'colombia': '100876405'}
POR_PAGINA = 10

def _lista(valor, maximo, largo):
    """Acepta una lista o un texto separado por comas; quita vacíos y repetidos."""
    partes = valor.split(',') if isinstance(valor, str) else list(valor or [])
    limpias = []
    for parte in partes:
        texto = ' '.join(str(parte).split())
        if not texto: continue
        if len(texto) > largo: raise ValueError('«%s…» es demasiado largo (máximo %d caracteres).' % (texto[:20], largo))
        if texto.lower() not in (x.lower() for x in limpias): limpias.append(texto)
    if len(limpias) > maximo: raise ValueError('Máximo %d elementos por lista.' % maximo)
    return limpias

def leer():
    guardadas = navegador.configuracion().get('busqueda') or {}
    return {clave: guardadas.get(clave, valor) for clave, valor in POR_DEFECTO.items()}

def guardar(dato):
    """Solo la usa el usuario desde el panel; el agente no tiene herramienta para cambiarlas."""
    try: horas = int(dato.get('antiguedad_horas', POR_DEFECTO['antiguedad_horas']))
    except (TypeError, ValueError): raise ValueError('La antigüedad debe ser un número de horas.')
    if not 1 <= horas <= 2160: raise ValueError('La antigüedad va de 1 hora a 90 días.')
    modalidades = [m for m in _lista(dato.get('modalidades', MODALIDADES), 3, 20) if m in MODALIDADES]
    if not modalidades: raise ValueError('Elige al menos una modalidad: remoto, híbrido o presencial.')
    idiomas = [i for i in _lista(dato.get('idiomas', ['es']), 4, 2) if i in IDIOMAS] or ['es']
    salario = ' '.join(str(dato.get('salario_minimo', '')).split())
    if len(salario) > 40: raise ValueError('El salario mínimo es demasiado largo.')
    limpio = {'antiguedad_horas': horas, 'modalidades': modalidades, 'ubicaciones': _lista(dato.get('ubicaciones', []), 10, 60),
              'cargos': _lista(dato.get('cargos', []), 20, 60), 'excluir': _lista(dato.get('excluir', []), 30, 60),
              'salario_minimo': salario, 'idiomas': idiomas}
    navegador.guardar_configuracion(busqueda=limpio)
    return leer()

def url_linkedin(palabras, ubicacion='', pagina=0):
    """Dirección de resultados de LinkedIn con las preferencias del usuario: 10 ofertas por página."""
    if not str(palabras).strip(): raise ValueError('Indica el cargo o las palabras que buscas.')
    preferencias = leer()
    lugar = (ubicacion or (preferencias['ubicaciones'] or ['Colombia'])[0]).strip()
    parametros = {'keywords': ' '.join(str(palabras).split()), 'location': lugar,
                  'f_TPR': 'r%d' % (preferencias['antiguedad_horas'] * 3600), 'start': max(0, int(pagina)) * POR_PAGINA}
    if lugar.lower() in LINKEDIN_PAIS: parametros['geoId'] = LINKEDIN_PAIS[lugar.lower()]
    if set(preferencias['modalidades']) != set(MODALIDADES):
        parametros['f_WT'] = ','.join(LINKEDIN_MODALIDAD[m] for m in MODALIDADES if m in preferencias['modalidades'])
    return {'url': LINKEDIN + urlencode(parametros), 'preferencias': preferencias,
            'leer': 'Ábrela con browser_navigate. Cada oferta es un link con su número al final de /jobs/view/…-<número>, '
                    'empresa, lugar y «Hace N horas». Descarta las que contengan alguna palabra de «excluir». '
                    'Para la siguiente página llama con pagina+1; si llega vacía, no hay más.'}
