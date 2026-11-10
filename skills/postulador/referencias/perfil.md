# Crear el perfil

Si `contexto_usuario` indica que no hay perfil, o `perfil_faltantes` trae faltantes:

1. **Parte de su CV.** Llama a `documentos_listar`. Si hay uno de tipo «Mi CV», léelo con `documento_leer` y extrae los datos. Si no hay ninguno, pídele que deje su CV en la carpeta `entrada` y que en el panel, pestaña Documentos, lo marque como «Mi CV». Tú no abres archivos.
2. **Pregunta solo lo que falta.** Llama a `perfil_faltantes`: devuelve lo que falta de la base y de su carrera. Si el perfil tiene `carrera`, sigue también la guía `carreras/<carrera>.md`. Si no tiene CV, entrevístalo por partes: contacto, estudios, trabajos (incluidos voluntariados y prácticas), habilidades, idiomas y qué busca.
3. **Copia los títulos tal cual.** «Abogada» no se cambia por «egresada», ni «Especialista en Derecho Laboral» por «Especialización laboral». Las fechas y las instituciones, igual que en sus documentos.
4. **Redacta, no inventes.** Viñetas breves y varios resúmenes, uno por tipo de cargo. Mejora la redacción, nunca los hechos: nada de cifras ni logros que no haya dicho.
5. **Campos sensibles.** Cédula, fecha de nacimiento y los que su paquete de carrera marque como sensibles no los escribes tú: pídele que los ponga en el panel, pestaña Perfil. Te llegan tapados.
6. **Muéstrale todo y guarda** con `perfil_guardar`. Datos para formularios que no van en el CV (disponibilidad, pretensión salarial) van con `notas_agregar` o en los datos de su carrera.
7. **Pídele que lo revise.** Dile: «abre el panel, pestaña Perfil, revisa los datos y pulsa Revisado». Sin eso no se generan CV ni cartas. Cada vez que cambies el perfil, tendrá que revisarlo otra vez.
8. Pregunta sus sitios preferidos. Las preferencias de búsqueda las cambia él en Ajustes del panel.

## Formato

Ejemplo completo: `ejemplos/perfil.json` en el repositorio.

- `name`, `headline`, `contact` (lista), `skills` (lista), `languages` (lista), `cv_tool_labels` (lista opcional).
- `education`: `title`, `organization`, `date`. El `id` (`f1`, `f2`…) lo pone el código.
- `experience`: `id`, `title`, `organization`, `date`, `bullets` (todas las viñetas), `cv_bullets` (índices por defecto).
- `publications` y `projects`: opcionales. `publications`: `id`, `cv_title`, `cv_citation`. `projects`: `id`, `cv_title`, `cv_description`.
- `cv_summaries`: objeto `{tipo_de_cargo: resumen}`.
- `carrera`: el paquete de su profesión, por ejemplo `derecho`. Lo puede elegir él en el panel.
- `campos_carrera`: objeto `{clave: valor}` con los campos del paquete, solo texto. No toques los sensibles: deja el valor tapado tal como te llegó.
- `revisado_el`, `revisado_huella` y `schema_version` los maneja el código: no los cambies.

Para CV en otro idioma, usa `perfil_guardar` con `idioma`, conservando los mismos ids y el mismo orden de viñetas.
