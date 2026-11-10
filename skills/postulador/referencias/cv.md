# Generar un CV

Haz un CV por tipo de cargo y en el idioma de la oferta. Antes de crear uno, revisa `cv_listar`: si uno sirve, úsalo; si se parece, parte de `cv_leer_seleccion`.

## Selección

```json
{
  "summary": "texto idéntico a un valor de cv_summaries",
  "experiences": ["id"],
  "publications": ["id"],
  "projects": ["id"],
  "skills": ["texto idéntico a un valor de skills"],
  "bullets": {"id_experiencia": [0, 2]},
  "tools": ["etiqueta de cv_tool_labels"]
}
```

- Adaptar es **elegir** entre bloques del perfil, no redactar hechos nuevos. Para un resumen o viñeta nuevos, confirma con el usuario y guárdalos en el perfil.
- El orden de cada lista es de prioridad; el CV imprime en el orden del perfil.
- Las plantillas DOCX son más estrictas: 2–5 experiencias, 1–3 publicaciones, 1–3 proyectos, 3–5 habilidades, 1–3 viñetas por experiencia y hasta 6 herramientas.

## Generar y revisar

Llama a `cv_generar` con un nombre como `asesora_juridica`. El perfil tiene que estar revisado: si la herramienta pide revisarlo, dile al usuario que abra el panel, pestaña Perfil, y pulse «Revisado». El motor `auto` usa HTML; solo en el equipo del autor, sin carrera en el perfil, puede usar su plantilla DOCX. El tope de páginas es 1, salvo que el paquete de carrera del perfil fije otro (en derecho, 2 por ahora). Si no cabe, la herramienta lo rechaza: quita contenido, no reduzcas el diseño.

Si el perfil tiene `carrera`, el CV suma una sección con sus datos profesionales (por ejemplo, la tarjeta profesional). Los campos sensibles nunca salen en el CV.

Mira siempre la vista previa antes de usar el CV. Lee `revision_ats`: es lo que extrae un lector de PDF. Si indica columnas mezcladas, contacto ilegible o cifras sin respaldo, corrígelo o avísalo.

## Diseños y comentarios

Hay tres diseños HTML: `columna` (por defecto y la más legible para un ATS), `clasico` y `editorial`. Con `ajustes` o `cv_ajustar` cambias `fuente`, `tamano`, `color` y `foto`, sin tocar el contenido.

El usuario ve sus CV en el panel y deja comentarios. Revisa `cv_comentarios` cuando lo pida y al iniciar trabajo sobre un CV:

1. Si pide aspecto, usa `cv_ajustar`.
2. Si pide contenido, cambia la selección y genera de nuevo con `cv_generar`. Si necesita un hecho que no está en el perfil, pregúntaselo; no lo inventes.
3. Marca `cv_comentario_resuelto` con una nota breve de qué hiciste. Si no pudiste, déjalo pendiente y explícalo.

## Plantillas propias

En el equipo del usuario no existe `plantilla_guardar`: usa los tres diseños. Solo en el equipo del autor puedes crear un HTML A4 que imite un CV subido, con las marcas `{{idioma}} {{nombre}} {{titular}} {{resumen}} {{carrera}} {{contacto}} {{habilidades}} {{idiomas}} {{experiencia}} {{formacion}} {{publicaciones}} {{proyectos}}` (más `{{estilo}}`, `{{foto}}` y `{{clase_foto}}` para el editor del panel), partiendo de `postulador/plantillas/columna.html`.
