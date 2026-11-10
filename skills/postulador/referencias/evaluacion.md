# Evaluar una oferta

Hazlo antes de aplicar, con la oferta completa.

1. Lee la oferta completa. Pásala a `ats_evaluar` entera y sin resumir: acortarla cambia los números.
2. Prepara la selección del CV adaptado (`referencias/cv.md`), en el idioma de la oferta.
3. Lista los requisitos reales. Para cada uno: `texto` (cita literal de la oferta), `excluyente` (si es obligatorio), `estado` y `evidencia` (cita literal del perfil o las notas).
4. Estados: `cumple`, `parcial`, `por_confirmar` (el perfil no lo dice) y `brecha` (no lo cumple). Nunca uses `cumple` sin evidencia; la herramienta lo rechaza.
5. Llama a `ats_evaluar`. Si rechaza una cita, cópiala literal de la oferta o del perfil; no cambies el estado para que pase.
6. Reporta el campo `resumen` copiado tal cual: no recalcules, redondees ni renombres sus cifras.

## Cómo leer el resultado

- `idoneidad`: 70 % requisitos y 30 % ATS del CV adaptado. Si falla un excluyente, queda en 39 % o menos.
- `ats_base`: siempre el CV genérico sin adaptar, nunca un CV temático. `ats_adaptado`: la selección que evaluaste. `mejora`: la diferencia.
- `ats_techo`: lo máximo posible solo con hechos del perfil.
- `disponibles_en_perfil`: términos que tienes pero no pusiste. Mejora la selección y evalúa otra vez.
- `brechas_reales`: términos que el perfil no respalda. Nunca los añadas; si el usuario tiene esa experiencia, pregúntale y guárdala en el perfil.
- `decision`: `aplicar`, `revisar`, `preguntar` o `no_aplicar`. Es una recomendación: el usuario puede decidir otra cosa.

Presenta los números como estimación propia, no como el puntaje de un ATS real ni como probabilidad de contratación. No selecciones contenido irrelevante solo para subir el número.
