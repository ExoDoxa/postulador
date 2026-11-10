# Acceso directo a la IA (meta 9, pregunta 4)

**Estado:** sin investigar. Mientras no haya resultado, rige el plan B.

## Pregunta

¿La app de escritorio de Claude acepta que se abra una sesión de Code ya en una carpeta, por línea de comandos o por
un enlace?

## Plan B (implementado)

`python -m postulador arranque` deja en la carpeta de arranque un `LEEME.html` con la ruta exacta que hay que
elegir al crear la sesión, y en el Escritorio el acceso directo «Cómo abrir Postulador con Claude», que lo abre. Si
existe `docs/piloto/elegir_carpeta.png` (una imagen que toma el autor de la pantalla de la app donde se elige la
carpeta), se copia y se muestra en el `LEEME.html`.

## Qué probar

1. Opciones de la línea de comandos de la app de escritorio (`Claude.exe --help` o su documentación).
2. Enlaces propios de la app (`claude://…`) que abran una sesión en una carpeta.
3. Si alguno sirve: que `arranque` cree «Postulador con Claude.lnk» con ese comando, y anotar aquí la versión de la
   app con que se probó.
