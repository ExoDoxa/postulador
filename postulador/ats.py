"""Puntaje tipo ATS sin IA e idoneidad por requisitos: mide cuánto mejora un CV al adaptarlo, sin inventar hechos.

Es una estimación propia: ningún ATS real publica su fórmula y el puntaje no predice una contratación.
"""
import json
import re
import unicodedata
from . import cv, datos, perfil as perfiles

ACTIVA = re.compile(r'requisit|requirement|qualification|must have|indispensable|excluyente|buscamos|you have|debes|necesitas|what you.?ll need|perfil', re.I)
SECCION = re.compile(r'^[^.]{3,60}:?$')
STOP = set('''a al algo ante aqui asi aun cada como con contra cual cuando de del desde donde dos e el ella ellos en entre era es esa ese eso esta estar este esto estos fue ha hacer hay la las le lo los mas me mi mucho muy ni no nos nuestra nuestro o otra otro para pero poco por porque puede que quien se segun ser si sin sobre son su sus tambien te tener tiene todo todos tu tus un una uno unos y ya
empresa trabajo cargo oferta equipo persona buscamos requisitos funciones responsabilidades experiencia anos ano nivel aplicar vacante salario
alguien nosotros nuestras nuestros ustedes usted tipo lugar acuerdo manera forma parte donde mismo misma cualquier siempre mejor mejores gran grandes buen buena bueno ofrecemos beneficios contrato modalidad remoto presencial horario adicional adicionales actividades capacidad capacidades completo completa
a able about active actively across after all also an and any are as at be because been being both but by can company could do does each either etc for from full general get given good great has have help how if in into is it its job join just like make may more most must need needs new of on one only or other our out over own per position remote role same should so some such than team that the their them then there these they this those through to under up us very via was we well were what when where which while who why will with within without work working would you your years year experience required requirements responsibilities skills ability strong including using plus fully candidate candidates employment type salary benefits monthly post'''.split())
CORTOS = {'ai', 'ia', 'qa', 'ux', 'ui', 'bi', 'hr', 'rh', 'c#', 'c++', 'sql', 'api', 'crm', 'erp', 'seo', 'aws', 'git', 'php', 'b1', 'b2', 'c1', 'c2', 'go', 'r'}
RUIDO = re.compile(r'https?://\S+|www\.\S+|\S+@\S+|\S+\.(?:com|ai|io|co|org|net)\S*')
SINONIMOS = {'customer': 'client', 'customers': 'client', 'cliente': 'client', 'clientes': 'client', 'quality': 'qa', 'calidad': 'qa', 'ia': 'ai', 'inteligencia artificial': 'ai', 'artificial intelligence': 'ai', 'rh': 'hr', 'ingles': 'english', 'espanol': 'spanish', 'psicologia': 'psychology',
             'investigacion': 'research', 'atencion al cliente': 'customer service', 'soporte': 'support', 'pruebas': 'testing', 'desarrollo': 'development'}
TEXTOS_INGLES = {'the', 'and', 'with', 'you', 'for', 'will', 'our', 'are'}
TEXTOS_ESPANOL = {'el', 'la', 'con', 'para', 'los', 'del', 'las', 'una'}
UMBRAL_APLICAR, UMBRAL_REVISAR = 70, 50
TOPE_EXCLUYENTE = 39
VALOR_ESTADO = {'cumple': 1, 'parcial': .5, 'por_confirmar': .5, 'brecha': 0}
TERMINOS_MAXIMOS = 30
PORCION_CONTACTO = .5

def plano(texto):
    sin_tildes = unicodedata.normalize('NFKD', texto.lower()).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', sin_tildes).strip()

def palabras(texto):
    return re.findall(r'[a-z0-9][a-z0-9+#.\-]*[a-z0-9+#]|[a-z0-9]', plano(RUIDO.sub(' ', texto)))

def raiz(palabra):
    palabra = SINONIMOS.get(palabra, palabra)
    if len(palabra) > 3 and palabra.endswith('s') and not palabra.endswith('ss'): palabra = palabra[:-1]
    return palabra[:7] if len(palabra) >= 8 else palabra

def valida(palabra):
    if palabra in STOP: return False
    if palabra in CORTOS: return True
    return palabra.replace('-', '').replace('.', '').isalpha() and len(palabra) >= 3

def raices(texto):
    limpio = plano(texto)
    for frase, sustituto in SINONIMOS.items():
        if ' ' in frase: limpio = limpio.replace(frase, sustituto)
    return {raiz(palabra) for palabra in palabras(limpio) if valida(palabra)}

def terminos(oferta):
    """Separa los términos de la oferta en requisitos y resto, ordenados por peso."""
    pesos, requisitos, legibles, activa = {}, set(), {}, False
    for linea in oferta.splitlines():
        if ACTIVA.search(linea) and SECCION.match(linea.strip()): activa = True
        elif SECCION.match(linea.strip()) and not linea.lstrip().startswith(('-', '*', '•')): activa = False
        for palabra in [p for p in palabras(linea) if valida(p)]:
            legibles.setdefault(raiz(palabra), palabra)
        for termino in {raiz(p) for p in palabras(linea) if valida(p)}:
            requisito = activa or bool(ACTIVA.search(linea))
            pesos[termino] = pesos.get(termino, 0) + (2 if requisito else 1)
            if requisito: requisitos.add(termino)
    principales = sorted(pesos, key=lambda termino: (-pesos[termino], termino))[:TERMINOS_MAXIMOS]
    return {termino: pesos[termino] for termino in principales}, requisitos, legibles

def puntuar(oferta, titulo, texto_cv):
    """Sobre 100: requisitos 40, resto de la oferta 20, cargo 20, secciones 10 y formato 10."""
    pesos, requisitos, legibles = terminos(oferta)
    presentes = raices(texto_cv)
    def cobertura(claves):
        total = sum(pesos[clave] for clave in claves)
        return sum(pesos[clave] for clave in claves if clave in presentes) / total if total else 1
    clave_requisitos = [termino for termino in pesos if termino in requisitos]
    resto = [termino for termino in pesos if termino not in requisitos]
    cargo = raices(titulo)
    plano_cv = plano(texto_cv)
    secciones = sum((bool(re.search(r'@|\+\d', texto_cv)), len(texto_cv) > 300, bool(re.search(r'\b(19|20)\d{2}\b', texto_cv))))
    desglose = {'requisitos': round(40 * cobertura(clave_requisitos), 1), 'resto_oferta': round(20 * cobertura(resto), 1),
                'cargo': round(20 * (len(cargo & presentes) / len(cargo) if cargo else 1), 1), 'secciones': round(10 * secciones / 3, 1),
                'formato': 10.0 if len(plano_cv.split()) >= 150 else 5.0}
    return {'puntaje': round(sum(desglose.values())), 'desglose': desglose, 'faltan': [legibles[termino] for termino in pesos if termino not in presentes]}

def idioma_de(texto):
    lista = set(palabras(texto))
    return 'en' if len(lista & TEXTOS_INGLES) > len(lista & TEXTOS_ESPANOL) else 'es'

def _notas():
    archivo = datos() / 'notas.md'
    return archivo.read_text(encoding='utf-8') if archivo.is_file() else ''

def _todos_los_perfiles():
    """Los perfiles traducen los mismos hechos: una cita vale en cualquier idioma."""
    return ' '.join(archivo.read_text(encoding='utf-8') for archivo in sorted(datos().glob('perfil*.json')))

def revisar_requisitos(requisitos, oferta, perfil):
    """El agente clasifica; aquí se exige que cite la oferta y que lo cumplido tenga respaldo verificable."""
    if not requisitos: raise ValueError('Analiza al menos un requisito de la oferta.')
    fuente_oferta, respaldo = plano(oferta), plano(json.dumps(perfil, ensure_ascii=False) + _todos_los_perfiles() + _notas())
    puntos = total = 0
    for requisito in requisitos:
        estado, peso = requisito.get('estado'), 3 if requisito.get('excluyente') else 1
        if estado not in VALOR_ESTADO: raise ValueError('estado inválido; usa: ' + ', '.join(VALOR_ESTADO))
        if plano(requisito.get('texto', '')) not in fuente_oferta or not requisito.get('texto', '').strip():
            raise ValueError('texto debe citar literalmente la oferta: ' + str(requisito.get('texto')))
        if estado in ('cumple', 'parcial') and (not requisito.get('evidencia', '').strip() or plano(requisito['evidencia']) not in respaldo):
            raise ValueError('evidencia debe citar literalmente el perfil o las notas: ' + requisito['texto'])
        puntos += VALOR_ESTADO[estado] * peso; total += peso
    return round(100 * puntos / total)

def decidir(idoneidad, requisitos):
    if any(r.get('excluyente') and r['estado'] == 'brecha' for r in requisitos): return 'no_aplicar'
    if any(r.get('excluyente') and r['estado'] == 'por_confirmar' for r in requisitos): return 'preguntar'
    return 'aplicar' if idoneidad >= UMBRAL_APLICAR else 'revisar' if idoneidad >= UMBRAL_REVISAR else 'no_aplicar'

def idoneidad_con(puntaje_requisitos, puntaje_ats, requisitos):
    valor = round(.7 * puntaje_requisitos + .3 * puntaje_ats)
    return min(valor, TOPE_EXCLUYENTE) if any(r.get('excluyente') and r['estado'] == 'brecha' for r in requisitos) else valor

def evaluar(oferta, titulo, requisitos, seleccion, idioma='es'):
    """Compara CV base, CV adaptado y techo: lo máximo posible usando solo hechos del perfil."""
    if len(oferta.strip()) < 80: raise ValueError('La oferta es demasiado breve; lee la descripción completa.')
    perfil = perfiles.leer(idioma)
    cv.validar(seleccion, perfil)
    base = puntuar(oferta, titulo, cv.texto_seleccion(cv.seleccion_base(perfil), perfil))
    adaptado = puntuar(oferta, titulo, cv.texto_seleccion(seleccion, perfil))
    techo = puntuar(oferta, titulo, cv.texto_perfil(perfil))
    puntaje_requisitos = revisar_requisitos(requisitos, oferta, perfil)
    idoneidad = idoneidad_con(puntaje_requisitos, adaptado['puntaje'], requisitos)
    mejora = adaptado['puntaje'] - base['puntaje']
    resultado = {
        'resumen': 'Idoneidad %d %%. ATS: CV genérico %d → CV adaptado %d (%+d). Máximo con hechos del perfil: %d. Decisión: %s.' % (idoneidad, base['puntaje'], adaptado['puntaje'], mejora, techo['puntaje'], decidir(idoneidad, requisitos)),
        'oferta_caracteres': len(oferta), 'idoneidad': idoneidad, 'idoneidad_base': idoneidad_con(puntaje_requisitos, base['puntaje'], requisitos), 'requisitos': puntaje_requisitos,
        'ats_base': base['puntaje'], 'ats_adaptado': adaptado['puntaje'], 'ats_techo': techo['puntaje'], 'mejora': mejora,
        'decision': decidir(idoneidad, requisitos), 'desglose': adaptado['desglose'],
        'disponibles_en_perfil': [t for t in adaptado['faltan'] if t not in techo['faltan']], 'brechas_reales': techo['faltan'],
        'aviso': 'Estimación propia, no la de un ATS real. Las brechas reales no se rellenan: serían inventar.',
    }
    if idioma_de(oferta) != idioma: resultado['aviso_idioma'] = 'La oferta parece estar en otro idioma; evalúa con el perfil en ese idioma.'
    return resultado

def cifras_sin_respaldo(texto, perfil):
    numero = r'\d[\d.,]*\d|\d'
    respaldo = plano(json.dumps(perfil, ensure_ascii=False) + _notas())
    return sorted(cifra for cifra in set(re.findall(numero, plano(texto))) - set(re.findall(numero, respaldo)) if not re.fullmatch(r'0\d', cifra))

def extraer_pdf(ruta):
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        return None
    return extract_text(str(ruta))

def revisar_pdf(ruta, seleccion, idioma='es'):
    """Lee el PDF como lo haría un ATS: detecta texto ilegible, columnas mezcladas y cifras sin respaldo."""
    texto = extraer_pdf(ruta)
    if texto is None: return {'disponible': False, 'problemas': ['Instala pdfminer.six para leer el PDF: pip install -r requirements.txt']}
    perfil = perfiles.leer(idioma)
    leido, problemas = plano(texto), []
    if len(leido.split()) < 100: problemas.append('Casi no hay texto legible: un ATS podría verlo vacío.')
    for dato in perfil['contact']:
        if plano(dato) not in leido: problemas.append('Contacto no legible: ' + dato)
    primero = next((plano(dato) for dato in perfil['contact'] if '@' in dato), '')
    posicion = leido.find(primero) / max(len(leido), 1) if primero and primero in leido else 0
    if posicion > PORCION_CONTACTO: problemas.append('El correo aparece al %d%% del texto: un ATS puede leer tu contacto y tu resumen después de la experiencia.' % round(posicion * 100))
    fragmentos = [seleccion['summary']] + [viñeta for item in cv.experiencias(seleccion, perfil) for viñeta in cv.motor_docx.bullets_for(seleccion, item)]
    enteros = [fragmento for fragmento in fragmentos if plano(fragmento) in leido]
    orden = round(100 * len(enteros) / len(fragmentos))
    if orden < 80: problemas.append('Solo %d%% de los párrafos se lee de corrido: las columnas pueden estar mezclándose.' % orden)
    cifras = cifras_sin_respaldo(texto, perfil)
    if cifras: problemas.append('Cifras que no están en el perfil, revisa la plantilla: ' + ', '.join(cifras[:10]))
    return {'disponible': True, 'palabras': len(leido.split()), 'lectura_en_orden': orden, 'problemas': problemas}
