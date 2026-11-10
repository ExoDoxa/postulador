# Prueba en sesión real

Se hace en la app de escritorio de Claude, pestaña Code, con una sesión creada en la carpeta de arranque. Lo que se
puede probar sin IA ya está automatizado:

| Prueba | Cómo | Último resultado |
|---|---|---|
| Unitarias | `python -m unittest discover -s tests -v` | 117 pruebas, todas pasan (2026-11-10) |
| Panel de punta a punta | `python -m tests.e2e_panel` | 0 fallos (2026-11-10) |
| Contención contra un navegador real | `python -m tests.contencion` | 0 fallos, 0 envíos al portal (2026-11-10) |
| Respuestas reales de Playwright | `python -m tests.capturar_a0` | ver `tests/fixtures/playwright_0_0_84/LEEME.md` |

## Encierro y arranque (bloque A1)

- [ ] La IA llama a `diagnostico` al empezar y sale sin `problemas`.
- [ ] `Read`, `Glob`, `Grep`, `Bash` y `plantilla_guardar` no están en su lista de herramientas.
- [ ] Con un conector de claude.ai activado a propósito, la IA se niega a buscar y explica qué hacer. Después se
      vuelve a desactivar.
- [ ] Una sesión abierta en otra carpeta no tiene las herramientas de Postulador.
- [ ] El acceso directo «Panel de Radicado» abre el panel sin Claude.

## Formularios (bloque A2)

- [ ] La IA registra una postulación `preparada`, rellena un formulario real, sube el CV con `cv:<nombre>` y llama
      a `formulario_listo`.
- [ ] Un intento de pulsar «Enviar» queda bloqueado; un «Siguiente» se lo pide a ella.
- [ ] El panel muestra la postulación en «Lista para enviar» y su comprobante coincide con la página.
- [ ] Mientras espera, la IA no puede escribir; en una sesión nueva tampoco.
- [ ] Ella envía, la IA ve la confirmación y la pasa a `reportada`; ella pulsa «La envié».

## Perfil y documentos (bloque C)

- [ ] Ella deja su CV en `entrada/`, lo marca como «Mi CV» en el panel y la IA lo lee con `documento_leer`.
- [ ] Un diploma sin «El asistente puede leerlo» no se puede leer.
- [ ] La entrevista avanza con `perfil_faltantes` y copia los títulos tal cual.
- [ ] Tras un cambio de la IA, `cv_generar` se niega hasta que ella pulse «Revisado».
- [ ] El CV de ella ocupa las páginas que le hacen falta sin pasar del tope del paquete.
