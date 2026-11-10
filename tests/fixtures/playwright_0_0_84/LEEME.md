# Respuestas reales de @playwright/mcp@0.0.84

Capturadas con `python -m tests.capturar_a0` (navegador aislado y sin ventana, contra `tests/portal_falso.py`).

| Comprobación | Resultado |
|---|---|
| La imagen de `browser_take_screenshot` llega como contenido `image` en base64 | sí, 22987 bytes de PNG |
| `browser_take_screenshot` acepta `fullPage` | sí |
| Petición con un `Host` ajeno | rechazada (403) |
| Petición con un `Origin` ajeno | ACEPTADA (200): anotar en la tabla de riesgos |
| Petición sin cabeceras extra | 200 |
| El navegador dedicado se lanza sin `--remote-allow-origins=*` | sí |
