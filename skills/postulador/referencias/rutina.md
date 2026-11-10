# Rutina de postulaciones

Recorre los pasos en orden. Si el usuario pide solo una parte, haz esa parte.

## 0. Preparar

Llama a `contexto_usuario`. Si el navegador no responde, usa `navegador_abrir`. Si un sitio pide iniciar sesión, pídele que entre; nunca le pidas la contraseña en el chat.

## 1. Respuestas de las empresas

En el equipo del usuario (tope `solo_rellenar`) no lees su correo: él marca las respuestas («Avanzó», «Rechazada») en el panel. Pregúntale si recibió novedades y, si te cuenta un avance, ayúdalo a prepararse.

Solo en el equipo del autor, con el tope en `aprobar` o más: si tiene sesión en su correo, lee lo de los últimos dos días, marca `rechazada` o `avanzo` según lo que digan y usa las alertas de empleo como fuente de ofertas. Solo lectura.

## 2. Buscar

Lee `busqueda_preferencias` y aplícalas en todo: antigüedad máxima (`antiguedad_horas`), modalidades, ubicaciones, cargos, palabras a `excluir`, salario mínimo e idiomas. Busca con cada cargo de `cargos` (o con los resúmenes del perfil si está vacío) en `ofertas_tableros` y en los sitios preferidos de sus notas; en LinkedIn usa `linkedin_url` y sigue `sitios/linkedin.md`. Descarta lo que contradiga las preferencias sin preguntar. Si el usuario quiere cambiarlas, indícale Ajustes del panel. No des por abierta una oferta sin comprobarlo en la fuente.

## 3. Elegir

Antes de aplicar, descarta duplicados con `postulaciones_listar` e `historial_buscar`.

Comprueba que la oferta siga abierta en la fuente original y evalúala con `referencias/evaluacion.md`. Descarta si la decisión es `no_aplicar` o si parece fraude, y registra `descartada` con el motivo. Con `revisar` o `preguntar`, muestra una lista corta antes de aplicar.

## 4. Aplicar

1. Consulta `politica_consultar`. Si `contexto_usuario` trae `espera_envio`, no empieces otra: recuérdale al usuario que resuelva la que espera en el panel.
2. Elige o genera el CV (`referencias/cv.md`) y revisa su `revision_ats`.
3. Si piden carta, redáctala solo con hechos del perfil, en el idioma de la oferta, y genera con `carta_generar`. Corrige lo que aparezca en `cifras_sin_respaldo`.
4. Rellena con el perfil, y busca antes en `respuestas_buscar` e `historial_buscar` para ser coherente con lo ya respondido.
5. Si falta un dato, pregunta. Si corres sin chat, registra `incompleta` con la pregunta en `nota` y sigue con la siguiente oferta.
6. Actúa según el nivel. En `solo_rellenar`: registra la postulación como `preparada`, rellena, sube el CV con `cv:<nombre>`, llama a `formulario_listo` y dile «revisa la ventana del navegador y pulsa Enviar tú». Espera a que la resuelva en el panel. Si en el turno siguiente ves la confirmación del portal, pásala a `reportada`.
   Solo si existen las herramientas de aprobación (equipo del autor): antes de solicitar una aprobación, revisa con `aprobaciones_listar` si hay alguna `aprobada` para terminar ese envío, y verifica el mensaje de éxito.

Para cuentas nuevas, anota el sitio en las notas, nunca la contraseña.

## 5. Registrar

Registra cada oferta con `postulacion_registrar`: cargo, empresa, sitio, estado (`preparada` antes de rellenar, `descartada` con motivo si no aplicas), enlace, CV usado, puntajes de `ats_evaluar` si existe y una nota con las respuestas relevantes.

## 6. Cerrar

Revisa `seguimientos_pendientes` y sigue `referencias/resultados.md`. En el informe final incluye, por oferta, lo que dejaste listo para que envíe y por qué descartaste las demás.
