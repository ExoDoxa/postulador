'use strict';
const vista = document.getElementById('vista');
let token = '', huellaMesa = '', nodoVivo = null, cvAbierto = null, comprobanteAbierto = null, estricto = true;

const el = (etiqueta, atributos = {}, ...hijos) => {
  const nodo = document.createElement(etiqueta);
  for (const [clave, valor] of Object.entries(atributos)) {
    if (clave.startsWith('on')) nodo.addEventListener(clave.slice(2), valor);
    else if (clave === 'clase') nodo.className = valor;
    else if (valor !== null && valor !== undefined) nodo.setAttribute(clave, valor);
  }
  nodo.append(...hijos.flat().filter((hijo) => hijo !== null && hijo !== undefined));
  return nodo;
};

const avisar = (texto) => {
  const nodo = document.getElementById('aviso');
  nodo.textContent = texto; nodo.hidden = false;
  clearTimeout(avisar.t); avisar.t = setTimeout(() => { nodo.hidden = true; }, 3500);
};

async function pedir(ruta, cuerpo) {
  const opciones = cuerpo === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Panel-Token': token }, body: JSON.stringify(cuerpo) };
  const respuesta = await fetch(ruta, opciones);
  const dato = await respuesta.json();
  if (!respuesta.ok) throw new Error(dato.error || 'Algo falló.');
  return dato;
}

const accion = (funcion) => async (evento) => {
  const boton = evento.currentTarget; boton.disabled = true;
  try { await funcion(evento); } catch (error) { avisar(error.message); } finally { boton.disabled = false; }
};

const enlace = (url, texto) => (/^https?:\/\//i.test(url) ? el('a', { href: url, target: '_blank', rel: 'noopener noreferrer' }, texto) : texto);
const vacio = (texto) => el('p', { clase: 'vacio' }, texto);
const tono = (valor) => (valor >= 70 ? '' : valor >= 50 ? ' medio' : ' bajo');

const tabla = (columnas, filas) => el('div', { clase: 'envoltura' }, el('table', {},
  el('thead', {}, el('tr', {}, columnas.map(([titulo, , clase]) => el('th', { clase, scope: 'col' }, titulo)))),
  el('tbody', {}, filas.map((fila) => el('tr', {}, columnas.map(([, celda, clase]) => el('td', { clase }, celda(fila))))))));

const ESTADOS = {
  preparada: 'En preparación', por_aprobar: 'Espera aprobación', rellenada: 'Lista para enviar', reportada: 'Enviada según el asistente, ¿la confirmas?',
  enviada: 'Enviada', avanzo: 'Avanzó', rechazada: 'Rechazada', descartada: 'Descartada', incompleta: 'Incompleta',
};
const nombreEstado = (estado) => ESTADOS[estado] || estado;

const verComprobante = (id) => () => { comprobanteAbierto = id; if (location.hash === '#comprobante') mostrar(); else location.hash = '#comprobante'; };

const SELLOS = { la_envie: 'Enviada', ya_no: 'Descartada', corregir: 'Devuelta', ya_estaba_enviada: 'Enviada' };
const folio = (id) => el('span', { clase: 'folio', 'aria-hidden': 'true' }, 'Folio ' + String(id).padStart(3, '0'));

// Las cuatro decisiones de ella sobre una postulación que espera su envío. El sello cae sobre la ficha y luego se archiva.
function botonesEnvio(item, alTerminar) {
  const hacer = (accionPedida, mensaje) => accion(async (evento) => {
    const ficha = evento.currentTarget.closest('.expediente, .olvidada');
    await pedir('/api/postulaciones/' + item.id, { accion: accionPedida });
    avisar(mensaje);
    if (ficha) ficha.dataset.sello = SELLOS[accionPedida];
    setTimeout(alTerminar, ficha ? 520 : 0);
  });
  return el('div', { clase: 'acciones' },
    el('button', { clase: 'sellar', onclick: hacer('la_envie', 'Anotada como enviada. Empieza a contar el seguimiento.') }, 'La envié'),
    el('button', { onclick: hacer('ya_no', 'Descartada.') }, 'No, ya no'),
    el('button', { onclick: hacer('corregir', 'El asistente la puede corregir.') }, 'Que el asistente la corrija'),
    el('button', { onclick: hacer('ya_estaba_enviada', 'Anotada como enviada y como incidente: el asistente no debió poder enviarla.') }, 'Ya estaba enviada cuando la vi'));
}

async function listaParaEnviar() {
  const esperan = await pedir('/api/postulaciones?estado=rellenada,reportada');
  const cuerpo = [el('h2', {}, 'Lista para enviar'),
    el('p', { clase: 'nota' }, 'El asistente rellenó estos formularios. Revisa la ventana del navegador, corrige si quieres y pulsa Enviar tú. Después dime aquí qué pasó: mientras alguna espere, el asistente no puede seguir.')];
  if (!esperan.length) cuerpo.push(vacio('Nada espera tu envío. Cuando el asistente rellene un formulario, la ficha aparecerá aquí.'));
  for (const item of esperan) {
    cuerpo.push(el('article', { clase: 'expediente' }, folio(item.id),
      el('div', {},
        el('p', { clase: 'etiqueta' }, item.sitio),
        el('h3', {}, item.cargo),
        el('p', {}, item.empresa, ' · ', enlace(item.url, 'ver oferta')),
        el('p', { clase: item.estado === 'reportada' ? 'marca reportada' : 'marca' }, nombreEstado(item.estado)),
        botonesEnvio(item, mostrar)),
      el('aside', {}, item.comprobante ? el('button', { onclick: verComprobante(item.comprobante) }, 'Lo que rellenó el asistente') : el('p', { clase: 'nota' }, 'Sin comprobante'))));
  }
  return cuerpo;
}

async function aprobacionesAutor() {
  const pendientes = await pedir('/api/aprobaciones');
  if (!pendientes.length) return [];
  const cuerpo = [el('h2', {}, 'Aprobaciones pendientes')];
  for (const item of pendientes) {
    const resolver = (aprobar) => accion(async (evento) => {
      const tarjeta = evento.currentTarget.closest('.expediente');
      await pedir('/api/aprobaciones/' + item.id, { aprobar });
      tarjeta.dataset.sello = aprobar ? 'Aprobada' : 'Rechazada';
      avisar(aprobar ? 'Aprobada: vale una sola vez durante 24 horas.' : 'Rechazada.');
      setTimeout(mostrar, 620);
    });
    const lateral = item.idoneidad === null ? [] : [el('p', { clase: 'etiqueta' }, 'Idoneidad'), el('p', { clase: 'porcentaje' + tono(item.idoneidad) }, item.idoneidad + ' %')];
    cuerpo.push(el('article', { clase: 'expediente' },
      el('div', {}, el('p', { clase: 'etiqueta' }, item.host), el('h3', {}, item.cargo), el('p', {}, item.empresa, ' · ', enlace(item.url, 'ver formulario')),
        item.detalle ? el('pre', {}, item.detalle) : null,
        el('div', { clase: 'acciones' }, el('button', { clase: 'sellar', onclick: resolver(true) }, 'Aprobar envío'), el('button', { onclick: resolver(false) }, 'Rechazar'))),
      el('aside', {}, lateral)));
  }
  return cuerpo;
}

async function mesa() {
  const partes = [await listaParaEnviar()];
  if (!estricto) partes.push(await aprobacionesAutor());
  huellaMesa = JSON.stringify(await pedir('/api/postulaciones?estado=rellenada,reportada'));
  return partes.flat();
}

async function comprobante() {
  if (!comprobanteAbierto) return [vacio('Elige un comprobante desde «Lista para enviar» o «Postulaciones».')];
  const dato = await pedir('/api/comprobantes/' + comprobanteAbierto);
  return [
    el('div', { clase: 'fila' }, el('button', { onclick: () => { location.hash = '#mesa'; } }, '← Volver')),
    el('h2', {}, 'Lo que rellenó el asistente'),
    el('section', { clase: 'recibo', 'aria-label': 'Comprobante ' + dato.id },
    el('p', { clase: 'etiqueta' }, 'Comprobante N.º ' + String(dato.id).padStart(4, '0') + ' · escrito por la puerta, no por el asistente'),
    el('p', {}, el('strong', {}, dato.cargo), ' · ', dato.empresa, ' · ', nombreEstado(dato.estado)),
    el('p', { clase: 'riesgo' }, 'Si cambiaste algo antes de enviar, lo enviado puede ser distinto.'),
    el('p', { clase: 'nota' }, 'Empezó ', dato.inicio, ' · terminó ', dato.fin, dato.envios_bloqueados ? ' · la puerta bloqueó ' + dato.envios_bloqueados + ' intento(s) de pulsar botones' : ''),
    el('h3', {}, 'Campos'),
    dato.campos.length ? tabla([['Campo', (f) => f.campo], ['Valor', (f) => f.valor], ['Hora', (f) => f.hora, 'numero']], dato.campos) : vacio('No escribió campos.'),
    el('h3', {}, 'Casillas y clics'),
    dato.clics.length ? tabla([['Elemento', (f) => f.elemento], ['Hora', (f) => f.hora, 'numero']], dato.clics) : vacio('Sin clics anotados.'),
    el('h3', {}, 'Archivos subidos'),
    dato.archivos.length ? tabla([['Archivo', (f) => f.archivo], ['CV', (f) => f.cv || '—'], ['Hora', (f) => f.hora, 'numero']], dato.archivos) : vacio('No subió archivos.'),
    el('h3', {}, 'Así se veía la página'),
    dato.tiene_imagen ? el('a', { href: '/api/comprobantes/' + dato.id + '/imagen', target: '_blank', rel: 'noopener' }, el('img', { clase: 'imagen-pagina', src: '/api/comprobantes/' + dato.id + '/imagen', alt: 'Imagen de la página cuando el asistente terminó' })) : vacio('No hay imagen de la página.')),
  ];
}

const filaTasas = (titulo, filas) => [el('h2', {}, titulo), filas.length ? tabla([
  ['Grupo', (f) => f.grupo], ['Enviadas', (f) => String(f.enviadas), 'numero'],
  ['Respuesta', (f) => el('span', {}, f.tasa_respuesta + ' %')], ['Avance', (f) => el('span', {}, f.tasa_avance + ' %')],
], filas.slice(0, 10)) : vacio('Todavía sin datos.')];

const NOMBRES = { browser_click: 'Clic', browser_navigate: 'Abrir página', browser_snapshot: 'Leer página', browser_type: 'Escribir', browser_fill_form: 'Rellenar formulario', browser_tabs: 'Pestañas', browser_press_key: 'Pulsar tecla', browser_file_upload: 'Subir archivo', browser_take_screenshot: 'Imagen de la página', cv_generar: 'Generar CV', ats_evaluar: 'Evaluar oferta', postulacion_registrar: 'Registrar postulación', informe_guardar: 'Guardar informe', formulario_listo: 'Formulario listo', formulario_abandonar: 'Formulario abandonado', incidente_envio: 'Ya estaba enviada (incidente)', diagnostico: 'Revisar instalación', documento_leer: 'Leer documento' };

async function pintarVivo() {
  const dato = await pedir('/api/vivo');
  nodoVivo.replaceChildren(
    el('h2', {}, 'Pestañas del navegador'),
    dato.pestanas.length ? tabla([['Página', (f) => enlace(f.url, f.titulo || f.url)]], dato.pestanas) : vacio('El navegador está cerrado.'),
    el('h2', {}, 'Qué está haciendo el asistente'),
    dato.actividad.length ? tabla([
      ['Hora', (f) => f.hora.slice(11), 'numero'], ['Acción', (f) => NOMBRES[f.accion] || f.accion],
      ['Resultado', (f) => (f.bloqueada ? el('strong', { clase: 'bloqueo' }, 'Bloqueada por la puerta') : f.error ? 'Con error' : 'Hecha')], ['Dónde', (f) => f.lugar || '—'],
    ], dato.actividad) : vacio('Sin actividad todavía. Pídele algo al asistente en el chat.'));
}

async function vivo() {
  nodoVivo = el('div');
  await pintarVivo();
  return [el('p', { clase: 'nota' }, 'Conversas en el chat; aquí ves lo que pasa. Lo que el asistente escribe en cada formulario queda en su comprobante.'), nodoVivo];
}

async function informes() {
  const lista = await pedir('/api/informes');
  const lector = el('pre', { clase: 'informe', hidden: 'hidden', tabindex: '0', 'aria-label': 'Contenido del informe' });
  const abrir = (nombre) => accion(async () => { const dato = await pedir('/api/informes/' + encodeURIComponent(nombre)); lector.hidden = false; lector.textContent = dato.contenido; lector.focus(); });
  return [el('h2', {}, 'Informes'),
    lista.length ? lista.map((item) => el('button', { clase: 'tarea', onclick: abrir(item.nombre) }, item.nombre)) : vacio('El asistente dejará aquí sus informes.'), lector];
}

const COLORES = [['Azul tinta', '#1f3a4d'], ['Verde bosque', '#24513f'], ['Vino', '#6d2433'], ['Grafito', '#2b2b2f'], ['Terracota', '#8c2f1b']];
const rutaCv = (nombre, archivo, version, descarga) => '/cv/' + encodeURIComponent(nombre) + '/' + encodeURIComponent(archivo) + '?v=' + version + (descarga ? '&descargar=1' : '');

async function galeria() {
  const dato = await pedir('/api/cv');
  if (!dato.cv.length) return [el('h2', {}, 'Mis CV'), vacio('Pídele al asistente: «hazme un CV para este cargo». Aparecerá aquí.')];
  return [el('h2', {}, 'Mis CV'), el('div', { clase: 'galeria' }, dato.cv.map((item) => el('button', { clase: 'hoja-cv', onclick: () => { cvAbierto = item.nombre; mostrar(); } },
    item.preview ? el('img', { src: rutaCv(item.nombre, 'preview.png', item.version), alt: '', loading: 'lazy' }) : el('span', { clase: 'sin-vista' }, 'Sin vista previa'),
    el('span', { clase: 'nombre-cv' }, item.nombre.replace(/_/g, ' ')),
    item.pendientes ? el('span', { clase: 'cuenta' }, item.pendientes + ' por atender') : null)))];
}

async function editorCv() {
  const dato = await pedir('/api/cv/' + encodeURIComponent(cvAbierto));
  const nombre = dato.nombre, ajustes = dato.ajustes;
  const opcion = (valor, texto, actual) => el('option', { value: valor, ...(String(valor) === String(actual) ? { selected: 'selected' } : {}) }, texto);
  const campo = (etiqueta, control) => el('label', { clase: 'campo' }, el('span', { clase: 'etiqueta' }, etiqueta), control);
  const diseno = el('select', {}, Object.entries(dato.disenos).map(([valor, texto]) => opcion(valor, valor + ' · ' + texto, ajustes.plantilla || 'columna')));
  const fuente = el('select', {}, dato.fuentes.map((valor) => opcion(valor, valor, ajustes.fuente)));
  const tamano = el('input', { type: 'number', min: dato.tamanos[0], max: dato.tamanos[1], step: '0.1', value: ajustes.tamano });
  const color = el('select', {}, COLORES.map(([texto, valor]) => opcion(valor, texto, ajustes.color)));
  const foto = el('select', {}, dato.posiciones_foto.map((valor) => opcion(valor, valor, ajustes.foto)));
  const archivo = el('input', { type: 'file', accept: 'image/jpeg,image/png', 'aria-label': 'Subir foto' });
  const aplicar = accion(async () => {
    avisar('Generando el CV…');
    const resultado = await pedir('/api/cv/' + encodeURIComponent(nombre) + '/ajustes', { plantilla: diseno.value, fuente: fuente.value, tamano: Number(tamano.value), color: color.value, foto: foto.value });
    cvAbierto = resultado.nombre;
    avisar(resultado.nombre === nombre ? 'CV actualizado.' : 'Tu CV de Word sigue igual; esta versión quedó como ' + resultado.nombre + '.');
    mostrar();
  });
  archivo.addEventListener('change', async () => {
    if (!archivo.files[0]) return;
    const respuesta = await fetch('/api/foto', { method: 'POST', headers: { 'X-Panel-Token': token }, body: archivo.files[0] });
    const resultado = await respuesta.json();
    avisar(respuesta.ok ? 'Foto guardada. Elige su posición y aplica.' : resultado.error);
  });
  const texto = el('textarea', { 'aria-label': 'Comentario para el asistente', placeholder: 'Quita la experiencia X, resalta mi experiencia en litigio…' });
  const comentar = accion(async () => { await pedir('/api/cv/' + encodeURIComponent(nombre) + '/comentarios', { texto: texto.value }); avisar('Comentario guardado. Pídele al asistente en el chat que lo atienda.'); mostrar(); });
  const abrirCarpeta = accion(async () => { await pedir('/api/cv/' + encodeURIComponent(nombre) + '/abrir', {}); avisar('Carpeta abierta.'); });
  const avisos = (dato.revision.problemas || []).map((linea) => el('p', { clase: 'riesgo' }, linea));
  return [
    el('div', { clase: 'fila' }, el('button', { onclick: () => { cvAbierto = null; mostrar(); } }, '← Todos los CV')),
    el('h2', {}, nombre.replace(/_/g, ' ')),
    el('div', { clase: 'editor' },
      el('div', { clase: 'mesa-cv' }, dato.preview ? el('img', { src: rutaCv(nombre, 'preview.png', dato.version), alt: 'Vista previa del CV ' + nombre }) : vacio('Sin vista previa. Aplica un diseño para generarla.')),
      el('div', { clase: 'controles' },
        avisos.length ? el('h3', {}, 'Cómo lo lee un programa de selección') : null, avisos,
        el('h3', {}, 'Aspecto'),
        el('div', { clase: 'campos' }, campo('Diseño', diseno), campo('Letra', fuente), campo('Tamaño', tamano), campo('Color', color), campo('Foto', foto), campo('Subir foto', archivo)),
        el('div', { clase: 'acciones' }, el('button', { onclick: aplicar }, 'Aplicar cambios')),
        el('h3', {}, 'Comentarios para el asistente'),
        dato.comentarios.length ? el('ul', { clase: 'comentarios' }, dato.comentarios.map((item) => el('li', { clase: item.estado }, el('span', { clase: 'etiqueta' }, item.estado), el('p', {}, item.texto), item.nota ? el('p', { clase: 'nota-agente' }, item.nota) : null))) : null,
        texto,
        el('div', { clase: 'acciones' }, el('button', { onclick: comentar }, 'Guardar comentario')),
        el('h3', {}, 'Exportar'),
        el('div', { clase: 'acciones' },
          dato.pdf ? el('a', { clase: 'boton', href: rutaCv(nombre, dato.pdf, dato.version, true) }, 'PDF') : null,
          dato.docx ? el('a', { clase: 'boton', href: rutaCv(nombre, dato.docx, dato.version, true) }, 'Word') : null,
          el('button', { onclick: abrirCarpeta }, 'Abrir carpeta')))),
  ];
}

const mesaCv = () => (cvAbierto ? editorCv() : galeria());

async function resumen() {
  const dato = await pedir('/api/resumen');
  const cifra = (etiqueta, valor) => el('div', {}, el('strong', {}, String(valor ?? '—')), el('span', { clase: 'etiqueta' }, etiqueta));
  const embudo = dato.embudo;
  const debil = Math.max(0, ...dato.por_sitio.map((f) => f.enviadas)) < 10;
  return [
    el('h2', {}, 'Cómo va la búsqueda'),
    el('div', { clase: 'cifras' }, cifra('Enviadas', (embudo.enviada || 0) + (embudo.avanzo || 0) + (embudo.rechazada || 0)), cifra('Avances', embudo.avanzo || 0), cifra('Rechazos', embudo.rechazada || 0),
      cifra('Esperan tu envío', (embudo.rellenada || 0) + (embudo.reportada || 0))),
    el('p', { clase: 'nota' }, 'Solo cuentan como enviadas las que confirmaste. Un grupo con menos de 10 enviadas es solo una tendencia. Sin respuesta no significa rechazo.', debil ? ' Aún hay pocos datos.' : ''),
    filaTasas('Por sitio', dato.por_sitio), filaTasas('Por CV', dato.por_cv),
    el('h2', {}, 'Motivos de rechazo'),
    dato.motivos.length ? tabla([['Motivo', (f) => f[0]], ['Veces', (f) => String(f[1]), 'numero']], dato.motivos) : vacio('Sin motivos registrados.'),
  ];
}

async function postulaciones() {
  const zona = el('div');
  const texto = el('input', { type: 'search', placeholder: 'Empresa, cargo o sitio', 'aria-label': 'Buscar' });
  const estado = el('select', { 'aria-label': 'Estado' }, ['', ...Object.keys(ESTADOS)].map((v) => el('option', { value: v }, v ? nombreEstado(v) : 'Todos los estados')));
  const respuesta = (fila, accionPedida) => accion(async () => { await pedir('/api/postulaciones/' + fila.id, { accion: accionPedida }); avisar('Anotado.'); await cargar(); });
  const acciones = (f) => {
    if (f.estado === 'enviada') return el('span', { clase: 'fila' }, el('button', { onclick: respuesta(f, 'avanzo') }, 'Avanzó'), el('button', { onclick: respuesta(f, 'rechazada') }, 'Rechazada'));
    if (f.estado === 'rellenada' || f.estado === 'reportada') return el('a', { href: '#mesa' }, 'Resolver');
    return '—';
  };
  const cargar = async () => {
    const filas = await pedir('/api/postulaciones?' + new URLSearchParams({ texto: texto.value, estado: estado.value }));
    zona.replaceChildren(filas.length ? tabla([
      ['Cargo', (f) => enlace(f.url, f.cargo)], ['Empresa', (f) => f.empresa], ['Sitio', (f) => f.sitio],
      ['Estado', (f) => nombreEstado(f.estado)], ['Fecha', (f) => f.enviada_el || '—', 'numero'],
      ['Comprobante', (f) => (f.comprobante ? el('button', { onclick: verComprobante(f.comprobante) }, 'Ver') : '—')], ['Respuesta', acciones],
    ], filas) : vacio('Nada coincide.'));
  };
  texto.addEventListener('input', cargar); estado.addEventListener('change', cargar);
  await cargar();
  return [el('h2', {}, 'Postulaciones'), el('div', { clase: 'filtros' }, texto, estado), zona];
}

async function seguimientos() {
  const filas = await pedir('/api/seguimientos');
  const hecho = (fila) => accion(async () => { await pedir('/api/seguimientos/' + fila.id, { nota: 'Marcado desde el panel' }); avisar('Seguimiento registrado.'); mostrar(); });
  const responder = (fila, accionPedida) => accion(async () => { await pedir('/api/postulaciones/' + fila.id, { accion: accionPedida }); avisar('Anotado.'); mostrar(); });
  return [el('h2', {}, 'Seguimientos pendientes'), el('p', { clase: 'nota' }, 'Si quieres escribirle a la empresa, pídele al asistente un borrador en el chat. Nada se envía solo.'),
    filas.length ? tabla([
      ['Cargo', (f) => enlace(f.url, f.cargo)], ['Empresa', (f) => f.empresa], ['Enviada', (f) => f.enviada_el, 'numero'],
      ['Acciones', (f) => el('span', { clase: 'fila' }, el('button', { onclick: hecho(f) }, 'Hecho'), el('button', { onclick: responder(f, 'rechazada') }, 'Rechazada'), el('button', { onclick: responder(f, 'avanzo') }, 'Avanzó'))],
    ], filas) : vacio('Nada pendiente.')];
}

const CAMPOS_PERFIL = { name: 'Nombre', headline: 'Titular', contact: 'Contacto', skills: 'Habilidades', languages: 'Idiomas', education: 'Formación', experience: 'Experiencia',
  publications: 'Publicaciones', projects: 'Proyectos', cv_summaries: 'Resúmenes', cv_tool_labels: 'Herramientas', carrera: 'Carrera', campos_carrera: 'Datos de carrera', bullets: 'viñetas',
  title: 'título', organization: 'entidad', date: 'fechas', cv_bullets: 'viñetas del CV' };
const nombreCampo = (ruta) => ruta.replace(/[a-z_]+/g, (parte) => CAMPOS_PERFIL[parte] || parte).replace(/\./g, ' › ');
const textoValor = (valor) => (valor === null || valor === undefined ? '—' : typeof valor === 'object' ? JSON.stringify(valor) : String(valor));

async function perfilVista() {
  const [carrera, cambios] = await Promise.all([pedir('/api/perfil/carrera'), pedir('/api/perfil/cambios').catch(() => null)]);
  if (!carrera.perfil) return [el('h2', {}, 'Mi perfil'), vacio('Todavía no hay perfil. Pídele al asistente en el chat: «hagamos mi perfil».')];
  const revisar = accion(async () => { await pedir('/api/perfil/revisado', {}); avisar('Perfil revisado. El asistente ya puede generar tus CV.'); mostrar(); });
  const cuerpo = [el('h2', {}, 'Mi perfil')];
  if (cambios && !cambios.revisado) {
    cuerpo.push(el('section', { clase: 'aviso-perfil' },
      el('h3', {}, cambios.nunca_revisado ? 'Revisa tu perfil antes de que el asistente genere tus CV' : 'El asistente cambió tu perfil: revísalo'),
      el('p', { clase: 'nota' }, 'Mientras no lo marques como revisado, el asistente no genera CV ni cartas.'),
      cambios.cambios.length ? tabla([['Dato', (f) => nombreCampo(f.campo)], ['Antes', (f) => textoValor(f.antes)], ['Ahora', (f) => textoValor(f.despues)]], cambios.cambios.slice(0, 200)) : null,
      el('div', { clase: 'acciones' }, el('button', { clase: 'sellar', onclick: revisar }, 'Revisado'))));
  } else if (cambios) cuerpo.push(el('p', { clase: 'nota' }, 'Revisado el ' + cambios.revisado_el + '.'));
  const elegir = el('select', { 'aria-label': 'Carrera' }, el('option', { value: '' }, 'Elige tu carrera'), carrera.carreras.map((id) => el('option', { value: id, ...(id === carrera.carrera ? { selected: 'selected' } : {}) }, id)));
  const campos = {};
  const formulario = carrera.paquete ? carrera.paquete.campos.map((campo) => {
    campos[campo.clave] = el('input', { value: carrera.valores[campo.clave] || '', 'aria-label': campo.etiqueta, size: 40 });
    return el('label', { clase: 'campo' }, el('span', { clase: 'etiqueta' }, campo.etiqueta + (campo.obligatorio ? ' *' : '') + (campo.sensible ? ' · el asistente no lo ve' : '')), campos[campo.clave]);
  }) : [el('p', { clase: 'nota' }, 'Elige tu carrera para ver sus datos.')];
  const guardar = accion(async () => {
    const valores = Object.fromEntries(Object.entries(campos).map(([clave, control]) => [clave, control.value]));
    await pedir('/api/perfil/carrera', { carrera: elegir.value, valores });
    avisar('Datos guardados.'); mostrar();
  });
  cuerpo.push(el('h2', {}, carrera.paquete ? 'Datos de ' + carrera.paquete.nombre.toLowerCase() : 'Datos de tu carrera'),
    el('div', { clase: 'fila' }, elegir), el('div', { clase: 'campos' }, formulario),
    el('div', { clase: 'acciones' }, el('button', { onclick: guardar }, 'Guardar datos')));
  return cuerpo;
}

async function documentosVista() {
  const dato = await pedir('/api/documentos');
  const cuerpo = [el('h2', {}, 'Mis documentos'),
    el('p', { clase: 'nota' }, 'Deja tus archivos en la carpeta entrada', dato.entrada ? ' (' + dato.entrada + ')' : '', '. Aquí aparecen solos. El asistente solo ve el tipo y el nombre que elijas, y lee el texto únicamente si marcas «El asistente puede leerlo».')];
  if (!dato.documentos.length) cuerpo.push(vacio('Todavía no hay documentos.'));
  for (const item of dato.documentos) {
    const tipo = el('select', { 'aria-label': 'Tipo' }, el('option', { value: '' }, 'Elige el tipo'), dato.tipos.map((t) => el('option', { value: t.clave, ...(t.clave === item.tipo ? { selected: 'selected' } : {}) }, t.etiqueta)));
    const nombre = el('input', { value: item.nombre || '', placeholder: 'Nombre visible', 'aria-label': 'Nombre visible', size: 30 });
    const leer = el('input', { type: 'checkbox', ...(item.ia_puede_leer ? { checked: 'checked' } : {}) });
    const vinculo = el('select', { 'aria-label': 'Vínculo con tu formación' }, el('option', { value: '' }, 'Sin vínculo'), dato.formacion.map((f) => el('option', { value: f.id, ...(f.id === item.vinculo ? { selected: 'selected' } : {}) }, f.titulo)));
    const guardar = accion(async () => {
      await pedir('/api/documentos/' + item.id, { tipo: tipo.value, nombre: nombre.value, ia_puede_leer: leer.checked, vinculo: vinculo.value });
      avisar('Documento guardado.'); mostrar();
    });
    cuerpo.push(el('article', { clase: 'expediente documento' + (item.tipo ? '' : ' nuevo') },
      el('div', {},
        el('p', { clase: 'etiqueta' }, item.tipo ? 'Clasificado' : 'Nuevo: dime qué es'),
        el('h3', {}, item.nombre || item.nombre_original),
        el('p', { clase: 'nota' }, 'Archivo original: ', item.nombre_original, ' · ', el('a', { href: '/api/documentos/' + item.id + '/archivo', target: '_blank', rel: 'noopener' }, 'abrir')),
        el('div', { clase: 'campos' },
          el('label', { clase: 'campo' }, el('span', { clase: 'etiqueta' }, 'Tipo'), tipo),
          el('label', { clase: 'campo' }, el('span', { clase: 'etiqueta' }, 'Nombre visible'), nombre),
          el('label', { clase: 'campo' }, el('span', { clase: 'etiqueta' }, 'Corresponde a'), vinculo)),
        el('label', { clase: 'fila' }, leer, ' El asistente puede leerlo («Mi CV» siempre se puede leer)'),
        el('div', { clase: 'acciones' }, el('button', { onclick: guardar }, 'Guardar'))),
      el('aside', {})));
  }
  return cuerpo;
}

async function ajustes() {
  const dato = await pedir('/api/ajustes');
  const navegador = el('select', { 'aria-label': 'Navegador' }, Object.keys(dato.disponibles).map((nombre) => el('option', { value: nombre, ...(nombre === dato.navegador ? { selected: 'selected' } : {}) }, nombre)));
  const guardarNavegador = accion(async () => { await pedir('/api/navegador', { navegador: navegador.value }); avisar('Se usará la próxima vez que se abra.'); });
  const sitio = el('input', { placeholder: 'Sitio, como computrabajo.com', 'aria-label': 'Sitio' });
  const nivel = el('select', { 'aria-label': 'Nivel' }, dato.niveles.map((v) => el('option', { value: v, ...(v === dato.nivel_por_defecto ? { selected: 'selected' } : {}) }, v)));
  const guardarNivel = accion(async () => { await pedir('/api/politica', { sitio: sitio.value, nivel: nivel.value }); avisar('Nivel guardado.'); mostrar(); });
  const b = dato.busqueda;
  const nombresModalidad = { remoto: 'Remoto', hibrido: 'Híbrido', presencial: 'Presencial' };
  const nombresIdioma = { es: 'Español', en: 'Inglés', pt: 'Portugués', fr: 'Francés' };
  const casillas = (opciones, marcadas, nombres, etiqueta) => el('fieldset', { clase: 'fila' }, el('legend', {}, etiqueta),
    opciones.map((valor) => el('label', {}, el('input', { type: 'checkbox', value: valor, ...(marcadas.includes(valor) ? { checked: 'checked' } : {}) }), ' ' + nombres[valor])));
  const texto = (valor, etiqueta, ayuda) => el('input', { value: valor, 'aria-label': etiqueta, placeholder: ayuda, size: 50 });
  const antiguedad = el('select', { 'aria-label': 'Antigüedad máxima' }, Object.entries(dato.antiguedades).map(([horas, nombre]) => el('option', { value: horas, ...(Number(horas) === b.antiguedad_horas ? { selected: 'selected' } : {}) }, nombre)));
  if (!(b.antiguedad_horas in dato.antiguedades)) antiguedad.append(el('option', { value: b.antiguedad_horas, selected: 'selected' }, b.antiguedad_horas + ' horas'));
  const modalidades = casillas(dato.modalidades, b.modalidades, nombresModalidad, 'Modalidad');
  const idiomas = casillas(dato.idiomas, b.idiomas, nombresIdioma, 'Idiomas de las ofertas');
  const ubicaciones = texto(b.ubicaciones.join(', '), 'Ubicaciones', 'Colombia, Bogotá');
  const cargos = texto(b.cargos.join(', '), 'Cargos', 'abogada, asesora jurídica, litigante');
  const excluir = texto(b.excluir.join(', '), 'Excluir', 'ventas puerta a puerta');
  const salario = texto(b.salario_minimo, 'Salario mínimo', 'COP 3.500.000');
  const marcadas = (grupo) => [...grupo.querySelectorAll('input:checked')].map((casilla) => casilla.value);
  const guardarBusqueda = accion(async () => {
    await pedir('/api/busqueda', { antiguedad_horas: antiguedad.value, modalidades: marcadas(modalidades), idiomas: marcadas(idiomas),
      ubicaciones: ubicaciones.value, cargos: cargos.value, excluir: excluir.value, salario_minimo: salario.value });
    avisar('Preferencias de búsqueda guardadas.'); mostrar();
  });
  const campo = (etiqueta, control) => el('label', { clase: 'campo' }, etiqueta + ' ', control);
  return [
    el('h2', {}, 'Qué ofertas buscar'),
    el('p', { clase: 'nota' }, 'El asistente usa esto en cada búsqueda. Solo tú puedes cambiarlo. Separa varios valores con comas.'),
    campo('Publicadas en:', antiguedad), modalidades,
    campo('Ubicaciones:', ubicaciones), campo('Cargos o palabras:', cargos), campo('Descartar si dice:', excluir),
    campo('Salario mínimo:', salario), idiomas,
    el('div', { clase: 'fila' }, el('button', { onclick: guardarBusqueda }, 'Guardar preferencias')),
    el('h2', {}, 'Navegador del asistente'), el('div', { clase: 'fila' }, navegador, el('button', { onclick: guardarNavegador }, 'Guardar')),
    el('p', { clase: 'nota' }, dato.activo ? 'Abierto ahora: ' + dato.activo : 'Cerrado.'),
    el('h2', {}, 'Autonomía por sitio'),
    el('p', { clase: 'nota' }, 'Tope de este equipo: ' + dato.nivel_maximo + (dato.estricto ? '. El asistente rellena y el envío lo haces tú.' : '.') + ' Por defecto: ' + dato.nivel_por_defecto + '.'),
    dato.politicas.length ? tabla([['Sitio', (f) => f.sitio], ['Nivel', (f) => f.nivel], ['Aviso', (f) => f.advertencia || '—']], dato.politicas) : null,
    el('div', { clase: 'fila' }, sitio, nivel, el('button', { onclick: guardarNivel }, 'Guardar')),
  ];
}

const vistas = { mesa, comprobante, cv: mesaCv, perfil: perfilVista, documentos: documentosVista, vivo, informes, resumen, postulaciones, seguimientos, ajustes };
const actual = () => (vistas[location.hash.slice(1)] ? location.hash.slice(1) : 'mesa');

async function pintarOlvidadas() {
  const nodo = document.getElementById('olvidadas');
  const lista = await pedir('/api/olvidadas');
  nodo.replaceChildren(...lista.map((item) => el('section', { clase: 'olvidada', role: 'region', 'aria-label': 'Postulación sin resolver' },
    el('p', {}, el('strong', {}, '¿Enviaste la postulación a ' + item.cargo + ' en ' + item.empresa + '?'), ' Mientras no la resuelvas, el asistente no puede seguir.'),
    botonesEnvio(item, mostrar))));
  nodo.hidden = !lista.length;
}

async function mostrar() {
  const nombre = actual();
  document.querySelectorAll('.pestanas a').forEach((enlaceNav) => { if (enlaceNav.dataset.vista === nombre) enlaceNav.setAttribute('aria-current', 'page'); else enlaceNav.removeAttribute('aria-current'); });
  try { vista.replaceChildren(...(await vistas[nombre]()).flat().filter(Boolean)); } catch (error) { vista.replaceChildren(vacio(error.message)); }
  contar().catch(() => {});
}

async function contar() {
  const [lista, seguir, hojas, docs] = await Promise.all([pedir('/api/postulaciones?estado=rellenada,reportada'), pedir('/api/seguimientos'), pedir('/api/cv'), pedir('/api/documentos')]);
  document.getElementById('cuenta-cv').textContent = hojas.pendientes || '';
  document.getElementById('cuenta-lista').textContent = lista.length || '';
  document.getElementById('cuenta-seguir').textContent = seguir.length || '';
  document.getElementById('cuenta-docs').textContent = docs.documentos.filter((d) => !d.tipo).length || '';
  await pintarOlvidadas();
}

async function refrescar() {
  // Nunca reconstruye la vista si nada cambió: se perderían el foco, el desplazamiento y lo que se está escribiendo.
  const nodo = document.getElementById('desconectado');
  try {
    if (actual() === 'mesa' && JSON.stringify(await pedir('/api/postulaciones?estado=rellenada,reportada')) !== huellaMesa) await mostrar();
    else if (actual() === 'vivo') await pintarVivo();
    await contar();
    nodo.hidden = true;
  } catch (error) { nodo.hidden = false; }
}

async function iniciar() {
  const hoy = new Date();
  document.getElementById('fecha').textContent = hoy.toLocaleDateString('es-CO', { dateStyle: 'long' });
  document.getElementById('numero-expediente').textContent = 'EXP-' + hoy.getFullYear() + '-' + String(hoy.getMonth() + 1).padStart(2, '0') + String(hoy.getDate()).padStart(2, '0');
  token = (await pedir('/api/sesion')).token;
  estricto = (await pedir('/api/ajustes')).estricto;
  document.querySelector('.saltar').addEventListener('click', (evento) => { evento.preventDefault(); vista.focus(); });
  window.addEventListener('hashchange', async () => { await mostrar(); vista.focus(); });
  await mostrar();
  setInterval(refrescar, 5000);
}
iniciar();
