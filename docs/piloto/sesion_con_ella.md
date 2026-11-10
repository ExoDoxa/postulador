# Sesión del autor con ella (bloque B)

Una conversación antes de dar el piloto por cerrado. Lo que salga va como decisiones nuevas en
[concepts_brief.md](../../concepts_brief.md) y ajusta los valores provisionales del código.

## Qué averiguar

| Pregunta | Dónde se ajusta |
|---|---|
| ¿Dónde busca hoy y en qué sitios postula? | Pregunta 1 del diseño; si hace falta, guías en `skills/postulador/sitios/` |
| ¿Esos sitios tienen formularios que valga la pena rellenar? Si no, se reconsidera A5 (sin navegador) | Diseño, bloque A2 |
| ¿Qué botones intermedios tienen («Siguiente», «Continuar»)? | `PASO_SEGURO_POR_SITIO` en `postulador/puerta.py` |
| ¿Cuántas páginas tiene su CV y cuántas acepta el mercado legal? | `paginas_maximas` en `postulador/paquetes/derecho.json` (hoy 2) |
| ¿Qué datos de abogada le piden los formularios? | `campos` en `derecho.json` |
| ¿Qué documentos le piden? | `tipos_documento` en `derecho.json` |
| ¿Qué palabras del panel no entiende? | `postulador/web/app.js` |
| ¿Cómo le resultó la entrevista? | `skills/postulador/carreras/derecho.md` |

## Al terminar

- [ ] Quitar `"provisional"` de `derecho.json` cuando sus valores estén confirmados.
- [ ] Anotar las respuestas en `concepts_brief.md` y marcar resueltas las preguntas 1 y 2 del diseño.
