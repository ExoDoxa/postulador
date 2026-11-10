# LinkedIn

Riesgo: LinkedIn prohíbe el software que automatiza actividad y puede restringir o cerrar la cuenta. Muestra la advertencia de `politica_consultar`.

- Busca con `linkedin_url(palabras, ubicacion, pagina)`: devuelve la vista pública de resultados con la antigüedad y la modalidad del usuario ya aplicadas. Ábrela con `browser_navigate`. Cada oferta es un link cuyo `/url` termina en `-<número>`: ese número da su enlace estable `https://www.linkedin.com/jobs/view/<número>/`. Trae empresa, lugar y «Hace N horas». Diez por página; sigue con `pagina+1` hasta que llegue vacía o tengas suficientes. LinkedIn no siempre respeta el filtro de modalidad (el 10 nov devolvió presenciales con «solo remoto»): confirma la modalidad y la antigüedad en la oferta antes de proponerla.
- El buscador normal (`/jobs/search/`) redirige a `/jobs/search-results/`, pierde la ubicación escrita y el filtro de remoto, y no muestra el número de cada oferta: no lo uses para buscar.
- Para leer una oferta o aplicar, abre `https://www.linkedin.com/jobs/view/<número>/` con la sesión del usuario. Prioriza Solicitud sencilla.
- El modal de Solicitud sencilla es `[role=dialog]`.
- Si la descripción no carga, léela en `linkedin.com/jobs-guest/jobs/api/jobPosting/<id>`, sin abusar: responde 429 si se pide demasiado.
- Actúa a ritmo normal: si aparece una verificación o aviso de límite, detente e informa.
