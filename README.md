# Radicado

**Tu búsqueda de empleo, con sello y comprobante.** Un asistente de IA que busca empleo contigo: adapta tu CV a cada oferta, rellena formularios en un navegador aparte y lleva el expediente. El envío lo haces tú, y cada formulario deja un comprobante escrito por el código.

Por dentro el paquete se llama `postulador` (los comandos son `python -m postulador …`).

Corre en tu PC con tu propia suscripción de Claude. No necesitas clave de API y tus datos no salen de tu equipo, salvo lo que el motor de IA procesa para trabajar y lo que envíes a cada portal.

## Instalar (Windows)

Necesitas Python 3.10 o más nuevo (con «Add python.exe to PATH»), Node.js LTS, Git y la app de escritorio de Claude.

1. Clona el repositorio **fuera de OneDrive**, por ejemplo:
   `git clone https://github.com/ExoDoxa/radicado.git "%LOCALAPPDATA%\Postulador\codigo"`
2. Doble clic en **`instalar.cmd`**. Instala lo que falta, crea tu carpeta de arranque (`C:\Users\<tú>\Radicado`) y deja dos accesos directos en el Escritorio: **Panel de Radicado** y **Cómo abrir Radicado con Claude**.
3. En **claude.ai → Configuración → Conectores**, desactiva todos los conectores.
4. Abre el navegador del asistente (`python -m postulador abrir`) e inicia sesión en tus portales de empleo. Es una ventana aparte de tu navegador normal.
5. En la app de Claude, pestaña **Code**, crea una sesión nueva **eligiendo la carpeta de arranque**. Escribe «hola».

Para actualizar: `git pull` y otra vez `instalar.cmd`. Después cierra y vuelve a abrir la app de Claude.

La lista completa para quien instala está en [docs/piloto/instalacion.md](docs/piloto/instalacion.md).

## Cómo se usa

- **En el chat** le pides cosas: «hagamos mi perfil», «hazme un CV para asesora jurídica», «busca ofertas y rellena las que encajen».
- **En el panel** (acceso directo «Panel de Radicado», funciona sin abrir Claude):
  - **Lista para enviar:** lo que el asistente rellenó. Revisas la ventana del navegador, pulsas Enviar tú y aquí marcas «La envié», «No, ya no», «Que el asistente la corrija» o «Ya estaba enviada cuando la vi». Mientras alguna espere, el asistente no puede seguir.
  - **Lo que rellenó el asistente:** cada postulación tiene un comprobante escrito por el código: campos, casillas, CV subido, horas e imagen de la página.
  - **Perfil:** tus datos de carrera (por ejemplo, tarjeta profesional) y el botón **Revisado**. Sin revisar, no se generan CV ni cartas; si el asistente cambia algo, te muestra qué y tienes que revisar otra vez.
  - **Documentos:** lo que dejas en la carpeta `entrada` aparece aquí. Eliges qué es cada archivo y si el asistente puede leerlo. «Mi CV» siempre se puede leer.
  - **Mis CV, Postulaciones, Seguimientos, Resultados, En vivo, Informes y Ajustes.**

## Qué no puede hacer el asistente

Lo impide el código, no solo las instrucciones:

- **Enviar.** En el equipo de otra persona el tope es `solo_rellenar` (`%LOCALAPPDATA%\Postulador\equipo.json`, que solo escribe `instalar.cmd`). Si el archivo falta o está dañado, el tope igual es `solo_rellenar`.
- **Pulsar botones mientras rellena.** La puerta (`postulador/puerta.py`, entre la IA y el navegador) bloquea todo botón, Enter y diálogo aceptado. Solo pasan el campo de adjuntar archivo y los pasos que se marquen como seguros por sitio. Un «Siguiente» lo pulsas tú.
- **Seguir con otra oferta** mientras una espera tu envío (candado guardado en la base: vale aunque se reinicie todo).
- **Marcar «enviada», respuestas o seguimientos.** Si ve la confirmación del portal la marca «Enviada según el asistente»; la confirmas tú.
- **Leer tus archivos.** En la carpeta de arranque no tiene comandos, ni lectura o edición de archivos, ni otros navegadores. Tus documentos los lee solo si lo permites, y los números de cédula le llegan tapados.
- **Subir algo que no sea tu CV**, pagar, marcar declaraciones juradas, abrir el panel o direcciones del propio equipo, ni ejecutar código en la página.

**Es una barrera fuerte, no absoluta.** Un elemento que no es botón y envía con JavaScript podría pasar: por eso existe «Ya estaba enviada cuando la vi», que cuenta como incidente. Los riesgos están en [docs/designs/piloto_abogada.md](docs/designs/piloto_abogada.md).

## Carreras

Cada carrera tiene un paquete en `postulador/paquetes/`: sus campos, el tope de páginas del CV y los tipos de documento. Hoy hay uno, `derecho.json`, con valores provisionales (CV de hasta 2 páginas).

## Para el autor

En tu propio equipo puedes subir el tope una vez:

```powershell
python -m postulador arranque --nivel-maximo aprobar   # o enviar_solo
```

Con el tope en `aprobar` o más vuelven la cola de aprobaciones, `plantilla_guardar`, los seguimientos desde el chat y la lectura del correo de la rutina. Comandos:

```powershell
python -m postulador doctor               # estado y diagnóstico
python -m postulador panel --abrir        # panel en el navegador
python -m postulador abrir                # navegador del asistente y su servicio de control
python -m postulador datos                # dónde están los datos; --mover CARPETA los copia (por ejemplo, a una USB)
python -m postulador reporte              # embudo, tasas por sitio y CV, rechazos y seguimientos
python -m postulador importar-historial   # importa un REGISTRO_POSTULACIONES.md
python -m postulador ejecutar "Revisa novedades"   # sin chat; programar "…" --hora 08:00 lo repite cada día
```

| Nivel | Qué hace |
|---|---|
| `enviar_solo` | Envía lo que cumpla las reglas |
| `aprobar` | Deja el formulario listo y espera tu visto bueno en el panel (vale una vez, 24 horas) |
| `solo_rellenar` | Rellena, guarda el comprobante y envías tú |
| `solo_preparar` | No toca el sitio: te entrega CV y respuestas |

## Cómo funciona

```
App de Claude (Code), sesión en C:\Users\<persona>\Radicado   denegado: comandos, leer/editar archivos, otros navegadores
   ├─ skill postulador          reglas y procesos: skills/postulador/
   ├─ MCP postulador            perfil, CV, documentos, registro, diagnostico: postulador/
   └─ puerta (MCP playwright)   postulador/puerta.py → Playwright MCP :8931 → navegador del asistente :9222
Panel :8770 en tu navegador normal                                 postulador/panel.py + postulador/web/
Datos (según %LOCALAPPDATA%\Postulador\ubicacion.json): postulador.db, perfil, CV, documentos/, comprobantes/
```

- **CV:** HTML impreso con Chrome o Edge (o tu plantilla DOCX, solo en el equipo del autor). Nunca pasa del tope de páginas.
- **Cartas:** solo con hechos de tu perfil; señala cifras sin respaldo.
- **Búsqueda:** preferencias en Ajustes; LinkedIn por el navegador y tableros públicos en `tableros.json` (formato en `ejemplos/tableros.json`).

## Riesgos

- **LinkedIn** prohíbe el software que automatiza actividad y puede restringir o cerrar tu cuenta. Otros portales pueden tener reglas parecidas.
- **Suscripciones:** tienen límites de uso, y sus términos pueden cambiar.
- **Revisa lo que se envía en tu nombre.** El asistente solo debe usar datos de tu perfil, pero puede equivocarse: para eso está el comprobante.

## Pruebas

```powershell
python -m unittest discover -s tests -v   # unitarias
python -m tests.e2e_panel                 # panel en un navegador (pip install playwright)
python -m tests.contencion                # ataques a la puerta contra un portal falso y un navegador real (Node)
python -m tests.capturar_a0               # respuestas reales de Playwright MCP
```
