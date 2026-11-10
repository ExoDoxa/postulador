# Magneto

- Para buscar, haz clic real en el primer `input[type=text]` visible, escribe y pulsa Enter. La URL queda `/co/trabajos/buscar/<cargo>`; los parámetros `?q=` no filtran.
- «Aplicar» solo responde a `button.click()` desde JS, no al clic por coordenadas.
- Algunas vacantes abren un cuestionario tipo chat: cada respuesta se confirma con `[class*=open_short_button]` y las de opción múltiple con «Guardar». «Enviar respuestas» se activa al final.
- Lee el bloque completo de requisitos antes de aplicar.
