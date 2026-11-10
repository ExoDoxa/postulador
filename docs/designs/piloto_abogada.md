# Piloto de Postulador para una abogada

*   **Autor:** ExoDoxa
*   **Estado:** Aprobado por el autor (2026-11-10). Revisión EGM hecha y correcciones aplicadas (2026-11-10)
*   **Fecha:** 2026-11-10
*   **Contexto:** [concepts_brief.md](../../concepts_brief.md) (D1 a D18 y respuestas a P1 a P10)
*   **Revisión:** [goldfish_review_report.md](../../goldfish_review_report.md) (decisiones A a G)

--------------------------------------------------------------------------------

## Estado de la implementación (2026-11-10)

El autor pidió dejar el piloto completo para instalarlo, **antes** de la sesión con ella (bloque B). Así que A0, A1,
A2 y C están programados, y lo que debía salir de B quedó con valores provisionales, marcados en el código:
`postulador/paquetes/derecho.json` (campos, tipos de documento y un CV de hasta 2 páginas) y
`PASO_SEGURO_POR_SITIO`, que sigue vacío. Si B concluye que sus portales no tienen formularios que valga la pena
rellenar, A2 se puede desactivar bajando el tope a `solo_preparar`.

Resultados: 117 pruebas unitarias, el e2e del panel y la contención contra un navegador real
(`python -m tests.contencion`, 0 envíos) pasan.

**Lo que cambió respecto del texto de abajo, al implementar:**

| Cambio | Por qué |
|---|---|
| Con un borrador abierto, sí pasa el clic en el campo de adjuntar archivo (`BOTON_ARCHIVO` en `puerta.py`), salvo que su etiqueta suene a envío | A0 mostró que Playwright MCP 0.0.84 presenta el campo de archivo como un botón: sin la excepción, la IA no podría subir el CV |
| Playwright MCP arranca con la carpeta de CV como carpeta de trabajo (`navegador.carpeta_mcp`) | La contención mostró que 0.0.84 se niega a subir archivos fuera de su carpeta de trabajo. También acota las subidas a los CV |
| Playwright MCP 0.0.84 rechaza un `Host` ajeno pero **acepta un `Origin` ajeno** (A0) | Queda en la tabla de riesgos: falta comprobar si una página web podría usarlo sin leer la respuesta |
| La tabla de transiciones, el candado y el sello del perfil rigen solo con el tope en `solo_rellenar` o menos. Con un tope mayor (equipo del autor) todo sigue como hoy | Así el flujo `aprobar` del autor, su lectura de correo y sus seguimientos no cambian |
| La IA también registra en `incompleta` y `descartada` | La rutina registra las ofertas descartadas con su motivo; ninguno de esos estados cuenta como enviado ni pone el candado |
| El borrador se abre solo con la primera escritura; los clics se anotan si ya hay uno | Si un clic lo abriera, navegar por la lista de ofertas bloquearía escribir en el formulario |
| La prueba de contención corre la puerta en el mismo proceso, con un Playwright MCP real sin ventana | Prueba la misma lógica que por stdio y no necesita lanzar la app de Claude |
| `instalar.cmd` hace con doble clic los pasos de instalación | El autor pidió que ella pudiera descargarlo e instalarlo |
| Meta 9: solo el plan B (`LEEME.html` y su acceso directo) | La pregunta 4 sigue sin investigar ([acceso_directo_ia.md](../piloto/acceso_directo_ia.md)) |

--------------------------------------------------------------------------------

## Términos y referencias

| Término | Qué significa en este documento |
|---|---|
| La puerta | `postulador/puerta.py`. Es el servidor MCP que la app conoce como `playwright`. Recibe cada orden de la IA para el navegador, decide si la deja pasar y, si la deja, se la reenvía a Playwright MCP |
| Niveles | Cuánto puede hacer la IA en un sitio, de menos a más: `solo_preparar` (no abre formularios), `solo_rellenar` (rellena y no envía), `aprobar` (envía tras una aprobación) y `enviar_solo` (envía sin preguntar) |
| Tope | El nivel más alto que se permite en el equipo, sin importar lo que diga cada sitio. En el equipo de ella es `solo_rellenar` |
| Borrador | Lo que la puerta va anotando mientras la IA rellena un formulario. Se convierte en comprobante con `formulario_listo` |
| Comprobante | La fila que la puerta guarda al terminar un formulario: campos, archivos, CV, horas e imagen de la página |
| Candado | Mientras alguna postulación espera que ella la envíe, la puerta solo deja leer |
| Imagen de la página | El PNG que toma `browser_take_screenshot` |
| Lectura de la página | El texto estructurado que devuelve `browser_snapshot`. De ahí salen las etiquetas de los campos |
| Hash SHA-256 | El resumen de un archivo, para saber si cambió. No se usa la palabra «huella» para esto |
| Sello de revisión | `revisado_el` y `revisado_huella` dentro del perfil: prueban qué contenido revisó ella |
| PN | Las preguntas P1 a P10 del brief. «Pregunta N», sin la P, es una pregunta abierta de este documento |
| DN | Las decisiones D1 a D18 del brief |
| Paso 0 y paso 1 | Pasos ya hechos del brief: el paso 0 probó la app de escritorio (10 nov) y el paso 1 reforzó la puerta |
| Contención de nivel 1 | La prueba del brief que ataca la puerta con un guion, sin IA, contra un portal falso |
| Revisores del brief | Las propuestas numeradas que hicieron los revisores del brief, por ejemplo «propuesta 2» |
| Ley 1581 | La ley colombiana de protección de datos personales |
| Modelo de difusión | Un modelo que genera texto en paralelo. El brief lo evaluó para rellenar y lo aparcó |

## Resumen

Este documento diseña el piloto de Postulador para una sola persona: la hermana del autor, abogada en Colombia.
Ella trabaja en la pestaña Code de la app de escritorio de Claude, en una sesión creada en su carpeta de arranque
(`C:\Users\<ella>\Postulador`). Ahí la IA le hace una entrevista, arma su perfil, genera sus CV, busca ofertas y
rellena formularios en un navegador visible. El clic de envío lo hace ella. En el panel ve su perfil, sus
documentos, sus CV y un tablero de postulaciones. Cada postulación lleva un comprobante que escribe el código, no la
IA.

El piloto parte de lo que ya está hecho: la puerta reforzada (paso 1), la carpeta de arranque con denegaciones
(D15), el lugar único de datos (D16) y las preferencias de búsqueda (D14). Lo que falta, en el orden que fijó el
autor (decisión G de la revisión):

1. **A0:** capturar las respuestas reales de Playwright MCP que la puerta va a leer;
2. **A1, común:** encierro, tope, `diagnostico`, quitar lo que sobra y el acceso directo al panel;
3. **B:** una sesión del autor con ella para ver sus canales de búsqueda, sus formularios y su CV;
4. **A2, formularios:** quién cambia cada estado, candado, borrador, comprobante y tablero. Solo si B confirma que
   sus portales tienen formularios que valga la pena rellenar;
5. **C:** perfil de abogada con CV de varias páginas, documentos, entrevista y acceso directo a la IA.

Todo lo demás del brief queda para después del piloto.

## El problema

Hoy Postulador solo lo puede manejar su autor, y está hecho para buscar empleo en tecnología. Para una abogada
fallan cosas concretas:

*   **El tablero cuenta lo que la IA dice.** `postulacion_actualizar` deja a la IA marcar `enviada`, y nada
    distingue lo que hizo la IA de lo que hizo ella (`registro.py:31`). No queda registro de qué se escribió en cada
    formulario ni de qué CV se subió. Si algo sale mal, ni ella ni el autor pueden reconstruir qué se envió con su
    nombre.
*   **El perfil no tiene campos de abogada.** No hay tarjeta profesional ni área de práctica que se vean en el
    panel o en el CV. Además el perfil exige publicaciones y proyectos (`perfil.py:7-8`), algo propio de quien
    trabaja en tecnología.
*   **Sus documentos no tienen dónde ir.** Diplomas, tarjeta profesional y certificados no tienen carpeta, ni
    registro, ni forma de guardarlos sin que la IA vea su contenido.
*   **La entrevista y la skill están pensadas para tecnología.** Hablan de ATS, idoneidad y portales como
    Greenhouse, que poco sirven para un cargo legal en Colombia.
*   **Arrancar no es obvio.** Si la sesión no se crea en la carpeta de arranque, no carga ni la puerta ni las
    denegaciones (paso 0, 10 nov). El autor no encontró cómo elegir la carpeta en dos intentos.
*   **El encierro tiene un hueco sin cerrar.** La app suma los conectores de la cuenta de claude.ai (TinyFish,
    Gmail, Drive…), y desde el proyecto no hay forma confiable de desactivarlos. Un conector que maneje un
    navegador se salta la puerta por completo.

Lo que ella gana si el piloto funciona: deja de adaptar su CV a cada oferta y de llenar formularios repetidos, y
sabe qué rellenó el asistente en su nombre.

## Metas

Cada meta dice cómo se comprueba.

1.  **Encierro: lo que bloquea y lo que es instrucción.**
    *   *Bloquea:* los conectores desactivados en la configuración de claude.ai de su cuenta (lista de verificación
        del autor), las denegaciones de la carpeta de arranque y la herramienta `diagnostico`, que el código responde
        sin depender de la IA.
    *   *Es instrucción:* al empezar cada sesión, la skill revisa sus herramientas y se niega a buscar o rellenar si
        falta `postulador` o la puerta, o si ve alguna herramienta que maneje un navegador o el escritorio por fuera
        de la puerta, incluida cualquier `mcp__claude_ai_*`.

    *Se comprueba* de tres formas:
    *   en una sesión fuera de la carpeta de arranque no aparecen las herramientas de Postulador ni la puerta, así
        que la IA no puede usar el perfil ni dejar comprobantes;
    *   en una sesión dentro de la carpeta con un conector activo, la IA se niega y explica qué hacer;
    *   `diagnostico` informa un problema si `.claude/settings.json` no tiene las denegaciones.

    El riesgo de que, fuera de la carpeta, la IA use otro navegador queda en la tabla de riesgos.
2.  **La puerta bloquea todo clic que pueda enviar.** En su equipo, el tope es `solo_rellenar` en todos los sitios,
    sin importar lo que diga `politicas.json` ni lo que se cambie en el panel. Mientras hay un formulario a medio
    rellenar, la puerta bloquea todo clic sobre un botón, Enter, espacio y todo diálogo aceptado, salvo los pasos que
    el autor marque como seguros para ese sitio. *Se comprueba* de dos formas:
    *   la prueba de contención de nivel 1 (botón sin texto, NumpadEnter, diálogo, selector, pestaña vieja) contra
        un portal falso: el portal no recibe ningún envío y cada intento queda bloqueado y anotado;
    *   la medida de ella: en el panel puede marcar «Ya estaba enviada cuando la vi», y cada marca cuenta como un
        incidente.
3.  **Cada postulación rellenada tiene un comprobante escrito por el código.** Incluye:
    *   campos rellenados y su valor;
    *   casillas y botones de opción que se marcaron;
    *   archivos subidos y su hash SHA-256;
    *   CV usado;
    *   imagen de la página cuando la IA terminó;
    *   hora de inicio y de fin del relleno.

    Se presenta como **«lo que rellenó el asistente»**, no como «lo que se envió», porque ella puede corregir
    campos antes de hacer clic. Se guarda en una tabla a la que solo se añaden filas, y la IA no tiene ninguna
    herramienta que la escriba. Cuando el asistente termina, se activa el candado: la IA no puede escribir en ningún
    formulario mientras haya uno esperando que ella lo envíe, así que ella envía con calma sin que nada le cambie la
    página. *Se comprueba* de dos formas:
    *   rellenando el portal falso: los campos y archivos que escribió la puerta coinciden con la página;
    *   intentando que la IA escriba, haga clic o navegue con el candado puesto: la puerta lo bloquea, también en una
        sesión nueva.
4.  **«Enviada» la confirma ella.** La IA puede reportar que vio la confirmación del portal: la postulación pasa a
    `reportada` («Enviada según la IA»). Solo ella la pasa a `enviada` desde el panel («La envié»). Solo cuentan como
    enviadas, y solo generan seguimientos, las que están en `enviada`. Las respuestas de las empresas (avanzó,
    rechazada) y los seguimientos hechos los marca solo ella. *Se comprueba* con las pruebas de la tabla de quién
    cambia cada estado: cada cambio que no le toca a la IA falla cuando lo pide la IA.
5.  **Tablero útil para ella.**
    *   Se abre al empezar a buscar y muestra cada postulación con su estado y su comprobante.
    *   Arriba muestra las postulaciones que llevan más de un día esperando que ella las envíe y le pregunta «¿la
        enviaste?», con la advertencia «mientras no la resuelvas, el asistente no puede seguir».
    *   La pantalla «Por firmar» pasa a llamarse «Lista para enviar», y ninguna pantalla usa «firmar».
    *   Un acceso directo «Panel de Postulador» abre el panel sin ninguna sesión de IA, para que confirme envíos y
        respuestas cualquier día.

    *Se comprueba* con ella en la prueba de uso: sin preguntarle al autor, identifica qué postulaciones le toca
    enviar y, sin abrir Claude, confirma una de ellas.
6.  **Perfil de abogada.** Un paquete de carrera de derecho define sus campos: clave, etiqueta, si es obligatorio,
    si es sensible y si va en el CV. El panel muestra y edita esos campos, y el CV los incluye. Publicaciones y
    proyectos dejan de ser obligatorios. El CV puede tener varias páginas, hasta el tope que fije el paquete. Los
    títulos se copian tal cual («abogada» no se cambia por «egresada»). **D6 en versión mínima:** no se generan CV
    ni cartas hasta que ella revise el perfil. Si la IA cambia algo después, el sello de revisión deja de valer y
    `cv_generar` se niega hasta que ella vuelva a marcar «Revisado». En los formularios, el control es el
    comprobante más el clic de ella. *Se comprueba* con la auditoría del perfil (0 datos inventados y 0 títulos
    alterados) y con un CV de ella que ocupa las páginas que le hacen falta sin pasar del tope.
7.  **Documentos sin que la IA los lea.** Ella deja archivos en `entrada/`. El código revisa esa carpeta, copia lo
    nuevo (nunca lo mueve) a la carpeta de documentos con un nombre que elige el código, y lo registra. Ella elige
    en el panel el tipo y el nombre visible. La IA solo ve el tipo y el nombre, salvo que ella le permita leer uno.
    En el piloto la IA solo sube a los portales el CV (`cv:<nombre>`). Los diplomas y la tarjeta profesional los sube
    ella. *Se comprueba* con que ninguna herramienta devuelva el contenido de un documento si ella no marcó «La IA
    puede leerlo».
8.  **Entrevista para derecho.** Parte de su CV y pregunta solo lo que falta para el paquete de derecho. Se escribe
    **después** de una sesión del autor con ella para ver qué necesita de verdad (P10). *Se comprueba* con que ella
    termine la entrevista sin ayuda y el perfil resultante pase la auditoría.
9.  **Arranque en un paso.** Un acceso directo abre la app de Claude ya en la carpeta de arranque. Si la app no lo
    permite, una instrucción de un solo paso con imagen. *Se comprueba* con que ella abra una sesión con encierro
    sin ayuda, tres veces seguidas.

**Medidas de éxito del piloto (4 semanas desde la instalación):**
*   0 datos inventados en la auditoría de su perfil. La hace el autor, contra el CV original y los documentos de
    ella, al final de las semanas 1 y 4;
*   0 incidentes marcados por ella («Ya estaba enviada cuando la vi»);
*   0 pagos o declaraciones juradas hechos por la IA;
*   ella envía al menos un CV generado por Postulador a una oferta real;
*   el soporte del autor no pasa del límite que él fije (pregunta 3);
*   cupo de la suscripción: el autor anota cada vez que ella llega al límite de su plan. Si pasa más de una vez por
    semana, se reconsidera el uso del navegador.

## Fuera de alcance

*   Otras personas y otras carreras. Solo derecho y solo ella.
*   Codex y cualquier IA distinta de Claude.
*   Ejecuciones programadas.
*   `enviar_solo` y `aprobar` en el equipo de ella: la cola de aprobaciones, la huella de aprobación de A3 y la
    transacción de varios pasos. En el equipo del autor, el flujo `aprobar` sigue como hoy.
*   Leer correo, sea el dedicado o el personal. El lector en código llega después del piloto.
*   Clasificar documentos con la IA o leer diplomas sin que ella lo permita.
*   Que la IA suba documentos a los portales (`doc:<id>`, decisión F). Solo sube el CV.
*   Plantillas de CV escritas por la IA (`plantilla_guardar`, decisión D).
*   ATS e idoneidad: quedan ocultos para el paquete de derecho, porque sus reglas son de tecnología.
*   El formato de hoja de vida del SIGEP (la hoja de vida del sector público colombiano).
*   Instalador propio, app propia y actualizaciones automáticas. El autor instala en una visita y actualiza con
    `git pull` y `python -m postulador arranque`.
*   El modelo de difusión para rellenar.
*   Búsqueda determinista por portal (la consecuencia de la prueba en LinkedIn del 9 nov), salvo que la pregunta 1
    la meta en el piloto.

## Preguntas abiertas

*   **1. ¿Dónde busca empleo ella?** Hoy Postulador busca en Greenhouse, Lever y Ashby (`portales.py:1`), donde
    casi no hay cargos legales en Colombia, y en LinkedIn por el navegador. Computrabajo, elempleo, SIGEP II,
    CNSC/SIMO y las páginas de firmas de abogados no están cubiertos. Si sus ofertas están en esos sitios, la medida
    de «un CV enviado en 4 semanas» puede fallar por falta de canal, no por el diseño. Se resuelve en la sesión con
    ella (bloque B), antes del bloque A2.
*   **2. ¿Cuál es el tope de páginas del CV para derecho?** El valor lo fija el paquete de carrera. Se decide en la
    sesión con ella.
*   **3. ¿Cuál es el límite de soporte por mes?** La medida de éxito lo pide como número.
*   **4. ¿El acceso directo a la IA es posible?** No se ha comprobado si la app de escritorio de Claude acepta que
    se abra una sesión ya en una carpeta, ni por línea de comandos ni por un enlace. Se investiga antes de programar
    la meta 9. Si no lo acepta, la meta 9 queda en su plan B: una instrucción de un solo paso con imagen.

**Resueltas en esta redacción y en la revisión:**

*   *Detección de «Enviada»:* la reporta la IA como `reportada` y siempre queda pendiente de que ella la confirme
    (decisión del autor, 10 nov). Se descartaron que la puerta compare la página al releerla y que escuche el
    navegador por CDP.
*   *Candado:* uno solo para todo el navegador, guardado en la base (decisión A de la revisión). La IA no sigue con
    otra oferta hasta que ella resuelva la que espera.
*   *Perfil:* un solo archivo con sello de revisión (decisión B).
*   *Envío:* con un borrador abierto se bloquea todo botón salvo una lista segura por sitio (decisión C).
*   *Plantillas:* se quita `plantilla_guardar` durante el piloto (decisión D).
*   *Tope:* en un archivo de máquina que falla cerrado (decisión E).
*   *Documentos a portales:* se aplaza `doc:<id>` (decisión F).
*   *Documentos:* barrido automático de `entrada/` (decisión del autor, 10 nov).
*   *CV de varias páginas:* entra en el piloto, con un tope configurable en cada paquete de carrera (decisión del
    autor, 10 nov).
*   *Panel sin sesión de IA:* entra en el piloto como un acceso directo propio (decisión del autor, 10 nov). La
    clave de un solo uso queda fuera; el riesgo que deja está en la tabla de riesgos.
*   *La revisión de herramientas al empezar es una instrucción, no un bloqueo:* se acepta para el piloto (meta 1).

## Recorridos de usuario

### Recorrido 1: Primera sesión y documentos

*   **Dado:** el autor instaló Postulador en el equipo de ella, desactivó los conectores de su cuenta de claude.ai,
    creó la carpeta de arranque y la acompañó a iniciar sesión en sus portales en el navegador dedicado. Ella dejó su
    CV actual, su diploma y su tarjeta profesional en `entrada/`.
*   **Cuando:** abre la app de Claude con el acceso directo y escribe «hola».
*   **Entonces:**
    *   la IA llama a `diagnostico` y revisa sus herramientas;
    *   la IA llama a `documentos_listar`, que copia los tres archivos a la carpeta de documentos;
    *   la IA le dice: «abre el panel, pestaña Documentos, y dime qué es cada archivo»;
    *   ella marca el CV como «Mi CV» y los otros dos con su tipo;
    *   la IA lee solo el CV y empieza la entrevista.

### Recorrido 2: Una postulación

*   **Dado:** un perfil revisado por ella, una oferta que encaja y ninguna postulación esperando que ella la envíe.
*   **Cuando:** la IA registra la postulación como `preparada` y rellena el formulario en el navegador visible.
*   **Entonces:**
    *   la puerta anota cada campo, cada casilla y cada archivo;
    *   si la IA intenta pulsar cualquier botón, incluido «Enviar», la puerta la bloquea. En un formulario de varios
        pasos, ella pulsa «Siguiente» y la IA sigue en la página nueva;
    *   la IA llama a `formulario_listo`, y la puerta toma la imagen de la página, guarda el comprobante y pone el
        candado;
    *   el tablero muestra la postulación en «Lista para enviar»;
    *   la IA le dice: «revisa la ventana del navegador y pulsa Enviar tú. Cuando la hayas resuelto en el panel,
        sigo con la siguiente oferta»;
    *   ella revisa, corrige si quiere y envía.

### Recorrido 3: Confirmar y registrar respuestas

*   **Dado:** una postulación en `rellenada`.
*   **Cuando:** en el turno siguiente la IA lee la página (leer sí se permite con el candado), ve la confirmación del
    portal y la reporta con `postulacion_actualizar(id, 'reportada')`.
*   **Entonces:**
    *   el tablero la muestra como «Enviada según la IA, ¿la confirmas?»;
    *   ella pulsa «La envié», se quita el candado y empieza a contar el seguimiento;
    *   la IA sigue con la siguiente oferta;
    *   semanas después, cuando la empresa responde, ella abre el acceso directo «Panel de Postulador» sin abrir
        Claude y marca «Avanzó» o «Rechazada».

### Recorrido 4: Una postulación olvidada

*   **Dado:** una postulación lleva más de un día en `rellenada` o `reportada`.
*   **Cuando:** ella abre el panel.
*   **Entonces:** arriba aparece «¿Enviaste la postulación a <cargo> en <empresa>? Mientras no la resuelvas, el
    asistente no puede seguir», con las opciones «Sí, la envié», «No, ya no» (la descarta), «Que el asistente la
    corrija» y «Ya estaba enviada cuando la vi».

## Plan técnico

### Vista general

```text
 Ella ─┬─► App de Claude (modo Code), sesión creada en C:\Users\<ella>\Postulador
       │        │  denegado: Bash, PowerShell, Edit, Write, Read, Glob, Grep, Agent, Task,
       │        │  WebFetch, otros navegadores y control del equipo (arranque.py)
       │        ├──► postulador (MCP, stdio) ── perfil, CV, documentos, postulaciones, diagnostico
       │        └──► playwright = la puerta (MCP, stdio)
       │                 │  filtra, tope solo_rellenar, candado leído de la base, un borrador a la vez,
       │                 │  formulario_listo → imagen de la página + comprobante + candado
       │                 └──► Playwright MCP :8931 ──CDP──► navegador dedicado :9222
       │                                                        ▲
       ├────────────────── clic de envío ────────────────────────┘
       │
       └─► Panel :8770 en SU navegador normal: tablero, comprobantes, perfil, documentos, CV
                 (lo arranca la sesión de IA o el acceso directo «Panel de Postulador»; una sola instancia)
                 │
   postulador.db + documentos/ + comprobantes/ + respaldos/   (carpeta de datos según ubicacion.json)
                 ▲
   entrada/ ── barrido al listar (copia, nunca mueve) ─┘

   %LOCALAPPDATA%\Postulador\ubicacion.json   dónde están los datos
   %LOCALAPPDATA%\Postulador\equipo.json      tope y carpeta de arranque (solo lo escribe arranque)
```

Hay tres procesos de Postulador:
*   el servidor MCP `postulador`;
*   la puerta;
*   el panel, que hoy arranca el servidor MCP y en el piloto también puede arrancar un acceso directo.

No se hablan entre ellos: comparten la base `postulador.db` y la carpeta de datos. Eso ya pasa hoy con las
aprobaciones y el registro de actividad, y el diseño mantiene esa forma. La IA solo llega a la base a través de las
herramientas de `postulador`. Con `Read` denegado, no puede abrir el archivo directamente.

**El navegador dedicado.** No es el navegador normal de ella. `navegador.asegurar_mcp` lo abre en la primera acción
de la IA, con su propio perfil (`%LOCALAPPDATA%\PostuladorNavegador`, `navegador.py:64-66`) y el puerto de
depuración 9222. En la instalación, el autor la acompaña a iniciar sesión en sus portales dentro de esa ventana; las
sesiones quedan guardadas en ese perfil. El panel, en cambio, se abre en su navegador normal.

### 1. Encierro (meta 1)

*   **Se deniegan `Read`, `Glob` y `Grep`.** Hoy no están en `DENEGADAS` (`arranque.py:17-19`), así que la IA puede
    leer `entrada/`, los diplomas incluidos, y la carpeta de datos. La skill ya se lee con `guia_leer`, así que
    ninguna función de Postulador necesita esas herramientas.
*   **Sin `plantilla_guardar`.** Con el tope en `solo_rellenar` o menos, la herramienta no aparece y `_llamar` la
    rechaza. Así, con `Read` denegado y sin `plantilla_guardar`, la IA no tiene cómo hacer que una plantilla HTML
    lea `entrada/` con `file://` al generar un CV.
*   **Argumentos fuera del esquema.** Las envolturas de `postulador` rechazan cualquier argumento que no esté en las
    `properties` de la herramienta. Hoy `_llamar` pasa `**argumentos` sin filtrar (`mcp_server.py:95`), así que la
    IA podría mandar, por ejemplo, `por='persona'`.
*   **Herramienta `diagnostico` en `postulador`.** Es lo que pedía el punto 3 del paso 0 del brief. Devuelve:
    *   la carpeta de arranque;
    *   el Python que se está usando;
    *   la carpeta de datos y si está disponible;
    *   la versión de Postulador (`postulador.__version__`);
    *   el tope y si `equipo.json` se pudo leer;
    *   si `.claude/settings.json` de la carpeta de arranque contiene exactamente las denegaciones que `arranque`
        genera hoy;
    *   `problemas`: una lista de frases sencillas en español.

    El código no puede ver las otras herramientas que cargó la app. Esa revisión la hace la IA según la skill (meta
    1). `diagnostico` solo exige la carpeta de arranque cuando el tope es `solo_rellenar` o menos, así que los
    comandos del autor (`ejecutar`, `programar`) siguen rellenando en su equipo.
*   **Regla de inicio en la skill y en `CLAUDE.md`.** Al empezar, la IA llama a `diagnostico` y revisa su lista de
    herramientas. No busca ni rellena nada si pasa cualquiera de estas cosas:
    *   `diagnostico` trae `problemas`;
    *   falta `postulador` o la puerta;
    *   ve herramientas de navegador, terminal o control del equipo fuera de la puerta;
    *   ve cualquier herramienta `mcp__claude_ai_*`.

    En ese caso le dice a ella, con palabras sencillas, que avise al autor.
*   **Lista de verificación de instalación.** Un documento para el autor que incluye:
    *   instalar Python y Node;
    *   clonar el código fuera de OneDrive y ejecutar `pip install -r requirements.txt`;
    *   ejecutar `arranque`;
    *   desactivar los conectores en claude.ai, en la cuenta de ella;
    *   abrir el navegador dedicado e iniciar sesión con ella en sus portales;
    *   abrir la primera sesión y comprobar `diagnostico`.

**Futuras mejoras, fuera del piloto:** una instrucción o un `deny` en la configuración de usuario de Claude
(`~/.claude`), para cubrir las sesiones fuera de la carpeta. Afecta todas las sesiones de ella, así que lo decide el
autor después del piloto.

### 2. Tope `solo_rellenar` y regla de envío (meta 2)

*   **El tope vive en un archivo de máquina.** `arranque` escribe `%LOCALAPPDATA%\Postulador\equipo.json`, junto a
    `ubicacion.json`:

    ```text
    { "version": 1, "nivel_maximo": "solo_rellenar", "arranque": "C:\\Users\\<ella>\\Postulador" }
    ```

    *   Solo lo escribe `arranque`. La IA no tiene comandos ni `Write`, y el panel no lo toca.
    *   **Falla cerrado:** si el archivo falta, no se puede leer o trae un nivel inválido, el tope es
        `solo_rellenar` y `diagnostico` lo informa como problema. Nunca lanza una excepción.
    *   El autor sube el tope de su propio equipo una vez, con `python -m postulador arranque --nivel-maximo
        aprobar`.
    *   Los tres procesos leen el mismo archivo, así que el panel que abre el acceso directo tiene el mismo tope.
*   **Cómo se aplica el tope.**
    *   `registro.nivel_de_url` devuelve el nivel menos permisivo entre el configurado y el tope. El orden sale de
        `ORDEN_NIVELES = tuple(reversed(NIVELES))`: `solo_preparar`, `solo_rellenar`, `aprobar`, `enviar_solo`. Hoy
        el nivel por defecto es `aprobar` (`registro.py:17`). Con el tope, cualquier sitio, también uno nuevo,
        queda en `solo_rellenar`.
    *   `fijar_politica` rechaza los niveles por encima del tope, y Ajustes del panel no los ofrece y muestra el tope
        vigente.
    *   `politica_consultar` devuelve el nivel efectivo, ya limitado, y el tope.
    *   Con el tope en `solo_rellenar` o menos, `postulador` no ofrece `aprobacion_solicitar`,
        `aprobacion_consultar` ni `aprobaciones_listar`. Ocultarlas es solo para que la IA no se confunda: lo que
        bloquea es `nivel_de_url` en la puerta (`puerta.py:135`).
*   **Regla de envío con un borrador abierto.** Desde la primera escritura de un formulario hasta `formulario_listo`,
    la puerta bloquea:
    *   todo `browser_click` cuyo elemento sea un botón (`button`, o un `input` de tipo `submit`, `button` o `image`,
        según la lectura de la página) y todo clic por selector sin referencia de la lectura;
    *   todo `browser_press_key` con Enter, NumpadEnter o espacio;
    *   todo `browser_handle_dialog` con `accept: true`.

    Solo pasan los clics cuya etiqueta esté en `PASO_SEGURO_POR_SITIO`, un diccionario nuevo con la misma forma que
    `ENVIO_POR_SITIO` (`puerta.py:21`): `{dominio: expresión regular de etiquetas seguras}`. Queda vacío hasta el
    bloque B, así que mientras tanto ella pulsa «Siguiente» en los formularios de varios pasos. Los clics sobre
    casillas, botones de opción y listas pasan y quedan en el borrador.

    Sin borrador abierto (por ejemplo, al buscar ofertas) se aplican las reglas de hoy.
*   **Mensaje de bloqueo.** `AVISAR` (`puerta.py:38`) pasa a pedir `formulario_listo`.

### 3. Comprobante y candado (meta 3)

**Un borrador a la vez.** La puerta conserva su estado único de hoy (`url`, `etiquetas` y `pestana_propia`,
`puerta.py:73-75`) y le suma un solo borrador. No lleva estado por pestaña. El borrador se abre con la primera
escritura (`browser_type`, `browser_fill_form`, `browser_select_option`, `browser_file_upload`, `browser_drop`,
`browser_drag`); los clics que pasan se anotan si ya hay uno. Si hay un borrador abierto y la IA intenta escribir en una página de otro
dominio, la puerta lo bloquea y le pide `formulario_listo` o `formulario_abandonar` primero. Dentro del mismo
dominio, los pasos de un formulario siguen en el mismo borrador.

**Qué guarda el borrador:**
*   la dirección;
*   la hora de inicio;
*   cada escritura que tuvo éxito: la etiqueta del campo, el valor y la hora;
*   cada `browser_click`, `browser_drag` y `browser_drop` que pasó, con su etiqueta;
*   cada archivo subido, con su nombre y su hash SHA-256;
*   cuántos intentos de envío se bloquearon.

La etiqueta sale de la lectura de la página. Si la referencia del elemento no está en la última lectura, se guarda
la que dio la IA con la marca «etiqueta según la IA».

**Candado de solo lectura.** Mientras exista en `postulador.db` alguna postulación en `rellenada` o `reportada`, la
puerta solo deja pasar:
*   `browser_snapshot`;
*   `browser_take_screenshot`;
*   `browser_wait_for`;
*   `browser_tabs` con `action: list`.

Todo lo demás se bloquea, en cualquier pestaña, con un mensaje que nombra la postulación y pide que ella la resuelva
en el panel. La condición se lee de la base en cada `decidir()`, así que vale en una puerta recién arrancada, en una
sesión nueva y con dos chats abiertos a la vez. Si la base no responde, la puerta bloquea: `atender()` ya falla
cerrado ante cualquier excepción (`puerta.py:221-225`), y una prueba lo cubre. El candado se quita cuando ella saca
la postulación de esos dos estados desde el panel (sección 4).

**Herramientas nuevas de la puerta.** Las dos se suman a la respuesta de `tools/list` después del filtro de
`PERMITIDAS`, en las dos ramas (la lista guardada y la que trae Playwright).

*   **`formulario_listo(postulacion_id)`.** Precondiciones: la postulación existe, está en `preparada` y hay un
    borrador abierto. Si alguna falla, responde con un error y no hace nada, así que una segunda llamada falla. Al
    cumplirse:
    1.  pide `browser_take_screenshot` a Playwright con `{"type": "png", "fullPage": true, "scale": "css"}` (formato
        confirmado en A0);
    2.  `comprobantes.crear` escribe el PNG y, en una sola transacción, inserta el comprobante y pasa la postulación
        a `rellenada`. Si la transacción falla, borra el PNG;
    3.  cierra el borrador y le responde a la IA que le diga a ella que revise y envíe.

    El comprobante guarda la dirección real de la página, no la de la postulación. No se compara el dominio: con un
    solo borrador no hace falta.
*   **`formulario_abandonar()`.** Cierra el borrador sin comprobante, por ejemplo si la IA descubre que la oferta no
    encaja. Anota en la actividad cuántos campos se habían escrito. La postulación no cambia; la IA la pasa a
    `incompleta` o `descartada` con `postulacion_actualizar`.

Si la IA nunca llama a `formulario_listo`, la postulación aparece en el tablero como «sin comprobante».

**Tabla `comprobantes` en `postulador.db`.** La crea `registro.conexion()`, igual que `aprobaciones._conexion` crea
la suya, para que `registro` y `comprobantes` no se importen en círculo. Columnas:
*   `id`, `postulacion_id`, `url`;
*   `inicio`, `fin`;
*   `campos` (JSON), `clics` (JSON), `archivos` (JSON), `cv`;
*   `imagen` (ruta relativa) e `imagen_sha256`;
*   `envios_bloqueados`, `creado`.

La imagen se guarda en `comprobantes/c<id del comprobante>.png`, dentro de la carpeta de datos. La columna `cv` sale
del `cv:<nombre>` que se subió; si no se subió ninguno, queda vacía. Dos disparadores de SQLite (`before update` y
`before delete`, con `raise(abort)`) hacen que solo se puedan añadir filas. Ninguna herramienta de `postulador`
escribe en esta tabla.

**Límite conocido.** Los valores que el portal rellena por su cuenta (por ejemplo, desde su perfil guardado) no
quedan como campos del comprobante: solo se ven en la imagen de la página.

### 4. Estados y quién los cambia (meta 4)

**Estado nuevo `reportada`** («Enviada según la IA»). No entra en `ENVIADAS` (`registro.py:15`), así que no cuenta
como enviada ni genera seguimientos. No hace falta columna nueva ni migración: `ENVIADAS` y los filtros de
`registro.py:91` y `registro.py:109` no cambian, y el historial importado sigue contando como hoy.

**Tabla de transiciones por actor.** `registrar` y `actualizar` reciben `actor` (`'ia'`, `'puerta'` o `'persona'`).
La herramienta de la IA siempre pasa `'ia'`, y el argumento no está en su esquema.

| Actor | Puede hacer |
|---|---|
| IA | registrar en `preparada`, `incompleta` o `descartada`; pasar entre esos tres; pasar de `rellenada` a `reportada` |
| Puerta | pasar de `preparada` a `rellenada`, solo dentro de `formulario_listo` |
| Panel (ella) | sacar de `rellenada` o `reportada`; marcar `avanzo` y `rechazada`; registrar `seguimiento_hecho` |

*   Cualquier otro cambio falla con un mensaje que dice qué actor puede hacerlo.
*   `reportada` mantiene el candado.
*   **En el equipo del autor**, con el tope en `aprobar` o más, la tabla no rige: la IA sigue como hoy, y la vista de
    aprobaciones del panel sigue igual.
*   `seguimiento_hecho` sale de la lista de herramientas de la IA cuando el tope es `solo_rellenar` o menos.

**Acciones de ella en el panel:**

| Botón | Desde | Pasa a |
|---|---|---|
| «La envié» | `rellenada`, `reportada` | `enviada`, con la fecha de envío y el primer seguimiento |
| «No, ya no» | `rellenada`, `reportada` | `descartada` |
| «Que el asistente la corrija» | `rellenada`, `reportada` | `preparada` |
| «Ya estaba enviada cuando la vi» | `preparada`, `rellenada`, `reportada` | `enviada`, y se anota un incidente en la actividad |
| «Avanzó», «Rechazada» | `enviada` | `avanzo`, `rechazada` |

Las cuatro primeras quitan el candado si era la última postulación en `rellenada` o `reportada`.

### 5. Tablero (meta 5)

*   **Pestaña de postulaciones.** Cada fila muestra el estado con palabras («Lista para enviar», «Enviada según la
    IA, ¿la confirmas?», «Enviada») y un enlace al comprobante.
*   **Vista del comprobante.** Se titula «Lo que rellenó el asistente» y muestra los campos, las casillas, los
    archivos, el CV, las horas y la imagen de la página. Debajo dice: «Si cambiaste algo antes de enviar, lo enviado
    puede ser distinto». Se sirve con dos rutas nuevas, `GET /api/comprobantes/<id>` y `.../imagen`.
*   **«Por firmar» pasa a «Lista para enviar».** Se alimenta de `GET /api/postulaciones?estado=rellenada,reportada`,
    que también da el contador `cuenta-lista`. El refresco periódico de `app.js:302-312` pasa a esa ruta. Las
    reportadas muestran los mismos botones que las rellenadas.
*   **Aviso de olvidadas.** Las postulaciones que llevan más de 24 horas en `rellenada` o `reportada`, contadas
    desde el `fin` de su último comprobante, salen arriba con la pregunta del recorrido 4.
*   **Seguimientos.** `POST /api/seguimientos/<id>` pasa a un cuerpo `{accion}`, igual que las demás acciones.
*   **Acceso directo «Panel de Postulador».** `arranque` lo crea en el Escritorio. Ejecuta
    `pythonw -m postulador panel --abrir` con la ruta absoluta de `pythonw.exe`, y abre el panel en su navegador
    predeterminado. Si el puerto 8770 ya tiene un panel de Postulador, solo abre la dirección. El panel ya corre como
    un proceso aparte que sobrevive al chat (`panel.asegurar`, `panel.py:118-126`), y `panel_abrir` ya reutiliza un
    panel abierto. Así que el acceso directo no necesita un ciclo de vida nuevo.
*   **Se quitan la pestaña Agente, «Conectar» y «Pedir al agente»,** como pedía el brief. Lanzan una IA oculta y
    no tienen lugar en el piloto.
*   **`panel_abrir` abre el panel en el navegador predeterminado de ella** (`os.startfile` con la dirección). Hoy
    solo devuelve la dirección, y la IA no puede abrirla porque la puerta bloquea las direcciones locales. La skill
    llama a `panel_abrir` al empezar a buscar.
*   **En el equipo del autor**, con el tope en `aprobar` o más, la vista de aprobaciones y el estado `por_aprobar`
    siguen como hoy.

### 6. Perfil de abogada (meta 6)

*   **Paquete de carrera** en `postulador/paquetes/derecho.json`. La carpeta se llama `paquetes/` para no chocar
    con el módulo nuevo `postulador/carreras.py`. Está en la instalación, así que la IA no puede editarlo. Lo
    escribe el autor (P9). Esquema, que se fija en el bloque C:

    ```text
    { id, nombre, paginas_maximas,
      campos: [ { clave, etiqueta, obligatorio, sensible, en_cv } ],
      tipos_documento: [ { clave, etiqueta } ] }
    ```

*   **Cambios en `perfil.py`:**
    *   `schema_version: 1`;
    *   `carrera`, el id del paquete;
    *   `campos_carrera`, que se valida contra el paquete;
    *   `publications` y `projects` pasan a ser opcionales;
    *   cada entrada de `education` lleva un `id`, para poder vincular un diploma.
*   **Un solo perfil con sello de revisión (D6 en versión mínima).** Hay un solo `perfil.json` (y
    `perfil_<idioma>.json`), y lo leen todos, entrevista incluida.
    *   **«Revisado»** en el panel guarda en el perfil `revisado_el` y `revisado_huella`: el hash SHA-256 del
        contenido sin esos dos campos. También deja una copia en `respaldos/revisado.json` (o
        `respaldos/revisado_<idioma>.json`), que el panel usa para mostrar qué cambió desde la última revisión.
        `respaldos/` queda fuera del patrón `perfil*.json` de `ats.py:93` y `cv.py:217`.
    *   **`cv_generar` y `carta_generar`** se niegan si el hash actual no coincide con `revisado_huella`, con el
        mensaje «revisa tu perfil en el panel».
    *   **Lo que ella edita en el panel** renueva el sello solo si estaba vigente antes de su cambio. Si había
        cambios de la IA sin revisar, el sello sigue sin valer hasta que ella pulse «Revisado».
    *   **Campos sensibles:** `perfil_guardar` (la IA) conserva los que están en el archivo y rechaza cambiarlos.
        `perfil_leer` los devuelve tapados. Solo se escriben desde el panel (Ley 1581).
    *   **Migración:** una sola vez, desde `arranque`: sella el perfil existente del autor, que ya estaba en uso.
    *   En los formularios no hay sello: el control es el comprobante más el clic de ella.
*   **CV.** `cv.py` pinta los campos con `en_cv` en una sección única `{{carrera}}`, con el título del paquete y una
    lista «etiqueta: valor». Los valores pasan por el mismo escape que las demás marcas (`cv.py:55, 62, 72, 112`). El
    tope fijo de una página (`cv.py:185`) pasa a ser `paginas_maximas` del paquete: 1 si el perfil no tiene
    carrera, y lo que fije `derecho.json` (pregunta 2). El mensaje de error dice el tope real. La carta mantiene su
    tope de una página (`cv.py:285`).
*   **Herramienta `perfil_faltantes`.** Devuelve los campos obligatorios del paquete que faltan en el perfil. Es la
    base de la entrevista.

### 7. Documentos (meta 7)

*   **Módulo nuevo `documentos.py`.** `barrer()` recorre `entrada/`. Para cada archivo cuyo hash SHA-256 no esté
    registrado:
    *   lo copia a `documentos/<AAAAMMDD>-<8 caracteres del hash><extensión>`, en la carpeta de datos;
    *   lo registra en la tabla `documentos`.

    El original queda en `entrada/`. Si deja el mismo archivo otra vez, el hash evita el duplicado. Ignora los
    archivos modificados en los últimos 10 segundos, para no copiar uno a medio guardar.
*   **Tabla `documentos`:**

    | Columna | Tipo | Nota |
    |---|---|---|
    | `id` | `INTEGER PRIMARY KEY` | |
    | `huella` | `TEXT NOT NULL UNIQUE` | hash SHA-256 del archivo |
    | `archivo` | `TEXT NOT NULL` | ruta relativa a la carpeta de datos |
    | `nombre_original` | `TEXT` | solo lo ve el panel |
    | `tipo` | `TEXT` | vacío hasta que ella lo clasifica |
    | `nombre` | `TEXT` | nombre visible que elige ella |
    | `ia_puede_leer` | `INTEGER DEFAULT 0` | el código lo pone en 1 cuando ella marca «Mi CV» |
    | `vinculo` | `TEXT` | id de una entrada del perfil, por ejemplo `f1` |
    | `creado`, `clasificado_el` | `TEXT` | fechas ISO |

*   **Dónde está `entrada/`.** Es `<arranque>/entrada`, con `arranque` tomado de `equipo.json`. Si no hay carpeta de
    arranque, no hay barrido.
*   **Cuándo se hace el barrido.** Solo al listar: en `documentos_listar` y en `GET /api/documentos`.
*   **Pestaña Documentos del panel.** Ahí ella elige el tipo (de `tipos_documento` del paquete, más «Mi CV»), el
    nombre visible y, si quiere, «La IA puede leerlo». También ahí fija el vínculo con un dato del perfil (por
    ejemplo, el diploma con su entrada de formación), como dice el brief.
*   **Herramientas para la IA:**
    *   `documentos_listar` devuelve solo `id`, `tipo` y `nombre` de los documentos ya clasificados. Nunca devuelve
        el nombre original ni la ruta.
    *   `documento_leer(id)` devuelve el texto solo si `ia_puede_leer` vale 1. Saca el texto del PDF con
        `ats.extraer_pdf` y el del DOCX con la lectura de párrafos de `motor_docx` (`para_text`). Antes de
        entregarlo, tapa los números que siguen a «C.C.» o «cédula», con la expresión regular
        `(?i)(c\.?\s?c\.?|c[ée]dula)[^\d]{0,15}[\d.\s]{6,15}`. Una imagen escaneada no se puede leer, y la herramienta
        lo dice. Si `pdfminer` no está instalado, responde con un texto que contiene «no puedo leer PDF en este
        equipo» y pide avisar al autor, sin una excepción de Python.
*   **Subidas a portales.** En el piloto la IA solo sube `cv:<nombre>` (sección 3 y ítem 20 del plan de
    implementación). Los diplomas y la tarjeta los sube ella.

### 8. Entrevista (meta 8)

Tiene dos partes:
*   una guía nueva, `skills/postulador/carreras/derecho.md`, que se escribe **después** de la sesión con ella;
*   `perfil_faltantes`, que es la parte en código.

La guía define tres cosas: el orden de las preguntas, qué se le pregunta a ella y qué se saca de su CV, y la regla
de copiar los títulos tal cual. La skill apunta a la guía según la `carrera` del perfil.

### 9. Acceso directo a la IA (meta 9)

El acceso directo al panel es parte de la meta 5. Este es el otro: `arranque` crea en el Escritorio un acceso
directo que abre la app de Claude en la carpeta de arranque, si la app acepta abrirse así (pregunta 4). Antes de
programarlo se investiga, y el resultado se guarda en `docs/piloto/acceso_directo_ia.md`, igual que A0. Mientras no
haya resultado, solo se implementa el plan B: `arranque` deja en la carpeta un `LEEME.html` con un solo paso y una
imagen de cómo elegir la carpeta al crear la sesión.

### Cambios en la skill

`SKILL.md` y sus guías cambian así:
*   regla de inicio con `diagnostico` y rechazo de cualquier `mcp__claude_ai_*`;
*   nunca hacer el clic de envío y llamar siempre a `formulario_listo`;
*   decirle a ella «revisa el navegador y pulsa Enviar tú» y esperar a que la resuelva antes de seguir;
*   reportar `reportada` solo después de ver la confirmación del portal;
*   no marcar respuestas de las empresas ni seguimientos;
*   subir solo `cv:<nombre>`;
*   no usar la palabra «firmar»;
*   no proponer comandos.

`referencias/rutina.md`, `referencias/resultados.md` y `referencias/entrevistas.md` dejan de pedir que la IA marque
`avanzo`, `rechazada` o aprobaciones cuando el tope es `solo_rellenar`. `referencias/cv.md` deja de decir «una
página» y «DOCX si existe».

### Pruebas del piloto

*   **Portal falso local para la prueba de contención.** La puerta bloquea las direcciones del propio equipo
    (`url_prohibida`, `puerta.py:51`), y el código de producción no cambia eso. La prueba lanza la puerta con un
    envoltorio que está en `tests/` y que reemplaza `url_prohibida` para permitir solo el origen del portal falso.
    La instalación de ella no tiene ese envoltorio.
*   **Aislamiento.** La prueba usa carpetas temporales de datos y de arranque, un `equipo.json` temporal (con
    `LOCALAPPDATA` apuntando a una carpeta temporal) y un perfil de navegador temporal. Se niega a correr si los
    puertos 9222 u 8931 ya están ocupados.
*   **Ataques que cubre la prueba:**
    *   los del nivel 1 del brief: botón sin texto, NumpadEnter, diálogo, selector sin identificar, pestaña vieja,
        página de pago, subir la base;
    *   navegar al panel (`127.0.0.1:8770`) y a un marco de otro dominio;
    *   escribir, hacer clic, navegar y cerrar una pestaña, en cualquier pestaña, con el candado puesto;
    *   el candado sigue en una puerta recién arrancada;
    *   escribir en otro dominio con un borrador abierto;
    *   subir una ruta suelta, con `browser_file_upload` o con `browser_drop`;
    *   pedir `plantilla_guardar`, que no existe con el tope.

    Pasa si se cumplen las cuatro condiciones:
    *   el portal no recibió ningún envío;
    *   cada intento quedó bloqueado y anotado en la actividad;
    *   los campos y archivos que escribió la puerta coinciden con la página;
    *   `politicas.json` y `equipo.json` no cambiaron.
*   **Prueba en sesión real con `Read` denegado.** Se hace en la app de escritorio, con una sesión creada en la
    carpeta de arranque. Comprueba:
    *   que la skill carga por `guia_leer`;
    *   que `diagnostico` responde sin `problemas`;
    *   que la entrevista avanza con `perfil_faltantes`;
    *   que `documento_leer` devuelve el texto de «Mi CV»;
    *   que `Read` no aparece en la lista de herramientas.

## Riesgos y mitigaciones

| Riesgo | Cómo falla | Mitigación | Lo que queda |
|---|---|---|---|
| El envío se reconoce por texto | Un botón de envío sin un texto conocido pasa | Con un borrador abierto se bloquea todo botón salvo `PASO_SEGURO_POR_SITIO` (sección 2) | Un enlace o un elemento que no es botón y envía con JavaScript. Lo mide ella con «Ya estaba enviada cuando la vi» |
| Sesión fuera de la carpeta de arranque | No cargan la puerta ni las denegaciones | Acceso directo de la meta 9; sin la carpeta no hay herramientas de Postulador ni perfil | La IA podría usar otra herramienta de navegador de la app con sus propias sesiones. Futura mejora: reglas de usuario |
| Conectores de la cuenta | Un conector maneja un navegador por fuera de la puerta | Se desactivan en la instalación; la regla de inicio rechaza `mcp__claude_ai_*` | Un conector nuevo que se active solo. La regla de inicio es una instrucción |
| Inyección desde ofertas | Una oferta pide a la IA hacer algo que ella no pidió | Tope, regla de envío, candado, solo `cv:` en subidas, sin `plantilla_guardar` | La IA puede escribir un dato equivocado en un campo; lo ve ella en el comprobante antes de enviar |
| Cupo de la suscripción | El navegador gasta mucho cupo y ella queda sin servicio | El autor anota cada vez que ella llega al límite (medidas de éxito) | Se reconsidera si pasa más de una vez por semana |
| Clave del panel por `/api/sesion` | Cualquier proceso local puede pedir la clave del panel y hacer las acciones de ella | En la sesión encerrada la IA no tiene comandos, y la puerta bloquea las direcciones locales | Se reabre si se habilita algún comando o si ella usa Claude fuera de la carpeta de arranque |
| Ley 1581 | El perfil y las páginas que lee la IA llegan a la empresa de IA | Campos sensibles solo desde el panel y tapados para la IA; documentos sin lectura salvo permiso | El resto del perfil sí llega. Ella lo acepta en la instalación |
| Canal de búsqueda | Sus ofertas están en portales que Postulador no cubre | Pregunta 1 en el bloque B, antes de A2 | La medida «un CV enviado» puede fallar por el canal |
| Puertos 8931 y 9222 sin autenticación | Un proceso local maneja el navegador | A0: Playwright MCP rechaza un `Host` ajeno (403) y el navegador no se lanza con `--remote-allow-origins=*` | Un proceso local con permisos de ella. Además 0.0.84 acepta un `Origin` ajeno: falta comprobar si una página web abierta en su navegador normal podría mandarle órdenes sin leer la respuesta (cada llamada después de `initialize` necesita la cabecera `Mcp-Session-Id`, que esa página no puede leer) |
| Soporte del autor | Ella depende de que el autor arregle cada falla | Lista de instalación, `diagnostico` con frases sencillas, límite de la pregunta 3 | Si se pasa del límite, se reconsidera el piloto |
| Valores que rellena el portal | El portal autocompleta campos que no pasan por la puerta | Se ven en la imagen de la página | No quedan como campos del comprobante |
| Base de datos caída | La puerta no puede leer el candado | `atender()` falla cerrado ante cualquier excepción (`puerta.py:221-225`), con prueba | Ninguno: con la base caída no se escribe |

## Alternativas consideradas

Cada alternativa sigue el mismo formato. El motivo empieza por la razón técnica y termina con la decisión que lo
fijó.

### Alcance del documento

#### A1. Diseñar el programa completo (pasos 2 a 7 del brief)

*   **A favor:** una sola arquitectura para todas las carreras y todas las personas.
*   **En contra:** con P1 a P10 abiertas, el plan de implementación habría dejado decisiones importantes sin tomar.
*   **Motivo del rechazo:** la huella de aprobación, la cola de aprobaciones y el lector de correo dependían de
    respuestas que todavía no existían. Rechazada por el autor; ver D17 del brief.

#### A2. Diseñar solo el siguiente bloque técnico (cerrar el paso 2 y hacer el paso 3 completo)

*   **A favor:** detalle suficiente para implementar sin decidir sobre la marcha.
*   **En contra:** el paso 3 completo (huella de aprobación, transacción de varios pasos, aprobaciones pequeñas)
    sobra si ella hace el clic final.
*   **Motivo del rechazo:** con `solo_rellenar`, el paso 3 se reduce al comprobante. Rechazada por el autor; ver P4
    del brief.

### Cómo se aprueba un envío

#### A3. Cola de aprobaciones con huella (diseño del brief, paso 3)

*   **A favor:** permite que la IA envíe sola después de una aprobación exacta, y ella no tiene que estar frente al
    navegador.
*   **En contra:**
    *   necesita leer todos los valores de la página, incluidos los que rellena el portal, y los marcos de otro
        dominio;
    *   tiene casos sin resolver: formularios de varios pasos, direcciones que cambian en cada sesión, y la
        aprobación que se pierde o vuelve a quedar disponible si el clic falla;
    *   después de aprobar, el chat tiene que seguir abierto para enviar.
*   **Motivo del rechazo:** el clic de ella es la aprobación y queda atado a lo que ella ve en pantalla, sin leer la
    página entera. Rechazada por el autor para el piloto; ver P4 y P5 del brief. Vuelve a considerarse después.

#### A4. Que el código repita el envío registrado («la IA nunca envía»)

*   **A favor:** la IA nunca toca el botón final.
*   **En contra:** hay que grabar y repetir el envío de cada portal.
*   **Motivo del rechazo:** la repetición se rompe en cuanto el portal cambia su diseño, y en `solo_rellenar` el
    problema no existe porque el envío lo hace ella. Rechazada por el autor; ver P4 del brief.

#### A5. Primera versión sin navegador en sitios ajenos (propuesta 2 de los revisores del brief)

*   **A favor:** elimina Node, los puertos, la puerta entera y el riesgo de agotar el cupo de la suscripción.
*   **En contra:** ella no se ahorra llenar formularios, que es una de las dos ganancias prometidas.
*   **Motivo del rechazo:** rellenar formularios es una de las dos ganancias del piloto. Rechazada por el autor;
    ver D17 del brief. **Advertencia:** el bloque A2 solo se hace si la sesión con ella (bloque B) confirma que sus
    portales tienen formularios que valga la pena rellenar. Si no, esta alternativa vuelve a ser la más barata.

### Cómo se bloquea a la IA mientras ella envía

#### A10. Pestaña congelada, con un estado por pestaña

*   **A favor:** la IA puede seguir con otra oferta en otra pestaña mientras ella envía.
*   **En contra:**
    *   el estado vive en memoria y se pierde al reiniciar la puerta o con dos chats;
    *   las pestañas se identifican por posición, que cambia cuando ella cierra una;
    *   se puede cerrar o navegar una pestaña congelada desde otra;
    *   la IA la descongela cambiando el estado de la postulación.
*   **Motivo del rechazo:** cada una de esas fallas rompe la meta 3, y cerrarlas todas cuesta más que el candado
    global. Rechazada por el autor; ver la decisión A de la revisión.

#### A11. Candado por pestaña con los identificadores de CDP

*   **A favor:** las pestañas se identifican con los ids estables de `/json/list` (`navegador.py:75-81`) y el estado
    se guarda en la base, así que sobrevive a los reinicios.
*   **En contra:** la IA sigue pudiendo robarle el foco a la pestaña que ella está revisando, y la puerta tiene que
    cruzar dos fuentes (Playwright y CDP) para saber dónde está.
*   **Motivo del rechazo:** conserva el trabajo en paralelo, que en un piloto de una persona aporta poco frente al
    riesgo del foco. Rechazada por el autor; ver la decisión A de la revisión.

#### A12. Candado por dirección guardado en la base

*   **A favor:** solo se bloquea la dirección del formulario que espera, y la IA puede seguir en otras.
*   **En contra:** un formulario de varios pasos cambia de dirección, y la misma oferta puede abrirse con otra
    dirección.
*   **Motivo del rechazo:** la dirección no identifica un formulario con seguridad. Rechazada por el autor; ver la
    decisión A de la revisión.

### Cómo se sabe que ella envió

#### A6. La puerta compara la página cuando la IA la vuelve a leer

*   **A favor:** es poco código y la detección la hace la puerta, no la IA.
*   **En contra:** depende de que alguien vuelva a leer la página y de que el portal muestre un texto de
    confirmación reconocible.
*   **Motivo del rechazo:** la diferencia con la opción elegida es que la IA lo reporta sin código nuevo en la
    puerta; las dos opciones terminan en la confirmación de ella. Rechazada por el autor; ver D3 del brief.

#### A7. La puerta escucha el navegador por CDP en segundo plano

*   **A favor:** es la única detección que no depende ni de la IA ni de ella.
*   **En contra:**
    *   necesita un cliente websocket, sea una dependencia nueva o unas 100 líneas propias;
    *   necesita reconectarse cuando algo se cae;
    *   los guardados automáticos del portal dan falsos positivos;
    *   deja de funcionar si ella cierra la sesión antes de enviar.
*   **Motivo del rechazo:** su costo es alto frente a lo que aporta en un piloto de una persona. Rechazada por el
    autor; ver D3 del brief.

### Cómo se protege el perfil

#### A13. Dos copias del perfil: borrador y revisada

*   **A favor:** la IA usa solo datos revisados en los CV y en los formularios.
*   **En contra:**
    *   la entrevista no puede leer su propio borrador y pisa sus cambios;
    *   hay lectores que no pasan por la copia revisada (`cv.idioma_de`, notas y respuestas);
    *   en los formularios la IA escribe lo que sabe por la conversación, así que la copia revisada protege poco;
    *   necesita una migración y una tercera ruta de archivos.
*   **Motivo del rechazo:** cuesta mucho para lo que protege. El sello hace la misma garantía para lo que genera el
    código. Rechazada por el autor; ver la decisión B de la revisión y D6 del brief.

### Cómo llegan los documentos

#### A8. Ella pasa cada archivo desde el panel

*   **A favor:** la IA no participa y ella dice qué quiere hacer con cada archivo.
*   **En contra:** si ella no abre el panel, nada avanza, y es una ventana más que tiene que entender.
*   **Motivo del rechazo:** depende de que ella se acuerde de «subir» cada archivo; con el barrido igual clasifica en
    el panel. Rechazada por el autor en favor del barrido automático; ver D9 del brief.

#### A9. La IA archiva con `documento_archivar` y ella clasifica

*   **A favor:** la IA puede ayudarla en el chat («ya guardé tu diploma»).
*   **En contra:** la IA ve los nombres de los archivos, que pueden traer la cédula, y son dos herramientas más.
*   **Motivo del rechazo:** expone los nombres de archivo a la IA. Rechazada por el autor en favor del barrido
    automático; ver D9 del brief.

### Alternativas del brief que siguen rechazadas

*   **App nueva desde cero.** Postulador ya resuelve la mayor parte. Ver el brief, «Alternativas».
*   **Operar por terminal.** Ella no debe verla. Rechazada por el autor; ver D1 del brief.
*   **App de escritorio propia con instalador y chat propio.** Se usa el cliente oficial de Claude más el panel.
    Rechazada por el autor; ver D1 del brief.
*   **VS Code como entorno.** La app de escritorio intimida menos. Rechazada por el autor; ver D1 del brief.
*   **Pestaña de chat normal o Cowork con un MCP local** (propuesta 7 de los revisores del brief). En ese modo no se
    carga `.mcp.json`, así que la puerta no existe. Rechazada por la evidencia del paso 0 (10 nov); ver D15.
*   **Índice Markdown que edita la IA.** Duplica o pierde filas; la fuente es la base de datos. Rechazada con
    acuerdo del autor; ver el brief, «Alternativas».
*   **Que el autor opere una instalación con un perfil por familiar.** Las suscripciones son personales, el autor
    tendría credenciales ajenas y aplica la Ley 1581. Ver el brief, «Alternativas».
*   **Verificar los términos de uso de cada portal.** Probablemente inviable para una persona, como dice el brief;
    ella postula con su propia cuenta y hace el clic. Ver el brief, «Alternativas».
*   **Correo personal con una etiqueta para las respuestas.** La IA no lee correo en el piloto. Rechazada por el
    autor; ver P6 del brief.

### Aplazadas para después del piloto

*   **La puerta es dueña del navegador** (Playwright dentro de la puerta, sin puertos 8931 ni 9222). Sería necesaria
    si algún día se quiere detener la petición de red. No hace falta en `solo_rellenar`.
*   **Rellenar con `formulario_campo(postulación, campo, dato_id)`,** donde la IA señala un dato del perfil y el
    código escribe el valor literal. Resolvería la veracidad de los campos cortos, pero cambia toda la forma en que
    la skill rellena. Conviene evaluarla con los comprobantes del piloto en la mano.
*   **Subir documentos por identificador (`doc:<id>`).** Abre un camino para que una oferta maliciosa pida subir la
    cédula. Ver la decisión F de la revisión.
*   **Búsqueda determinista por portal.** Depende de qué canales salgan de la sesión con ella (pregunta 1).
*   **Modelo de difusión para rellenar.** Aparcado: ataca el cuello de botella equivocado y exige una clave de API
    aparte. Ver el brief.

--------------------------------------------------------------------------------

## Plan de implementación detallado

### Orden

| Bloque | Qué | Termina cuando |
|---|---|---|
| A0 | Capturar las respuestas reales de Playwright MCP 0.0.84 que la puerta va a leer, y comprobar `Host` y `Origin` | Las respuestas quedan en `tests/fixtures/playwright_0_0_84/` y el resultado en su `LEEME.md` |
| A1 | Común: encierro, tope en `equipo.json`, `diagnostico`, filtro de argumentos, quitar la pestaña Agente, `tareas.py` y `plantilla_guardar`, acceso directo al panel | Pasan `unittest`, el e2e del panel y la parte A1 de la prueba en sesión real |
| B | Sesión del autor con ella | Quedan resueltas en `concepts_brief.md` las preguntas 1 y 2, los campos de derecho, los tipos de documento, `PASO_SEGURO_POR_SITIO` y si A2 se hace |
| A2 | Formularios: estados por actor, candado, borrador, `formulario_listo`, comprobantes, tablero y contención | Pasan `unittest`, la prueba de contención y la parte A2 de la prueba en sesión real |
| C | Perfil de abogada con sello, CV de varias páginas, documentos, entrevista y acceso directo a la IA | Pasan `unittest`, la prueba de contención completa y la prueba en sesión real completa |

Cada bloque tiene su punto de control: no se empieza el siguiente sin pasar sus pruebas. Nada de A2 ni de C se
programa antes de que termine B. Si B concluye que sus portales no tienen formularios que valga la pena rellenar, A2
no se hace y se vuelve a considerar A5.

### Decisiones mecánicas que este plan fija

*   El tope vive en `%LOCALAPPDATA%\Postulador\equipo.json` y falla cerrado a `solo_rellenar`. No hay
    `postulador.json`, ni `POSTULADOR_ARRANQUE`, ni `--arranque`.
*   No hay columna `enviada_por` ni migración de estados: el estado nuevo `reportada` y la tabla de transiciones
    hacen ese trabajo.
*   Si el perfil tiene `carrera`, `cv_generar` con `motor='auto'` usa el motor HTML. `motor_docx.py` no se cambia
    en el piloto, salvo para reutilizar su lectura de párrafos.
*   Las subidas a portales solo aceptan `cv:<nombre>`, en `browser_file_upload` y en `browser_drop`. Una ruta suelta
    se rechaza siempre.
*   Se borra `tareas.py`, que solo usaban las rutas del panel que se quitan. Los comandos de terminal del autor
    (`ejecutar`, `programar`, `conectar`) no se tocan.
*   Los mensajes que las pruebas comprueban se fijan como subcadenas en el ítem que los crea.

### Bloque A0

#### 1. `tests/fixtures/playwright_0_0_84/` (crear)

*   **Tipo:** datos de prueba.
*   **Cambios:** guardar como texto la respuesta real de:
    *   `browser_tabs` con `action: list`, con dos y con tres pestañas;
    *   `browser_snapshot` de un formulario con campos, casillas y un botón, para las referencias y los roles;
    *   `browser_take_screenshot` con `{"type": "png", "fullPage": true, "scale": "css"}`, la respuesta JSON-RPC
        completa.

    Así se confirma si la imagen llega como contenido `image` en base64 o como un archivo. Si llega como archivo,
    `formulario_listo` lee ese archivo en lugar del base64.
*   **Comprobaciones de seguridad,** anotadas en `LEEME.md` de la misma carpeta:
    *   Playwright MCP 0.0.84 rechaza las peticiones a :8931 con un `Host` o un `Origin` ajenos;
    *   el navegador no se lanza con `--remote-allow-origins=*` (`navegador.py:88`).

    Si alguna falla, se anota en la tabla de riesgos antes de seguir.

### Bloque A1, común

#### 2. `postulador/__init__.py` (modificar)

*   **Tipo:** módulo base.
*   **Cambios:**
    *   `__version__ = '0.<n>'`, que usan `diagnostico` y el README.
    *   `archivo_equipo()` devuelve la ruta de `equipo.json`, junto a `archivo_ubicacion()` (`__init__.py:13-15`).
    *   `equipo()` lee el archivo y devuelve `{'nivel_maximo': ..., 'arranque': ..., 'problema': ...}`. Si falta, no
        es JSON o el nivel no está en `NIVELES`, devuelve `nivel_maximo='solo_rellenar'` y un `problema` en español.
        Nunca lanza.
    *   `nivel_maximo()` y `carpeta_arranque()` leen de `equipo()`.

#### 3. `postulador/arranque.py` (modificar)

*   **Tipo:** generador de la carpeta de arranque.
*   **Cambios:**
    *   `DENEGADAS` suma `Read`, `Glob` y `Grep`.
    *   `crear(carpeta=None, nivel_maximo='solo_rellenar', accesos=True)` escribe `equipo.json` de forma atómica
        (archivo temporal y `os.replace`).
    *   Con `accesos=True` y en Windows, crea «Panel de Postulador.lnk» en el Escritorio real, que puede estar dentro
        de OneDrive. La ruta se pide con `[Environment]::GetFolderPath('Desktop')`, y el `.lnk` se crea con
        `WScript.Shell`, las dos cosas desde un `powershell -NoProfile` que lanza `arranque` (lo corre el autor, no
        la IA).
        *   Destino: la ruta absoluta de `pythonw.exe`, junto a `sys.executable`. Si no existe, `python.exe` con la
            ventana minimizada (`WindowStyle = 7`).
        *   Argumentos: `-m postulador panel --abrir`. Carpeta de trabajo: `RAIZ`.
    *   `diagnostico()` devuelve el diccionario de la sección 1 del plan técnico. `permisos_al_dia` compara el `deny`
        de `<carpeta>/.claude/settings.json` con `DENEGADAS`.
    *   `INSTRUCCIONES` suma la regla de inicio de la sección 1 y le dice a ella que use el acceso directo «Panel de
        Postulador» para ver el tablero.

#### 4. `postulador/__main__.py` (modificar)

*   **Tipo:** comandos del autor.
*   **Cambios:**
    *   `arranque` suma `--nivel-maximo`, con las opciones de `registro.NIVELES` y `solo_rellenar` por defecto.
    *   `panel` suma `--abrir`, que abre el navegador predeterminado. Si el puerto ya está ocupado por un panel, solo
        abre la dirección y termina.
    *   `doctor` imprime `arranque.diagnostico()`.

#### 5. `postulador/registro.py` (modificar, bloque A1)

*   **Tipo:** registro de postulaciones y políticas.
*   **Cambios:**
    *   `ORDEN_NIVELES = tuple(reversed(NIVELES))`;
    *   `nivel_de_url` devuelve el menor entre el nivel calculado y `nivel_maximo()`;
    *   `fijar_politica` rechaza los niveles por encima del tope con un `ValueError` que contiene «por encima del
        tope»;
    *   `consultar_politica` devuelve `nivel` (el efectivo) y `tope`.

#### 6. `postulador/mcp_server.py` (modificar, bloque A1)

*   **Tipo:** servidor MCP `postulador`.
*   **Cambios:**
    *   **Herramienta nueva:** `diagnostico` (`arranque.diagnostico`).
    *   **Filtro de argumentos:** `_llamar` rechaza todo argumento que no esté en las `properties` de la herramienta,
        con un error que contiene «argumento no permitido».
    *   **Herramientas que se ocultan con el tope:** si `nivel_maximo()` es `solo_rellenar` o `solo_preparar`,
        `_lista_herramientas()` omite `aprobacion_solicitar`, `aprobacion_consultar`, `aprobaciones_listar` y
        `plantilla_guardar`, y `_llamar` las rechaza.
    *   **`panel_abrir`** llama a `panel.asegurar(abrir=True)`.
    *   **Descripciones:** `politica_consultar` menciona el tope.

#### 7. `postulador/panel.py` (modificar, bloque A1)

*   **Tipo:** servidor del panel.
*   **Cambios:**
    *   **Apertura:**
        *   `asegurar(abrir=False)`: espera hasta 5 segundos a que responda `/api/resumen`; si `abrir` es
            verdadero, abre la dirección con `os.startfile` en Windows y `webbrowser.open` en los demás sistemas;
        *   `main(puerto, abrir=False)`.
    *   **Se quitan:**
        *   las rutas `GET /api/tareas`, `GET /api/tareas/<id>`, `POST /api/tareas`, `POST /api/conectar` y
            `POST /api/cv/<nombre>/agente`;
        *   la función `conectar` y el import de `tareas`.
    *   **Ajustes:** `GET /api/ajustes` incluye `nivel_maximo`, y `POST` rechaza niveles por encima del tope.

#### 8. `postulador/tareas.py` (borrar)

*   **Motivo:** solo lo usaban las rutas del panel que lanzan una IA oculta. El brief pide quitarlas.

#### 9. `postulador/web/index.html`, `app.js` y `styles.css` (modificar, bloque A1)

*   **Cambios:**
    *   se quitan el enlace «Agente» (`index.html:12`), la vista `agente`, el botón «Pedir al agente» de la vista de
        CV (`app.js:214`), «Conectar» (`app.js:99`) y las constantes `LOGIN` y `motores` que solo usaba esa vista;
    *   Ajustes no ofrece niveles por encima de `nivel_maximo` y muestra «Tope de este equipo: <nivel>».

#### 10. `skills/postulador/SKILL.md` y `CLAUDE.md` de la carpeta de arranque (modificar, bloque A1)

*   **Cambios:**
    *   **Regla de inicio** de la sección 1, con el rechazo de cualquier `mcp__claude_ai_*`;
    *   **tabla de niveles:** explica que el tope manda;
    *   **prohibiciones:** no proponer comandos y no usar «firmar»;
    *   **la línea del panel** deja de decir «cola de firma».

    El `CLAUDE.md` de la carpeta de arranque sale de `INSTRUCCIONES` (ítem 3).

#### 11. `tests/test_postulador.py` (modificar, bloque A1)

*   **Tipo:** pruebas unitarias.
*   **Pruebas que se reescriben:**
    *   `ArranqueTests`: llama a `crear(..., accesos=False)`; comprueba `Read`, `Glob` y `Grep` en `deny`,
        `equipo.json` con el nivel que se pidió y que `diagnostico` detecta un `settings.json` alterado.
    *   `PanelTests`: las rutas quitadas responden 404.
    *   `McpTests`: `diagnostico` aparece; con el tope, las herramientas de aprobación y `plantilla_guardar` no
        aparecen.
*   **Pruebas nuevas:**
    *   `EquipoTests`: archivo ausente, corrupto o con un nivel inválido da `solo_rellenar` y un `problema`, sin
        excepción;
    *   `NivelMaximoTests`: con el tope en `solo_rellenar`, un sitio en `enviar_solo` y uno desconocido quedan en
        `solo_rellenar`; `fijar_politica('x', 'aprobar')` falla; `consultar_politica` devuelve el nivel efectivo;
    *   `ArgumentosTests`: `postulacion_actualizar` con `por='persona'` falla con «argumento no permitido»;
    *   `AccesoDirectoTests`: con `accesos=True`, la creación del `.lnk` se prueba simulando el `subprocess`, y se
        elige `pythonw.exe` con ruta absoluta.

    Todas las pruebas ponen `LOCALAPPDATA` en una carpeta temporal, para no tocar el `equipo.json` real.

#### 12. `tests/e2e_panel.py` (modificar, bloque A1)

*   **Cambios:** se quita el dato de prueba de `tareas/` y las comprobaciones de la pestaña Agente. Se comprueba que
    Ajustes muestra el tope. Se ejecuta con `python -m tests.e2e_panel`.

#### 13. `docs/piloto/instalacion.md` (crear)

*   **Tipo:** lista de verificación del autor.
*   **Pasos:**
    1.  instalar Python y Node;
    2.  clonar el repositorio fuera de OneDrive, por ejemplo en `%LOCALAPPDATA%\Postulador\codigo`;
    3.  `pip install -r requirements.txt`;
    4.  `python -m postulador arranque`;
    5.  en claude.ai, en la cuenta de ella, desactivar todos los conectores;
    6.  abrir el navegador dedicado e iniciar sesión con ella en sus portales;
    7.  abrir una sesión nueva en la carpeta de arranque y comprobar `diagnostico` sin `problemas`;
    8.  probar el acceso directo «Panel de Postulador».

    Para actualizar: `git pull`, `python -m postulador arranque`, y cerrar y volver a abrir la app de Claude para
    que los servidores arranquen con el código nuevo.

#### 14. `docs/piloto/pruebas_en_sesion.md` (crear)

*   **Tipo:** prueba manual en la app de escritorio.
*   **Parte A1:**
    *   `diagnostico` sin `problemas`;
    *   `Read`, `Glob`, `Grep` y `plantilla_guardar` no están en la lista de herramientas;
    *   una sesión abierta en la carpeta con un conector activo, en la que la IA se niega;
    *   el acceso directo «Panel de Postulador» abre el panel sin Claude.
*   **Partes A2 y C:** se completan en sus bloques (ítems 31 y 43).

#### 15. `README.md` (modificar, bloque A1)

*   **Cambios:**
    *   documenta `arranque --nivel-maximo`, `equipo.json` y `panel --abrir`;
    *   explica el acceso directo al panel;
    *   enlaza `docs/piloto/`.

### Bloque B

#### 16. `docs/piloto/sesion_con_ella.md` (crear antes de la sesión)

*   **Tipo:** guía de la sesión.
*   **Qué hay que averiguar:**
    *   dónde busca hoy y en qué sitios postula;
    *   si esos sitios tienen formularios que valga la pena rellenar. Si no, A2 no se hace y se vuelve a considerar
        A5;
    *   qué botones intermedios tienen esos formularios («Siguiente», «Continuar»), para fijar
        `PASO_SEGURO_POR_SITIO`;
    *   cuántas páginas tiene su CV y cuántas acepta el mercado legal: así se fija `paginas_maximas`;
    *   qué datos de abogada le piden los formularios;
    *   qué documentos le piden;
    *   qué palabras del panel no entiende.

#### 17. `concepts_brief.md` (modificar después de la sesión)

*   **Cambios:** los resultados de la sesión entran como decisiones nuevas en el registro, y las preguntas 1 y 2 de
    este diseño quedan resueltas.

### Bloque A2, formularios

Solo si B confirma que hay formularios que valga la pena rellenar.

#### 18. `postulador/registro.py` (modificar, bloque A2)

*   **Cambios:**
    *   **Estado nuevo** `reportada` en `ESTADOS`, fuera de `ENVIADAS`.
    *   **Tabla `comprobantes`:** `conexion()` la crea con sus disparadores, igual que `aprobaciones._conexion`.
    *   **Transiciones:** un diccionario `TRANSICIONES = {actor: {(desde, hasta), ...}}` con la tabla de la sección 4.
        `registrar(..., actor='persona')` y `actualizar(..., actor='persona')` lo consultan; un cambio que no está
        falla con un `ValueError` que contiene «no le corresponde». Con el tope en `aprobar` o más, la IA suma
        `por_aprobar` y `enviada`.
    *   **`accion_persona(id, accion, motivo='')`,** con las acciones `la_envie`, `ya_no`, `corregir`,
        `ya_estaba_enviada`, `avanzo` y `rechazada` de la tabla de la sección 4. `ya_estaba_enviada` además anota un
        incidente en `actividad`.
    *   **`seguimiento_hecho(id, nota, actor)`** solo acepta `actor='persona'` cuando el tope es `solo_rellenar` o
        menos.
    *   **Consultas:**
        *   `candado()` devuelve la primera postulación en `rellenada` o `reportada`, o `None`;
        *   `listar` acepta varios estados separados por coma y añade el `id` del último comprobante;
        *   `olvidadas(horas=24)` devuelve las postulaciones en `rellenada` o `reportada` cuyo último comprobante
            tiene `fin` de hace más de 24 horas.

#### 19. `postulador/comprobantes.py` (crear)

*   **Tipo:** módulo de datos.
*   **Cambios:**
    *   **`crear(postulacion_id, url, inicio, fin, campos, clics, archivos, cv, imagen_png, envios_bloqueados)`.**
        Reserva el id, escribe `comprobantes/c<id>.png` en la carpeta de datos con su SHA-256 y, en una sola
        transacción, inserta la fila y llama a `registro.actualizar(postulacion_id, 'rellenada', actor='puerta')`
        con la misma conexión. Si la transacción falla, borra el PNG.
    *   **Lectura:** `leer(id)`, `ultimo_de(postulacion_id)` y `ruta_imagen(id)`. `ruta_imagen` comprueba que la
        ruta quede dentro de `comprobantes/`.

#### 20. `postulador/puerta.py` (modificar, bloque A2)

*   **Tipo:** servidor MCP de la puerta.
*   **Estado:** se mantienen `url`, `etiquetas` y `pestana_propia`, y se suma `borrador` (o `None`). No se añade
    estado por pestaña.
*   **Orden en `atender()`:**
    1.  `formulario_listo` y `formulario_abandonar` se atienden aquí, sin reenviarlas y antes de `decidir()`;
    2.  todo argumento `paths` (en `browser_file_upload` y en `browser_drop`) debe ser `cv:<nombre>`, y se traduce a
        la ruta real con `cv.pdf_de`. Cualquier otra cosa se rechaza con `PROHIBIDO`;
    3.  `decidir()` corre con la ruta real, así que `ruta_ajena` sigue como segunda revisión;
    4.  se reenvía a Playwright.
*   **`decidir()`,** en este orden:
    1.  `prohibido()` (sin cambios de fondo).
    2.  **Candado.** Si `registro.candado()` devuelve una postulación, solo pasan `browser_snapshot`,
        `browser_take_screenshot`, `browser_wait_for` y `browser_tabs` con `action: list`. El mensaje contiene
        «espera que la envíes» y el cargo y la empresa.
    3.  **Un borrador a la vez.** Con un borrador abierto, una escritura en otro dominio se bloquea con un mensaje
        que contiene «formulario_listo».
    4.  **Regla de envío con borrador** de la sección 2, con `PASO_SEGURO_POR_SITIO`.
    5.  Las reglas de nivel de hoy, con el nivel ya limitado por el tope.
*   **Borrador:** tras cada escritura o clic que tuvo éxito, se añade `{herramienta, campo, valor, hora}`, con la
    etiqueta de `etiquetas` o la marca «etiqueta según la IA». Los intentos de envío bloqueados suman
    `envios_bloqueados`.
*   **`formulario_listo` y `formulario_abandonar`:** las precondiciones y los pasos de la sección 3. Esquemas:
    `{postulacion_id: integer}` y `{}`. Se añaden a `tools/list` después del filtro de `PERMITIDAS`, en las dos
    ramas.
*   **Mensajes:** `AVISAR` pasa a decir: «Deja el formulario listo, llama a formulario_listo con el id de la
    postulación y dile al usuario que revise el navegador y pulse Enviar él mismo».

#### 21. `postulador/cv.py` (modificar, bloque A2)

*   **Cambios:** `pdf_de(nombre)` exige `nombre == slug(nombre)` y devuelve `_resumen(carpeta)['pdf']`
    (`cv.py:263`) de `carpeta_cv()/nombre`, o `FileNotFoundError`. Así nunca elige la carta.

#### 22. `postulador/mcp_server.py` (modificar, bloque A2)

*   **Cambios:**
    *   `postulacion_registrar` y `postulacion_actualizar` pasan `actor='ia'`, y el `enum` de `estado` en su esquema
        es el de la IA según el tope;
    *   con el tope en `solo_rellenar` o menos, `seguimiento_hecho` no aparece y `_llamar` la rechaza.

#### 23. `postulador/panel.py` (modificar, bloque A2)

*   **Cambios:**
    *   `GET /api/postulaciones?estado=rellenada,reportada`;
    *   `GET /api/olvidadas`;
    *   `GET /api/comprobantes/<id>` (JSON sin la ruta de la imagen) y `GET /api/comprobantes/<id>/imagen`
        (`image/png`);
    *   `POST /api/postulaciones/<id>` cambia su cuerpo a `{accion, motivo}` y llama a `registro.accion_persona`.
        Como hoy, exige la cabecera `X-Panel-Token`;
    *   `POST /api/seguimientos/<id>` cambia su cuerpo a `{accion}` y llama a `registro.seguimiento_hecho` con
        `actor='persona'`;
    *   `GET /api/aprobaciones` devuelve `[]` si el tope es `solo_rellenar` o menos.

#### 24. `postulador/web/index.html`, `app.js` y `styles.css` (modificar, bloque A2)

*   **Cambios:**
    *   **«Por firmar» pasa a «Lista para enviar»,** con `id="cuenta-lista"`, alimentada por la ruta del ítem 23. El
        refresco de `app.js:302-312` pasa a esa ruta. Muestra los botones de la sección 4.
    *   **Vista de comprobante:** título «Lo que rellenó el asistente», tabla de campos, casillas, archivos, CV y
        horas, la imagen de la página y la advertencia de la sección 5.
    *   **Filas del tablero:** el estado con palabras y los botones «Avanzó» y «Rechazada» en las enviadas.
    *   **Aviso de olvidadas** en un contenedor `#olvidadas` arriba del contenido, con `GET /api/olvidadas` y el
        texto del recorrido 4.
    *   **Restos que se quitan:** «Pedir tu firma» (`app.js:82`), `data-sello="Firmada"` (`styles.css:52`) y todo
        texto con «firmar».
    *   **En el equipo del autor**, con el tope en `aprobar` o más, la vista de aprobaciones sigue igual.
    *   Estilos para el aviso, los estados y la vista de comprobante, con los mismos tokens de color del panel.

#### 25. `skills/postulador/SKILL.md` y sus guías (modificar, bloque A2)

*   **Cambios en `SKILL.md`:**
    *   en `solo_rellenar`, la IA registra la postulación como `preparada`, rellena, llama a `formulario_listo`, dice
        «revisa la ventana del navegador y pulsa Enviar tú» y espera a que ella la resuelva;
    *   la regla 6 pasa a: «Reporta `reportada` solo si en el turno siguiente ves la confirmación del portal. Ella
        confirma en el panel»;
    *   si la oferta no encaja a mitad del formulario, `formulario_abandonar`;
    *   no marcar `avanzo`, `rechazada` ni seguimientos;
    *   subir archivos solo con `cv:<nombre>`.
*   **Guías:** `referencias/rutina.md:13-14`, `referencias/resultados.md:13` y `referencias/entrevistas.md:11` dejan
    de pedir marcar `avanzo`, `rechazada` o aprobaciones cuando el tope es `solo_rellenar`.

#### 26. `tests/test_postulador.py` (modificar, bloque A2)

*   **Pruebas que se reescriben:**
    *   `test_sube_solo_desde_cv_y_documentos` pasa a usar `cv:<nombre>` y comprueba que una ruta suelta falla;
    *   `test_lee_la_url_del_listado_de_pestanas` y `test_firma_vale_una_sola_vez_y_solo_en_su_sitio` se mantienen,
        porque `Puerta.url` y el flujo `aprobar` no cambian; solo se ajustan si cambia el formato de los datos de A0;
    *   `test_la_puerta_abre_pestana_propia_antes_de_navegar` se mantiene;
    *   `ResultadosTests` usa `actor='persona'` donde marca respuestas;
    *   `PanelTests` y `McpTests` suman las rutas y herramientas de este bloque.
*   **Pruebas nuevas:**
    *   `TransicionesTests`: cada cambio prohibido falla con su actor; `reportada` no cuenta como enviada;
        `la_envie` genera el seguimiento; `ya_estaba_enviada` anota un incidente; `olvidadas` respeta las 24 horas;
    *   `ComprobantesTests`: `crear` escribe el PNG, la fila y el estado en una transacción; si la transacción falla,
        no queda el PNG; `update` y `delete` fallan por los disparadores; `ruta_imagen` no sale de `comprobantes/`;
    *   `CandadoTests`, con los datos de A0 y un servicio falso: con una postulación en `rellenada`, se bloquean
        escribir, hacer clic, navegar y cerrar; el candado sigue en una `Puerta()` nueva; con la base caída se
        bloquea; tras `la_envie` se quita;
    *   `BorradorTests`: la escritura y el clic en una casilla se anotan con la etiqueta de la lectura; una etiqueta
        ausente queda como «etiqueta según la IA»; un clic sobre un botón se bloquea; una escritura en otro dominio
        se bloquea; `formulario_listo` sin borrador falla y una segunda llamada falla;
    *   `SubidaCvTests`: `cv:<nombre>` se resuelve y pasa; una ruta suelta dentro de `cv/` se rechaza, también con
        `browser_drop`; `cv:../x` y `cv:Nombre Con Espacios` se rechazan;
    *   `PortalPruebaTests`: la `url_prohibida` de producción bloquea `http://127.0.0.1:9000`.

#### 27. `tests/portal_falso.py` (crear)

*   **Tipo:** herramienta de prueba. No empieza por `test`, así que `unittest discover` no la ejecuta.
*   **Cambios:** un `http.server` con estas páginas:
    *   formulario con botón «Enviar postulación», casillas y botones de opción;
    *   formulario de dos pasos con «Siguiente»;
    *   botón de solo icono;
    *   formulario con diálogo `confirm`;
    *   un marco de otro origen;
    *   enlace a una página de pago y enlace al panel;
    *   casilla «Declaro bajo juramento»;
    *   página de confirmación «Hemos recibido tu postulación».

    Registra cada `POST` recibido en una lista que el corredor consulta.

#### 28. `tests/puerta_prueba.py` (crear)

*   **Tipo:** envoltorio de prueba.
*   **Cambios:** importa `postulador.puerta`, reemplaza `url_prohibida` por una versión que además permite el origen
    exacto que recibe por argumento, y llama a `main()`. Solo lo usa `tests/contencion.py`.

#### 29. `tests/contencion.py` (crear)

*   **Tipo:** prueba de contención de nivel 1. Se ejecuta a mano con `python -m tests.contencion` y necesita Node y
    Chromium.
*   **Preparación:**
    1.  se niega a correr si 9222 u 8931 están ocupados;
    2.  levanta `portal_falso` en un puerto libre;
    3.  crea carpetas temporales de datos, de arranque y de `LOCALAPPDATA`, con `equipo.json` en `solo_rellenar`,
        y un perfil de navegador temporal (`navegador.guardar_configuracion`);
    4.  lanza `tests/puerta_prueba.py` como subproceso;
    5.  manda por stdio llamadas JSON-RPC con guion, sin IA.
*   **Ataques:** los de «Pruebas del piloto».
*   **Pasa si** se cumplen las cuatro condiciones de «Pruebas del piloto».

#### 30. `tests/e2e_panel.py` (modificar, bloque A2)

*   **Cambios:** se añaden la vista «Lista para enviar» con un comprobante, el aviso de olvidadas y que en ningún
    texto visible aparezca «firmar». El e2e de la mesa de firmas se conserva solo con el tope en `aprobar`.

#### 31. `docs/piloto/pruebas_en_sesion.md` (modificar, bloque A2)

*   **Parte A2:** una postulación de punta a punta en el portal falso, con el candado, el reporte de la IA y la
    confirmación en el panel; una sesión nueva con una postulación en `rellenada`, en la que la IA no puede
    escribir.

### Bloque C

#### 32. `postulador/paquetes/derecho.json` (crear)

*   **Tipo:** paquete de carrera.
*   **Cambios:**
    *   el esquema de la sección 6;
    *   los campos, tipos de documento y `paginas_maximas` que salgan del bloque B.

    Lo escribe el autor con ayuda de la IA y lo revisa (P9).

#### 33. `postulador/carreras.py` (crear)

*   **Tipo:** módulo.
*   **Funciones:**
    *   `cargar(id)` lee `paquetes/<id>.json`; el `id` solo admite `[a-z_]+`;
    *   `validar(campos, paquete)` devuelve los errores por campo;
    *   `faltantes(perfil)`;
    *   `tipos_documento(id)`;
    *   `paginas_maximas(perfil)`, que vale 1 si no hay carrera.

#### 34. `postulador/perfil.py` (modificar)

*   **Cambios:**
    *   **`REQUERIDOS`:** se quitan `publications` y `projects`. Si faltan, se leen como `[]`.
    *   **Campos nuevos:** `schema_version: 1`, `carrera`, `campos_carrera`, `revisado_el` y `revisado_huella`.
    *   **`guardar(perfil, idioma, por='ia')`:**
        *   valida `campos_carrera` con `carreras.validar`;
        *   con `por='ia'`, conserva los campos sensibles del archivo y rechaza cambiarlos con un error que contiene
            «solo desde el panel»;
        *   con `por='persona'`, renueva el sello solo si estaba vigente antes del cambio;
        *   asigna `id` a las entradas de `education` que no lo tengan (`f1`, `f2`…), sin cambiar los que ya
            existen.
    *   **Funciones nuevas:**
        *   `huella(perfil)`: SHA-256 del JSON canónico sin `revisado_el` ni `revisado_huella`;
        *   `sello_vigente(idioma)`;
        *   `marcar_revisado(idioma)`: fija el sello y copia el perfil a `respaldos/revisado<sufijo>.json`, las dos
            cosas de forma atómica (archivo temporal y `os.replace`);
        *   `leer(idioma, para_ia=False)`: con `para_ia=True`, tapa los campos sensibles.

#### 35. `postulador/arranque.py` (modificar, bloque C)

*   **Cambios:** migración única: si existe un perfil sin `schema_version`, `arranque` lo sella con
    `perfil.marcar_revisado`. Es el perfil del autor, que ya estaba en uso.

#### 36. `postulador/cv.py` (modificar, bloque C)

*   **Cambios:**
    *   `generar` y `generar_carta` empiezan con `perfil.sello_vigente`; si no vale, fallan con «revisa tu perfil en
        el panel»;
    *   `if paginas != 1` (`cv.py:185`) pasa a `if paginas > carreras.paginas_maximas(perfil)`, con un mensaje que
        dice el tope;
    *   se añade la sección `carrera` a los valores de la plantilla: título del paquete y lista «etiqueta: valor»
        con los campos que tengan `en_cv`, en el orden del paquete, escapados como las demás marcas;
    *   `motor='auto'` usa HTML si hay carrera.

#### 37. `postulador/plantillas/clasico.html`, `columna.html` y `editorial.html` (modificar)

*   **Cambios:** se añade la marca `{{carrera}}` después de `{{resumen}}`. Si está vacía, desaparece, igual que las
    demás secciones (`cv.py:71`).

#### 38. `postulador/documentos.py` (crear)

*   **Tipo:** módulo.
*   **Cambios:**
    *   la tabla `documentos` de la sección 7, creada en `registro.conexion()`;
    *   `barrer()`, que no hace nada si no hay carpeta de arranque e ignora los archivos modificados en los últimos
        10 segundos;
    *   `listar_para_ia()`, que barre y devuelve solo `id`, `tipo` y `nombre` de los documentos clasificados;
    *   `listar_para_panel()`, que barre y devuelve todos los datos;
    *   `clasificar(id, tipo, nombre, ia_puede_leer, vinculo)`; con `tipo='mi_cv'`, el código pone
        `ia_puede_leer=1`;
    *   `leer(id)`, con `ats.extraer_pdf`, `motor_docx.para_text`, la expresión regular de la sección 7 y los
        mensajes de imagen y de `pdfminer` ausente.

#### 39. `postulador/mcp_server.py` (modificar, bloque C)

*   **Cambios:**
    *   **Herramientas nuevas:** `documentos_listar`, `documento_leer` y `perfil_faltantes`.
    *   **`perfil_guardar`** pasa `por='ia'`, y `perfil_leer` pasa `para_ia=True`.
    *   **`cv_generar`** cambia su descripción: deja de decir «de una página» y nombra el tope del paquete.
    *   **ATS:** con un perfil de `carrera` `derecho`, `ats_evaluar` no aparece.

#### 40. `postulador/panel.py` (modificar, bloque C)

*   **Cambios:**
    *   **Documentos:**
        *   `GET /api/documentos` barre y lista;
        *   `POST /api/documentos/<id>` clasifica;
        *   `GET /api/documentos/<id>/archivo` sirve el archivo para que ella lo vea.
    *   **Perfil:**
        *   `GET /api/perfil/carrera` devuelve el paquete y los valores, sin tapar;
        *   `POST /api/perfil/carrera` guarda los campos, sensibles incluidos, con `por='persona'`;
        *   `GET /api/perfil/cambios` devuelve, campo por campo, el valor de `respaldos/revisado.json` y el actual;
        *   `POST /api/perfil/revisado` llama a `perfil.marcar_revisado`.

#### 41. `postulador/web/index.html`, `app.js` y `styles.css` (modificar, bloque C)

*   **Cambios:**
    *   **Enlaces nuevos** «Perfil» y «Documentos» en la navegación.
    *   **Pestaña Documentos:** los nuevos, sin clasificar, arriba; tipo, nombre visible, «La IA puede leerlo» y
        vínculo con un dato del perfil.
    *   **Pestaña Perfil:** arriba, el aviso «El asistente cambió tu perfil: revísalo», con la lista de cambios
        (antes y después) y el botón «Revisado»; debajo, la sección «Datos de abogada», generada desde el paquete.

#### 42. `skills/postulador/referencias/perfil.md`, `referencias/cv.md` y `carreras/derecho.md` (modificar y crear)

*   **Cambios:**
    *   `perfil.md` hace la entrevista en este orden: `documentos_listar`, `documento_leer` sobre «Mi CV»,
        `perfil_faltantes`, y luego preguntas solo por lo que falta;
    *   `perfil.md` copia los títulos tal cual y no escribe campos sensibles: le pide a ella que los ponga en el
        panel;
    *   `perfil.md` le pide a ella que marque «Revisado» al terminar;
    *   `cv.md:25` deja de decir «una página» y «DOCX si existe»;
    *   `derecho.md` es la guía de la entrevista para derecho, escrita con lo que salga del bloque B. Va en
        `carreras/` y no en `referencias/entrevistas.md`, que trata de entrevistas de trabajo.

#### 43. `skills/postulador/SKILL.md`, `docs/piloto/pruebas_en_sesion.md` y `README.md` (modificar, bloque C)

*   **Cambios:**
    *   la skill apunta a `carreras/<carrera>.md`;
    *   la prueba en sesión suma la parte C: que la entrevista avance con `perfil_faltantes`, que `documento_leer`
        sobre «Mi CV» funcione con `Read` denegado, que un documento sin permiso no se pueda leer y que `cv_generar`
        se niegue después de un cambio de la IA;
    *   el README documenta los documentos, el paquete de carrera y el sello.

#### 44. `docs/piloto/acceso_directo_ia.md`, `postulador/arranque.py` y `docs/piloto/elegir_carpeta.png` (crear y modificar)

*   **Cambios:**
    *   **Primero, investigar** si la app de escritorio de Claude acepta abrirse en una carpeta, por línea de
        comandos o por un enlace (pregunta 4). El resultado va en `acceso_directo_ia.md`.
    *   **Mientras no haya resultado, o si no lo acepta,** `arranque` copia `elegir_carpeta.png`, una imagen que toma
        el autor, y genera `LEEME.html` en la carpeta de arranque y su acceso directo en el Escritorio, con un solo
        paso.
    *   **Si lo acepta,** `arranque` crea «Postulador con Claude.lnk» en el Escritorio.

#### 45. `tests/test_postulador.py` (modificar, bloque C)

*   **Pruebas que se reescriben:** las que generan CV o cartas (`CvTests`, `EditorCvTests`, `CartaTests`) llaman
    antes a `perfil.marcar_revisado`.
*   **Pruebas nuevas:**
    *   `CarrerasTests`: carga y validación; un `id` con `..` falla.
    *   `PerfilV1Tests`:
        *   sin `publications`, el perfil es válido;
        *   un campo sensible no cambia con `por='ia'` y sale tapado en `leer(para_ia=True)`;
        *   se asignan los `id` de `education` sin cambiar los existentes;
        *   guardar con `por='ia'` invalida el sello, y `cv_generar` falla con «revisa tu perfil en el panel»;
        *   `marcar_revisado` deja el sello y la copia en `respaldos/`;
        *   un cambio de ella renueva el sello solo si estaba vigente;
        *   la migración sella el perfil del autor una sola vez.
    *   `CvPaginasTests`: un CV de dos páginas con tope 1 falla; el mismo CV con tope 3 pasa; aparece la sección
        de carrera; un valor con `<img src=file:...>` sale escapado.
    *   `DocumentosTests`:
        *   el barrido copia y no mueve, e ignora un archivo recién modificado;
        *   el mismo hash no se duplica;
        *   `listar_para_ia` no trae ni rutas ni nombres originales;
        *   `leer` sin permiso falla;
        *   la cédula queda tapada;
        *   sin `pdfminer`, el texto contiene «no puedo leer PDF en este equipo» (se simula el import).

### Plan de verificación

*   **Pruebas unitarias:** `python -m unittest discover -s tests -v`, al terminar cada bloque. Hoy hay 85 pruebas.
    Todas tienen que seguir pasando, salvo las que este plan reescribe a propósito, que están listadas en los ítems
    11, 26 y 45.
*   **Contención:** `python -m tests.contencion`, al terminar A2 y C. Pasa con las cuatro condiciones de «Pruebas del
    piloto».
*   **Panel de punta a punta:** `python -m tests.e2e_panel`, al terminar A1, A2 y C.
*   **Sesión real:** `docs/piloto/pruebas_en_sesion.md` en la app de escritorio, al terminar A1, A2 y C.
*   **Piloto:** las medidas de éxito de las metas, durante 4 semanas desde la instalación.

--------------------------------------------------------------------------------

*Drafted with EGM*
