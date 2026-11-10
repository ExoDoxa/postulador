# Instalación del piloto

Lista de verificación del autor para el equipo de la persona. Diseño: [piloto_abogada.md](../designs/piloto_abogada.md).

## Antes de la visita

- [ ] Ella tiene cuenta de Claude con un plan que incluya Claude Code, y la app de escritorio de Claude instalada.
- [ ] El código está en GitHub y el autor sabe la dirección para clonarlo.

## En su equipo

1. [ ] Instalar **Python 3.10 o más nuevo** desde python.org, con la casilla «Add python.exe to PATH».
2. [ ] Instalar **Node.js LTS** desde nodejs.org.
3. [ ] Instalar **Git** desde git-scm.com (para actualizar después).
4. [ ] Clonar el repositorio **fuera de OneDrive**, por ejemplo en `%LOCALAPPDATA%\Postulador\codigo`:
   `git clone https://github.com/ExoDoxa/postulador.git "%LOCALAPPDATA%\Postulador\codigo"`
5. [ ] Doble clic en `instalar.cmd` dentro de esa carpeta. Hace tres cosas:
   - `pip install -r requirements.txt` (lee PDF, por ejemplo su CV);
   - `python -m postulador arranque`: crea `C:\Users\<ella>\Postulador` con los permisos, escribe
     `%LOCALAPPDATA%\Postulador\equipo.json` con el tope `solo_rellenar` y deja en el Escritorio los accesos
     «Panel de Postulador» y «Cómo abrir Postulador con Claude»;
   - `python -m postulador doctor`: el diagnóstico tiene que salir con `"problemas": []`.
6. [ ] En **claude.ai → Configuración → Conectores**, en la cuenta de ella: desactivar todos (Gmail, Drive,
   Calendar, TinyFish, Figma…). Ninguno debe quedar activo.
7. [ ] Abrir el navegador del asistente con `python -m postulador abrir` e **iniciar sesión con ella** en sus
   portales (Computrabajo, elempleo, LinkedIn…). Las sesiones quedan en ese perfil (`%LOCALAPPDATA%\PostuladorNavegador`),
   aparte de su navegador normal.
8. [ ] En la app de Claude, pestaña **Code**, crear una sesión nueva eligiendo `C:\Users\<ella>\Postulador`. Escribir
   «hola» y comprobar que la IA llama a `diagnostico` sin problemas.
9. [ ] Abrir el acceso directo «Panel de Postulador»: se abre su tablero en su navegador normal, sin Claude.
10. [ ] Hacer con ella la prueba en sesión real ([pruebas_en_sesion.md](pruebas_en_sesion.md)).

## Para actualizar

1. `git pull` en la carpeta del código.
2. Doble clic en `instalar.cmd` (vuelve a generar los permisos sin tocar `entrada/` ni sus datos).
3. Cerrar la app de Claude y el navegador del asistente, y volver a abrirlos: así los servidores arrancan con el
   código nuevo.

## Equipo del autor

El autor usa el mismo código con más autonomía: una sola vez, `python -m postulador arranque --nivel-maximo aprobar`.
Sin eso, su equipo queda en `solo_rellenar`, porque `equipo.json` falla cerrado.

## Límites conocidos

- El acceso directo a la IA (meta 9) todavía es el plan B: el `LEEME.html` explica qué carpeta elegir. Ver
  [acceso_directo_ia.md](acceso_directo_ia.md).
- Los valores del paquete de derecho (`postulador/paquetes/derecho.json`) son provisionales hasta la sesión con
  ella ([sesion_con_ella.md](sesion_con_ella.md)).
