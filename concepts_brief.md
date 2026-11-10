# Postulador para profesionales de cualquier carrera

* **Autor:** ExoDoxa
* **Fecha:** 2026-11-09 (dos rondas de revisión). Actualizado el 2026-11-10: carpeta de arranque y datos movibles ya hechos, y alcance del piloto decidido (P1 a P10). Diseño del piloto: [docs/designs/piloto_abogada.md](docs/designs/piloto_abogada.md), revisado con EGM el 2026-11-10 (decisiones A a G en D19).

## Resumen

Postulador hoy es una herramienta que solo su autor puede operar, pensada para su propia búsqueda de empleo en tecnología. La meta es que la usen profesionales no técnicos de otras carreras. Los primeros serían familiares y amigos del autor: una abogada, médicos y una administradora de empresas con cargo público. Todos pagan ya Claude o ChatGPT.

Cómo se usaría:

1. La persona abre la **app de escritorio oficial de su IA** (Claude, pestaña Code, o Codex) sobre una carpeta preparada para ella.
2. **Conversa ahí.** La IA le hace una entrevista adaptada a su carrera que parte de su CV y pregunta solo lo que falta. También le pide datos que faltan, le avisa de captchas e inicios de sesión y le indica cuándo aprobar algo.
3. **Todo lo demás lo ve en el panel**, en una ventana que la IA no controla:
   - su perfil, con campos propios de su carrera (RETHUS, tarjeta profesional, especialidad);
   - su carpeta de certificados y diplomas;
   - sus CV;
   - un tablero de postulaciones que se abre al empezar a buscar y se actualiza mientras la IA trabaja.
4. **La IA busca ofertas y rellena formularios** en un navegador visible, a través de la puerta de envío. La puerta es el filtro que se interpone entre la IA y el navegador y decide qué acciones pasan. Nada se envía sin la aprobación de la persona. La IA nunca paga ni firma declaraciones juradas.

Lo que la persona gana: deja de adaptar su CV para cada oferta, de llenar formularios repetidos y de buscar a mano, sin perder el control de lo que se envía con su nombre.

## Registro de decisiones

| # | Decisión | Estado |
|---|---|---|
| D1 | Construir sobre el repositorio Postulador, no desde cero | Decidida |
| D2 | Nada de terminal ni comandos a la vista | Decidida |
| D3 | La persona trabaja en la app de escritorio oficial de Claude (Code) o de Codex. Se descartan VS Code y una app propia con instalador. Gemini queda fuera porque no tiene ese camino. | Decidida. Paso 0 aprobado para Claude en modo Code con la sesión creada en la carpeta de arranque. Codex queda para después del piloto (D17). |
| D4 | Cada persona usa su propia suscripción. Se acepta sin verificar el riesgo de los términos de uso. | Decidida |
| D5 | Entrevista por carrera que parte del CV y pregunta solo lo que falta | Decidida |
| D6 | Perfil veraz que aprueba la persona, con campos propios de cada carrera | Decidida |
| D7 | Carpeta local de certificados y diplomas, fuera de OneDrive, fácil de exportar | Decidida |
| D8 | El navegador por MCP y las skills actuales se mantienen | Decidida |
| D9 | Aprobación antes de cada envío. La puerta de envío se arregla. | Decidida. En el piloto la aprobación es el clic final de la persona (`solo_rellenar`, ver D17). La huella y la cola de aprobaciones quedan para después. |
| D10 | La IA nunca paga ni firma declaraciones juradas, en ningún canal | Decidida |
| D11 | CNSC/SIMO: la app propone, la persona decide si participa y la app puede llenar la inscripción | Decidida, con el tope de D10 |
| D12 | Correo dedicado a la búsqueda de empleo, avisado desde el inicio. Se puede leer completo. | Decidida. En el piloto nadie lo lee: la persona marca las respuestas en el tablero. El lector en código llega después. |
| D14 | Preferencias de búsqueda configurables por cada persona: antigüedad máxima de las ofertas (24 h, 3 días, una semana…), modalidad (remoto, híbrido, presencial), ciudades, cargos o palabras clave, salario mínimo e idioma. Se editan en el panel y la IA las lee al empezar; hoy la rutina fija «24–48 horas». | Decidida e **implementada el 10 nov**: módulo `busqueda.py`, sección «Qué ofertas buscar» en Ajustes, herramientas `busqueda_preferencias` (solo lectura) y `linkedin_url`. La puerta además abre siempre una pestaña propia. Probado en vivo. |
| D13 | Tablero que se abre al empezar a buscar. La fuente es la base de datos y el `.md` es solo una exportación generada por el código. Queda fuera del alcance de la IA. | Decidida |
| D15 | Carpeta de arranque `C:\Users\<persona>\Postulador`, generada con `python -m postulador arranque`. La sesión de Claude se crea en esa carpeta, y el repositorio queda solo para programar. | Decidida e **implementada el 10 nov** (`arranque.py`) |
| D16 | Un solo lugar de datos, el que indique `%LOCALAPPDATA%\Postulador\ubicacion.json`, validado con una marca de identidad. Se mueve con `python -m postulador datos --mover`. Los del autor están en `<USB>\Postulador\datos`. | Decidida e **implementada el 10 nov** (`ubicacion.py`) |
| D17 | **Piloto con una sola persona**, la hermana del autor (abogada). Solo Claude, sin ejecuciones programadas, sin `enviar_solo` y en `solo_rellenar`: la IA rellena y ella hace el clic final. El autor instala en una visita y actualiza con `git pull` más `python -m postulador arranque`. | Decidida el 10 nov |
| D18 | Conectores de la cuenta: en la instalación se desactivan en la configuración de claude.ai de la persona. Además, la skill revisa sus herramientas al empezar y se niega a trabajar si ve alguna que maneje un navegador fuera de la puerta, incluida cualquier `mcp__claude_ai_*`. | Decidida el 10 nov. La revisión de herramientas es una instrucción; lo que bloquea son los conectores desactivados, las denegaciones y `diagnostico` |
| D19 | Decisiones de la revisión EGM del diseño del piloto: **A.** un candado global de solo lectura guardado en la base, mientras alguna postulación espera que ella la envíe (la IA no sigue con otra oferta hasta entonces), y una tabla de quién cambia cada estado, con el estado nuevo `reportada`; **B.** un solo perfil con sello de revisión; **C.** con un formulario a medio rellenar, la puerta bloquea todo botón salvo una lista segura por sitio, y ella mide con «Ya estaba enviada cuando la vi»; **D.** se quita `plantilla_guardar` en el piloto; **E.** el tope vive en `%LOCALAPPDATA%\Postulador\equipo.json` y falla cerrado a `solo_rellenar`; **F.** se aplaza `doc:<id>`: la IA solo sube el CV; **G.** orden A0, A1 común, B, A2 formularios, C. | Decidida el 10 nov |

## Forma propuesta

### Cuatro carpetas

Hoy la carpeta que se abre es el propio código, y los datos viven dentro de él, en OneDrive. Cuatro revisores proponen separarlo así:

| Carpeta | Qué contiene | Quién escribe |
|---|---|---|
| Instalación | Código, skills, puerta | Nadie durante el uso. La IA no puede editarla. |
| Datos (donde indique `%LOCALAPPDATA%\Postulador\ubicacion.json`; los del autor, en `<USB>\Postulador\datos`) | Base de datos, perfil, CV, comprobantes | Solo los procesos de Postulador. La IA solo usa herramientas MCP. |
| Documentos (fuera de OneDrive) | Certificados, diplomas, soportes | El barrido de `entrada/` que hace el código al listar: copia, nunca mueve. |
| Arranque (lo que abre la app de IA; ya existe en `C:\Users\<persona>\Postulador`) | Instrucciones (CLAUDE.md/AGENTS.md), `.mcp.json` con rutas absolutas, permisos y una carpeta `entrada/` donde la persona deja archivos | Nadie durante el uso |

Con esa separación, el encierro de la IA se reduce a una regla fácil de comprobar: «sin comandos, sin editar archivos, sin escribir; solo herramientas de Postulador».

Ojo: en Windows 11 el Escritorio suele estar dentro de OneDrive, como en el equipo del autor.

### Quién es dueño de cada dato

| Dato | Dueño |
|---|---|
| Datos del perfil | La IA escribe en el perfil, pero no se generan CV ni cartas hasta que la persona lo revise: «Revisado» en el panel deja un sello, y cualquier cambio posterior de la IA lo invalida. En los formularios el control es el comprobante más el clic de ella (D6 en versión mínima, piloto, D19-B). Los campos sensibles solo los escribe ella. |
| Vínculo entre un documento y un dato del perfil | La persona lo fija en el panel (piloto). |
| Aprobaciones | La puerta las crea, la persona decide en una ventana que la IA no controla y la puerta las consume. |
| «Enviada» | En el piloto (`solo_rellenar`) la puerta no ve el envío: la IA lo reporta con el estado `reportada` y la persona lo confirma en el tablero. Solo las que están en `enviada` cuentan y generan seguimientos. Las respuestas y los seguimientos hechos los marca solo ella (D19-A). El comprobante de la puerta registra lo que rellenó el asistente. |
| «Respondió» | El lector de correo o la persona. |
| Tiempo de cada postulación | Las horas que registra la puerta. |
| Qué se respondió en cada formulario | El comprobante de la puerta. |
| Nivel de autonomía y navegador | El autor fija un tope en `%LOCALAPPDATA%\Postulador\equipo.json`, que solo escribe `arranque` y que, si falta o está dañado, vale `solo_rellenar` (D19-E). Por debajo del tope, la persona en el panel. |

Nivel de autonomía es lo que la IA puede hacer en cada sitio sin preguntar. Hoy hay cuatro valores, ninguno definido todavía en el brief:
- `solo_preparar`: no rellena nada;
- `solo_rellenar`: rellena, pero la persona hace el clic final;
- `aprobar`: rellena y envía con aprobación;
- `enviar_solo`: envía sin preguntar.

### El panel

- **Arranca solo.** Una sola instancia, que la persona abre desde un acceso directo o que se abre sola al arrancar el navegador. Funciona aunque no haya ninguna IA abierta. Corrección del 10 nov: el panel ya corre como proceso aparte que sobrevive al chat y se reutiliza si el puerto 8770 está ocupado (`panel.asegurar`). En el piloto se suma un acceso directo «Panel de Postulador».
- **Se abre fuera del alcance de la IA.** Cuando la puerta abre el navegador de la IA, abre antes el panel en el navegador normal de la persona.
- **Clave de un solo uso.** La clave del panel pasa en la dirección como secreto de un solo uso y se convierte en una cookie. Nunca se entrega por HTTP ni se guarda en disco.
- **Lo que ya existe y lo que falta.** La actualización en vivo ya existe (consulta cada 5 s); falta el resumen del tablero. Las pestañas actuales sirven de base: Postulaciones, Seguimientos, Resultados y la que hoy se llama «Por firmar».
- **Lo que se quita:** la pestaña Agente, «Conectar» y «Pedir al agente». Lanzan una IA oculta, abren la terminal y conservan la trampa del cobro por uso.

## Análisis

### Hallazgo más grave: la IA puede aprobarse sola (comprobado en el código)

Pasa hoy, en la versión del autor. Quitar `politica_fijar` y `navegador_elegir` no lo arregla. La IA puede:

1. navegar con su propio navegador a `127.0.0.1:8770`, porque la puerta no revisa `browser_navigate` (`puerta.py:40-54`);
2. pulsar «Aprobar envío». La expresión que detecta envíos (`puerta.py:12`) reconoce «enviar» y «envía», pero no «envío», así que el clic no cuenta como envío;
3. aprobar sin problemas, porque el panel le entrega su clave a cualquier petición local (`panel.py:71`);
4. volver al portal y enviar con la aprobación que acaba de crear.

Por la misma vía llega a Ajustes y puede poner una política que deje enviar sin preguntar en todos los sitios.

**Arreglo obligatorio, no opcional:** el navegador de la IA no puede abrir el panel, otras direcciones locales ni los esquemas `file:`, `data:`, `javascript:` y `chrome:`.

### La puerta deja pasar lo que no conoce

- **Herramientas no vigiladas.** Toda herramienta que la puerta no revisa pasa tal cual: navegar, cambiar de pestaña, aceptar diálogos de «¿confirmar envío?», teclas distintas de Enter, clics por coordenadas, y cualquier herramienta nueva de una versión futura de Playwright.
- **Código en la página.** `browser_evaluate` con `fetch(...)`, `requestSubmit()` o asignación de valores pasa, porque solo se buscan «click», «submit» y similares.
- **Botones sin texto.** Un clic en un botón con solo icono pasa.
- **Subida de archivos.** `browser_file_upload` acepta cualquier ruta: la IA podría subir la base de datos o una cédula escaneada a cualquier sitio.
- **La categoría «nunca».** Una declaración jurada es una casilla, no un botón de envío. Pagos y declaraciones necesitan su propia categoría «nunca», que ninguna aprobación desbloquea:
  - dominios de pago bloqueados, también dentro de marcos (frames);
  - casillas con «juramento», «declaro bajo» o «pagar» bloqueadas;
  - los pasos finales de SIMO pasan a la persona.

  Esta revisión tiene que ir antes del atajo de `enviar_solo`, que hoy salta todos los controles (`puerta.py:59`).

**Arreglo:**
- solo pasan las herramientas de una lista fija, ligada a la versión de Playwright MCP;
- la IA no puede ejecutar código en la página;
- se sube por identificador de documento, solo desde las carpetas de CV y documentos.

### La aprobación no está atada a lo que se envía

- La aprobación la pide la IA, no la puerta, y la persona aprueba un texto que escribió la IA.
- Se consume por dominio y toma la más antigua (`aprobaciones.py:48-54`).
- La puerta lleva un solo estado para todas las pestañas.
- Hay dos errores de borde:
  - si el clic falla pero el portal sí envió, la aprobación vuelve a quedar disponible;
  - si falla la llamada después de consumirla, se pierde.

**Diseño propuesto:** una «transacción de postulación» por pestaña, que abre la propia puerta.
1. La puerta registra cada escritura.
2. En la página final, la puerta misma lee los valores, incluidos los que el portal rellenó por su cuenta, y toma una captura.
3. Calcula una huella de la dirección, las preguntas con sus respuestas y los archivos subidos.
4. La aprobación guarda esa huella. Al enviar, la puerta vuelve a leer: si no coincide, no se envía.
5. Una pregunta que aparece después pide una aprobación pequeña, solo para lo nuevo.

Sin definir todavía: formularios de varios pasos, marcos de otro dominio (Greenhouse dentro de la página de la empresa) y direcciones que cambian en cada sesión (Workday, SIMO).

### El encierro de la IA nadie lo ha comprobado (todo esto está SIN VERIFICAR)

**Por qué es urgente.** El modo actual sin ventana encierra a la IA con opciones de arranque: `--strict-mcp-config --allowedTools=...` en Claude y `--sandbox read-only` en Codex. Las apps de escritorio no aceptan esas opciones, así que toda la seguridad pasa a depender de archivos de permisos del proyecto. Esos archivos todavía no existen.

**Lo que hay que averiguar:**
- si la pestaña Code y la app de Codex cargan el `.mcp.json`, las skills y las reglas de denegación del proyecto;
- si la persona puede saltarse una denegación con un clic o con un modo de «aprobar siempre»;
- si el sandbox de Codex se puede fijar por proyecto;
- si los servidores MCP corren dentro de ese sandbox. Si es así, Word y la base de datos dejarían de funcionar.

**Reglas que se proponen:**
- **«Denegar», nunca «preguntar».** Una persona no técnica pulsa «Permitir». Una oferta maliciosa que haga a la IA pedir un comando le gana a la puerta a través de la persona.
- **Conectores de la cuenta.** Los de claude.ai aparecen en las sesiones de código; en esta misma sesión del autor se cargaron TinyFish y otros. Cualquier otra herramienta de navegador, o funciones como «Claude in Chrome», se saltan la puerta por completo. Hay que desactivarlos.
- **Qué se deniega.** Toda la carpeta de instalación, `.mcp.json`, `.claude/**`, la configuración de Codex, AGENTS.md/CLAUDE.md y `skills/`. Si no, la IA podría dejar un `json.py` falso que la puerta cargaría en el siguiente arranque.
- **Otra forma de aprobar.** `python -m postulador aprobar ID` aprueba desde la línea de comandos. Con los comandos denegados deja de ser un riesgo; si no, hay que quitarlo.

### El correo dedicado abre dos riesgos nuevos

- **Tomar cuentas.** Es el correo de recuperación de cada portal, SIMO incluido. Si la IA lee los códigos, puede restablecer contraseñas.
- **Instrucciones escondidas.** La dirección sale en cada CV, así que cualquiera puede escribir un correo con instrucciones para la IA. Un enlace de «Confirmar» enviado por correo puede completar una postulación sin pasar por la puerta. Además, lo que la IA guarda en sus notas se le vuelve a mostrar en cada sesión.

**Arreglo:**
- un lector de correo hecho en código, de solo lectura, con una credencial que la IA nunca ve;
- ese lector entrega a la IA solo datos ordenados (remitente, tipo, postulación, fecha límite), nunca el HTML ni los enlaces;
- los códigos van a la persona, o la puerta los escribe solo en un inicio de sesión que la persona empezó, en el sitio que envió el código;
- el correo web queda bloqueado en el navegador de la IA.

### El tablero mostraría lo que la IA dice, no lo que pasó

- **La IA escribe lo que se cuenta.** Hoy ella misma escribe los estados que contaría el tablero (`postulacion_actualizar` puede marcar «enviada»). La meta de «0 envíos sin aprobación» dependería de su palabra.
- **Faltan datos:**
  - la hora de inicio se registra después de rellenar;
  - la fecha de envío no tiene hora;
  - una aprobación no se vincula con su postulación;
  - el registro de actividad se recorta a 60 líneas;
  - `respuestas` es un banco global de preguntas y respuestas que se sobrescribe.

**Arreglo:**
- «Enviada», el tiempo y las respuestas salen solo de los comprobantes de la puerta, guardados en una tabla a la que solo se añaden filas;
- lo que informa la IA se muestra como «reportado por la IA», distinto de «verificado»;
- el banco de respuestas reutilizables y las respuestas de cada postulación llevan nombres distintos.

### Documentos

- **Cómo se archivan.** «La IA archiva documentos» choca con prohibirle editar archivos. Decidido el 10 nov para el piloto: un barrido automático del código revisa `entrada/` y:
  - copia sin mover;
  - pone nombres elegidos por el código;
  - registra el archivo en una tabla.

  La persona clasifica (tipo y nombre) y fija el vínculo con un dato del perfil en el panel. No hay herramienta `documento_archivar`.

  El árbol de carpetas legible es una exportación.
- **Menos datos al modelo.** La IA no clasifica documentos: lo hace la persona en el panel (P7). La IA solo lee un documento si la persona lo permite («Mi CV» viene permitido), y el código tapa la cédula antes de entregar el texto. Al subir un documento a un portal, el contenido no pasa por la IA.
- **Faltan piezas:**
  - la formación del perfil no tiene identificador, así que un diploma no se puede vincular;
  - no hay `schema_version`;
  - los campos propios de una carrera ya se guardan, pero nada los muestra, ni el CV ni el panel.

  Hace falta un esquema de «paquete de carrera»: campo, tipo, validación, canal que lo exige, si necesita soporte y si es sensible.
- **Generar CV con la IA encerrada** sigue funcionando: corre dentro del servidor MCP. Pero `plantilla_guardar` guarda HTML escrito por la IA que se renderiza con JavaScript y red activos. Hay que renderizar sin scripts. *En el piloto se quita `plantilla_guardar` (D19-D).*

### Lo que una persona no técnica no va a entender

- **Dos «aprobar».** La app de IA muestra «Permitir» para herramientas y el panel muestra «Aprobar». La persona puede creer que ya aprobó el envío. Escribir «sí, envíala» en el chat no prueba nada. Regla: en uso normal no aparecen permisos en el chat, y la IA siempre dice «aprueba en el panel, pestaña ___».
- **Aprobar no envía.** Si el turno del chat terminó, después de aprobar no pasa nada, y las aprobaciones vencen a las 24 h. El panel debe decir «Aprobada, falta enviar: escribe *continúa* en el chat».
- **Tres ventanas** (chat, navegador de la IA, panel) sin indicar cuál la necesita. Cada relevo nombra la ventana y la acción.
- **«Firmar» tiene peso legal** para una abogada. Se cambia «Por firmar» por «Por aprobar», y cada tarjeta dice «esto no firma ninguna declaración».
- **La puerta aparece como `playwright`.** Está registrada con ese nombre, así que la persona aprueba «playwright» sin saber que es el filtro de seguridad.
- **«Tablero» ya significa otra cosa** en el código: bolsas de empleo (`tableros.json`).
- **Cuando algo falla, la IA ofrecerá comandos.** La skill debe prohibirlo y dar instrucciones en español o «avísale a [autor]».
- **Navegador sin sesiones.** El perfil del navegador empieza vacío, así que hay que iniciar sesión en cada portal y en el correo. Google podría negarse a iniciar sesión en un navegador con puerto de control (sin verificar).
- **Cupo de la suscripción.** Cada acción del navegador envía a la IA una lectura de la página de unos 5.000 a 30.000 tokens (estimación de los revisores), y una postulación lleva de 20 a 60 acciones. Un plan Pro podría agotarse con pocas postulaciones y dejar a la persona sin cupo para su trabajo. Salidas: rellenar con mapas de campos por sitio, sin IA, y un contador de consumo en el panel.

### Qué cambió respecto de la primera ronda

- **Se resuelve:**
  - la falta de conversación: el chat oficial se encarga;
  - el instalador por firmar;
  - la privacidad del correo personal.
- **Empeora:**
  - las formas de saltarse la puerta: ahora están los comandos, la edición de archivos y los conectores de la app, y se pierden las opciones de encierro del modo sin ventana;
  - sigue haciendo falta Python, Node y npx, ahora con avisos de permisos en inglés.
- **Sigue igual:**
  - la veracidad depende de instrucciones (`perfil_guardar` acepta cualquier cosa);
  - el CV de una página (`cv.py:185`);
  - publicaciones y proyectos obligatorios (`perfil.py:7-8`);
  - la búsqueda limitada a Greenhouse, Lever y Ashby;
  - el cupo agotado a mitad de formulario.

**Riesgos de la primera ronda que siguen vigentes:**

- **Veracidad.** La IA solo escribe borradores. Cada dato guarda su origen y un verificador revisa los textos libres. Los títulos regulados se copian tal cual: «especialista» no es «residente», ni «abogado» es «egresado no graduado».
- **Canales de estas carreras.** Ninguno está cubierto:
  - CNSC/SIMO, SIGEP II, Servicio Público de Empleo;
  - Computrabajo, elempleo;
  - páginas de hospitales, firmas de abogados, SECOP II.

  CNSC/SIMO es otro proceso: ventanas de inscripción, una oferta (OPEC) por concurso, pago por PSE, documentos y declaraciones.
- **Formato del CV.** Estos CV suelen tener varias páginas y SIGEP usa un formato oficial fijo. Los puntajes ATS e idoneidad no sirven aquí y pueden quitarle confianza a un profesional calificado.
- **Ley 1581.** Los datos sensibles (etnia, discapacidad, víctima) los escribe solo la persona. La frase «tus datos no salen de tu equipo» hay que corregirla: el perfil, las páginas y ahora los documentos escaneados llegan a la empresa de IA.

### Contradicciones y cómo resolverlas sin ceder

**Resultado ideal:** la IA solo propone, y rellena en los sitios que la persona permitió. Todo efecto que no se puede deshacer pasa por código y se activa con un gesto humano, en una ventana que la IA no maneja. Eso incluye enviar, aprobar, cambiar políticas, pagar, firmar y subir datos personales.

| Contradicción | Resolución |
|---|---|
| La app de IA tiene que ser capaz, pero sin comandos | Se le quitan todas las herramientas generales (comandos, edición, escritura, lectura web). Cada capacidad es una herramienta estrecha de Postulador. |
| La IA archiva documentos y escribe CV, pero no puede escribir archivos | El código escribe: barrido automático de `entrada/` y `cv_generar`. |
| El tablero se actualiza con la IA, pero está fuera de su alcance | Muestra lo que vio la puerta, no lo que dijo la IA: «verificado» frente a «reportado». |
| Aprobación exacta, pero formularios de varios pasos | Huella acumulada por postulación más aprobaciones pequeñas para lo que aparezca después. |
| La IA debe leer códigos, pero el buzón es una vía de ataque | El correo lo lee el código, y los códigos no entran en el contexto de la IA. |
| Bloquear ante la duda, pero no inundar a la persona de aprobaciones | La primera postulación en cada portal va en `solo_rellenar`: la persona hace el clic final y la puerta aprende cuál es el botón que envía. |
| Nunca pagar ni firmar, pero la IA llena SIMO | Se separa por dominio y por paso, no por texto del botón. Los pasos finales de SIMO los hace la persona. |
| Clasificar documentos sin enviar la cédula al modelo | Se sube por identificador, el modelo ve texto con la cédula tapada y los escaneos los clasifica la persona. |

### Prueba en vivo del 9 nov (Brave del autor, a través de la puerta nueva)

- **Funciona:** con la sesión ya iniciada, la búsqueda en LinkedIn de las últimas 24 horas en Colombia encontró ofertas en las cuatro áreas del perfil: asistente virtual, QA, IA y psicología. La puerta dejó leer y pulsar tarjetas, porque no son envíos.
- **LinkedIn cambió su diseño.** `/jobs/search/` redirige a `/jobs/search-results/` y en la redirección:
  - se pierden la ubicación escrita y el filtro de remoto (`f_WT`); el país solo se conserva con `geoId`;
  - se añade un filtro de salario (`f_SAL`) que parece salir de una preferencia guardada en la cuenta.

  Las ofertas son botones con el texto «Descartar empleo «cargo»». El enlace de cada una solo aparece al seleccionarla, y al recorrerlas varias seguidas la dirección no siempre se actualiza. Por eso la mitad de los enlaces quedaron sin confirmar.
- **Consecuencia:** la búsqueda conviene hacerla con código determinista por portal: dirección con filtros, lectura de tarjetas y enlace por oferta, con las preferencias de D14. La IA quedaría para leer la oferta completa y evaluar si encaja. Así gasta menos cupo y no depende de cómo la IA interprete cada diseño nuevo. Hay que actualizar la guía de LinkedIn de la skill.

### Paso 0: resultados (10 nov, con Claude Code 2.1.89 por terminal)

La pestaña Code de la app de escritorio usa el mismo motor y los mismos archivos del proyecto (`.mcp.json`, skills, `.claude/settings.json`). No se pudo manejar la ventana, porque esta sesión no tiene control del escritorio, así que **los avisos, su idioma y los clics siguen sin verificar**. Las pruebas se hicieron en una copia del repositorio.

| Punto | Resultado |
|---|---|
| Sin configuración (lo que vería una persona nueva) | Carga Postulador (32 herramientas) y la skill. **También carga** comandos, edición, lectura web, un segundo Playwright (`plugin:playwright`) y los conectores de la cuenta (TinyFish, Gmail, Drive…). |
| Reglas `deny` en `.claude/settings.json` | **Funcionan:** comandos, edición, escritura y lectura web desaparecen de la lista de herramientas, no solo piden permiso. Las herramientas de Postulador y de la puerta siguen funcionando. |
| Desactivar conectores con `env.ENABLE_CLAUDEAI_MCP_SERVERS=false` | **No es confiable:** en una sesión desaparecieron y en otra volvieron. Hace falta otro mecanismo. Además, los conectores de cada persona son distintos, así que no se pueden denegar por nombre. Sin resolver. |
| La IA intenta abrir el panel con la puerta | **Bloqueado.** Un formulario externo sí se abre. |
| Modo «permitir todo» (`--dangerously-skip-permissions`) frente a las reglas `deny` | **Sin probar:** la sesión de pruebas no permitió lanzar otra IA en ese modo. El archivo incluye `disableBypassPermissionsMode: disable`. |
| La puerta tarda en registrarse | En sesiones cortas la IA busca las herramientas del navegador antes de que estén listas. Hay que pedirle en la skill que espere y vuelva a buscarlas. |
| **La IA navega en la pestaña activa del usuario** | Hallazgo nuevo: Playwright usa la pestaña seleccionada, aunque sea del usuario. La skill pide pestañas propias, pero el código no lo impone. La puerta debería abrir siempre una pestaña propia y no actuar sobre las demás. |
| App de escritorio, **chat normal o Cowork con acceso a la carpeta** (prueba del autor, 10 nov) | **No carga nada del proyecto:** ni `.mcp.json` (no aparecen `postulador` ni la puerta) ni los permisos. Trae sus propias herramientas: `device_bash` (`echo hola` funcionó), `claude-in-chrome`, navegador integrado (`Claude_Browser`), TinyFish, Drive y otros. **En ese modo la puerta no existe.** El producto tiene que impedir o detectar que se use así: por ejemplo, que la skill se niegue a postular si no ve las herramientas de la puerta, y que el panel lo explique. Falta probar la pestaña Code. |
| App de escritorio, **modo Code** (prueba del autor, 10 nov) | La sesión arranca en la carpeta personal (`C:\Users\<autor>`) si no se elige otra al crearla. **Decirle en el chat «trabaja en esta carpeta» no carga `.mcp.json` ni los permisos**: faltaban `postulador` y la puerta, y PowerShell y Bash funcionaron. La app suma servidores propios que se saltarían la puerta: `Claude_Browser` (incluye `javascript_tool`), `claude-in-chrome` (el Chrome real), `computer-use` (control del escritorio) y `terminal` (`run_in_terminal`). Hay que denegarlos por nombre; ya están en el `settings.json` de prueba. La IA se negó por su cuenta a usar navegadores sin la puerta, y eso tiene que quedar como regla de la skill. **Falta probar la sesión abierta en la carpeta desde que se crea.** Por terminal, el mismo motor sí respeta las denegaciones. |
| **App de escritorio, modo Code, sesión creada en la carpeta de arranque** (10 nov) | **Funciona**, según confirmó el autor: con la sesión abierta en `C:\Users\<autor>\Postulador`, la app respeta los permisos y Postulador y la puerta trabajan. |
| **Carpeta de arranque implementada** (10 nov) | `python -m postulador arranque` crea `C:\Users\<persona>\Postulador` con `.mcp.json` (ruta absoluta de Python, `PYTHONPATH` y `POSTULADOR_DATOS`), `.claude/settings.json` con las denegaciones, `.codex/config.toml` (solo lectura, sin verificar), instrucciones para la IA y `entrada/`. El repositorio queda libre para programar. Probado con Claude por terminal: comandos, escritura y subagentes bloqueados; la puerta carga, impide abrir el panel y trabaja en una pestaña propia. La IA intentó conseguir comandos lanzando subagentes, así que también se deniegan `Agent` y `Task`. |
| **Datos fuera de OneDrive** (10 nov) | Hay un solo lugar de datos, registrado en `%LOCALAPPDATA%\Postulador\ubicacion.json` y validado con una marca de identidad. `python -m postulador datos --mover` copia los datos, los verifica por huella, revisa la base y deja el original como respaldo. Los datos del autor se movieron a su USB (`<USB>\Postulador\datos`, 107 archivos). Sin la USB, Postulador avisa «conéctala» en lugar de crear una carpeta vacía. Riesgos aceptados: FAT32 sin protección ante cortes y USB sin cifrar (Windows Home). |
| Carrera de tiempos al arrancar | Claude arranca los servidores MCP uno tras otro. En `claude -p`, los que conectan después de empezar la sesión no exponen sus herramientas, y a veces la puerta queda fuera. Afecta las pruebas por terminal; en la app de escritorio las herramientas llegan después. La puerta ahora responde la lista de herramientas al instante (`playwright_herramientas.json`, fijada a la versión de Playwright MCP) para acortar esa ventana. |
| Arranque para personas no técnicas | Elegir la carpeta al crear la sesión no es obvio: el autor no lo encontró en dos intentos. Hace falta un acceso directo que abra la app ya en la carpeta de arranque, o una instrucción de un solo paso con captura de pantalla. |
| Codex | **Sin probar:** el token de la sesión está revocado. Hay que volver a iniciar sesión (`codex login`). Ya está preparado `.codex/config.toml` de prueba (solo lectura y MCP de Postulador). |

## Metas y fuera de alcance

**Metas:** las decisiones D1 a D13, más:
- la puerta de envío arreglada con todo lo de este análisis;
- la IA encerrada en herramientas de Postulador;
- las cuatro carpetas separadas.

**Fuera de alcance:**
- el modelo de difusión rápido;
- Gemini y cualquier IA sin app de escritorio que cumpla el paso 0;
- leer el correo personal o de trabajo;
- un instalador propio y una app de escritorio propia.

**Decidido para el piloto (10 nov):** `enviar_solo`, las ejecuciones programadas y Codex quedan fuera del piloto (D17).

## Alternativas consideradas

**Rechazadas:**
- **Empezar una app nueva desde cero.** Rechazada: Postulador ya resuelve la mayor parte y lo que falta está en sus límites.
- **Operar por comandos en la terminal.** Rechazada por el autor: los usuarios no deben verla.
- **App de escritorio propia con instalador y chat propio.** Rechazada por el autor: se prefiere el chat oficial más el panel. Así no se construye ni mantiene un chat y cada persona usa el cliente oficial.
- **VS Code como entorno.** Rechazada por el autor: la app de escritorio intimida menos.
- **Verificar los términos de uso antes de seguir.** Rechazada por el autor: acepta el riesgo.
- **Índice Markdown que la IA va editando.** Rechazada con acuerdo del autor: duplica o pierde filas. La fuente es la base de datos.
- **Leer el correo personal limitado a una etiqueta.** Rechazada por el autor en favor del correo dedicado.
- **Modelo de difusión rápido para rellenar.** Aparcada. Ataca el cuello de botella equivocado: lo lento son las idas y vueltas, la carga de páginas y las aprobaciones. Además exige una clave de API pagada aparte.
- **Que el autor opere una instalación con un perfil por familiar.** Probablemente inviable: las suscripciones son personales, el autor tendría credenciales ajenas y aplica la Ley 1581.

**Propuestas por los revisores, por decidir:**
1. **`solo_rellenar` en todos lados para el piloto.** La persona hace el clic final de envío, y ese clic es la aprobación, atada exactamente a lo que ve en pantalla. Elimina la cola de aprobaciones, la huella y casi toda la carga de las pruebas de contención. Con el chat como motor, la cola de aprobaciones aporta poco: después de aprobar, el chat igual tiene que seguir vivo para enviar.
2. **Primera versión sin navegador en sitios ajenos y sin buzón.** Incluye entrevista, perfil por carrera, documentos, CV de varias páginas, exportación al formato SIGEP y un tablero con postulaciones marcadas a mano. Elimina Node, los puertos, toda la puerta y el riesgo de agotar el cupo.
3. **La puerta es dueña del navegador.** Playwright corre dentro de la puerta y se comunica por una tubería, sin puertos 8931 ni 9222. Mantiene los mismos nombres de herramientas, así que las skills siguen sirviendo. Es necesario si el objetivo final es detener la petición de red.
4. **Postulador como única capacidad de la IA.** La IA rellena con `formulario_campo(postulación, campo, dato_id)`: señala un dato del perfil y el código escribe el valor literal. Un solo mecanismo resuelve veracidad, huella y comprobante. Los textos libres siguen necesitando verificación.
5. **La IA nunca envía.** Después de la aprobación, el código repite el envío registrado para ese portal.
6. **Solo Claude en el piloto.** Soportar también Codex duplica la configuración, el encierro y el soporte. Se decide después de preguntar qué plan paga cada persona.
7. **Un cliente sin comandos por diseño**, como la pestaña Chat de Claude con un MCP local (sin verificar). El encierro se cumpliría sin configurar nada, pero no hay carpeta de skills.

## Decisiones clave y siguientes pasos

**Orden de trabajo:**

| Paso | Qué | Por qué en este orden |
|---|---|---|
| 0 | **Comprobar las apps de escritorio** (1–2 días, en una cuenta limpia de Windows), con la lista de abajo | La forma del producto, el encierro y las carpetas dependen de esto |
| 1 | **Arreglo urgente de la puerta.** Bloquear el panel y las direcciones locales en el navegador de la IA, lista fija de herramientas, sin código en la página, subidas solo por identificador, categoría «nunca» antes de `enviar_solo`, «envío» como etiqueta de envío, dominio exacto en políticas y en `ENVIO_POR_SITIO`, quitar `politica_fijar` y `navegador_elegir` | **Hecho el 2026-11-09**, con 10 pruebas nuevas (73 en total, todas pasan). Diferencia con lo planeado: las subidas se limitan a las carpetas `cv` y `documentos`, no a un identificador de documento. Queda para el paso 2: el panel sigue entregando su clave por `/api/sesion`, y una IA con comandos podría pedirla. Para el paso 3 quedan los errores de `devolver`/`consumir` y los marcos de otro dominio. |
| 2 | **Cuatro carpetas y encierro de la IA** con «denegar», generado desde una sola fuente, y una comprobación antes de cada sesión | Sin esto, la puerta se puede rodear. **En parte hecho el 10 nov:** carpeta de arranque con denegaciones (D15) y datos fuera del código (D16). Falta: conectores de la cuenta (D18), comprobación antes de cada sesión y la clave del panel por `/api/sesion`. |
| 3 | **Transacción de postulación y comprobantes** (huella, captura, tabla de comprobantes) | Base para aprobar con verdad y para el tablero |
| 4 | **Panel independiente y tablero** («verificado» frente a «reportado», tiempos, respuestas por postulación, «Por aprobar») | Depende de los comprobantes |
| 5 | **Perfil v1 y documentos** (borrador y aprobado, origen de cada dato, identificadores en formación, `schema_version`, paquetes de carrera, `documento_archivar`) | |
| 6 | **Entrevista por carrera y lector de correo en código** | |
| 7 | **Prueba con los familiares** | |

**Comprobación de cada app de escritorio (paso 0):**
1. Qué avisos de confianza y de MCP aparecen, en qué idioma y cuántos clics llevan.
2. Que la lista de herramientas muestre solo Postulador y la puerta: sin conectores de la cuenta, sin control del computador y sin navegador propio.
3. Que una herramienta `diagnostico` devuelva la carpeta, el Python que se usa, la carpeta de datos y la versión.
4. Que la app encuentre la skill y, en Codex, que lea AGENTS.md.
5. Que, sin ningún botón de «Permitir», queden denegados los comandos, la edición de `puerta.py` y `politicas.json`, la lectura web del panel y la lectura de la base. Y que ningún modo ni ajuste de usuario lo anule.
6. Que las herramientas MCP de 90 a 120 s (Word, arranque de Playwright) no se corten.
7. Que se muestren las imágenes que devuelven las herramientas.
8. Que los servidores MCP sobrevivan a un chat nuevo o se reinicien solos.
9. Que el uso se cobre a la suscripción aunque haya una clave de API en el entorno.
10. Solo Codex: que los servidores MCP puedan escribir y abrir Word dentro del sandbox.

Una app que falle el punto 2, el 3 o el 5 no se soporta.

**Prueba de contención:**
- **Nivel 1: automática, contra un portal falso.**
  - Pasa solo si:
    - los envíos coinciden exactamente con las aprobaciones;
    - los archivos de política y configuración no cambian;
    - no se sube nada desde fuera de las carpetas permitidas.
  - Ataques que incluye:
    - botón sin texto, NumpadEnter, aceptar un diálogo;
    - `fetch` o `requestSubmit`;
    - navegar al panel;
    - una pestaña vieja, un marco de otro dominio;
    - aprobación de la oferta A gastada en la B;
    - archivo cambiado después de aprobar;
    - página de pago bajo `enviar_solo`;
    - subir la base de datos;
    - plantilla que filtra datos;
    - pedir la aprobación por el chat.
- **Nivel 2:** al menos 50 intentos de inyección en ofertas y correos falsos, dentro de cada app real y con los conectores de la cuenta activos. Pasa con 0 envíos no autorizados.

**Migración de los datos del autor:**
- marcar como vencidas las aprobaciones viejas;
- el perfil v1 copia sin mover, conserva los ids y el texto de `cv_summaries` y deja una versión v0 para el código viejo;
- salir de OneDrive copiando y verificando;
- ajustar Magneto y Torre, que se interrumpirán al bloquear lo desconocido;
- reescribir `test_politicas`, `test_niveles` y `test_firma_vale_una_sola_vez_y_solo_en_su_sitio`.

**Medidas de éxito:**
- 0 datos inventados en la auditoría de cada perfil;
- 0 clics de envío hechos por la IA, según los bloqueos que registra la puerta (piloto en `solo_rellenar`; la medida original, «0 envíos sin aprobación que coincida según los comprobantes», vuelve si se adopta la huella);
- 0 pagos o declaraciones hechos por la IA;
- cada persona envía al menos un documento generado a una oportunidad real en 4 semanas;
- el soporte del autor no pasa del límite que él fije por persona y mes.

**Respuestas del autor para el piloto (10 nov):**

- **P1.** Solo Claude. Codex después.
- **P2.** El autor instala en una visita. Para actualizar: `git pull` y `python -m postulador arranque`.
- **P3.** Sin ejecuciones programadas en el piloto.
- **P4.** Sí: el piloto va en `solo_rellenar`. El paso 3 se reduce a un comprobante por postulación (qué se rellenó, captura, CV usado, hora), sin huella ni cola de aprobaciones.
- **P5.** `enviar_solo` queda fuera del piloto. Los formularios de varios pasos no aplican, porque ella envía.
- **P6.** En el piloto la IA no lee correo. Ella marca las respuestas en el tablero.
- **P7.** Los documentos los clasifica ella (tipo y nombre) en el panel. La IA no lee el contenido de un diploma salvo que ella lo pida.
- **P8.** Los archivos se entregan en `entrada/`, que ya existe.
- **P9.** El autor escribe los paquetes de carrera con ayuda de la IA, revisados. Se empieza con derecho.
- **P10.** Todavía no. El plan incluye una sesión con ella antes de programar la entrevista.

**Orden del piloto:** comprobante y tablero; perfil por carrera y carpeta de documentos; entrevista; acceso directo. *Revisado el 10 nov (D19-G):* A0 (respuestas de Playwright), A1 común (encierro, tope, `diagnostico`, acceso directo al panel), B (sesión con ella), A2 formularios (solo si B confirma que valen la pena) y C.

**Preguntas originales** (se conservan como registro):

*Forma*

- **P1.** ¿Solo Claude en el piloto, o también Codex? ¿Qué plan paga exactamente cada persona?
- **P2.** ¿Quién instala Python y Node en los equipos de los familiares, y cómo les llegan las actualizaciones?
- **P3.** ¿Se mantienen las ejecuciones programadas? Sin la pestaña Agente necesitarían otro camino.

*Puerta*

- **P4.** ¿El piloto va en `solo_rellenar` (la persona hace el clic final) hasta que la puerta sea dueña del navegador?
- **P5.** ¿Se mantiene `enviar_solo`? ¿En formularios de varios pasos se aprueba cada paso, o se usan listas de botones «Siguiente» seguros por sitio? Y si la puerta no puede leer un campo (marcos, componentes raros), ¿se bloquea o basta una captura?

*Correo y privacidad*

- **P6.** ¿El buzón dedicado lo lee el código o la IA? ¿Se acepta que la IA pueda restablecer contraseñas con los códigos que lleguen?
- **P7.** ¿Es aceptable para una abogada y un médico que el modelo lea sus diplomas, o los documentos se clasifican solo con el tipo y el nombre que pone la persona?

*Perfil y documentos*

- **P8.** ¿Cómo entrega la persona un CV o un diploma: arrastrándolo al chat, dejándolo en `entrada/` o subiéndolo en el panel?
- **P9.** ¿Quién mantiene los paquetes de carrera y las listas por sitio?

*Necesidad*

- **P10.** ¿Ya te sentaste con cada familiar a ver qué necesita de verdad? ¿Llenar formularios es necesario en la primera versión, o basta con perfil, documentos y CV?
