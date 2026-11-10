@echo off
rem Instala o actualiza Postulador en este equipo. Doble clic: no hay que escribir nada.
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo.
echo  === Postulador: instalación ===
echo.

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo  Falta Python 3.10 o más nuevo. Instálalo desde https://www.python.org/downloads/
  echo  y marca la casilla «Add python.exe to PATH». Después vuelve a abrir este archivo.
  goto :fin
)
where npx >nul 2>nul
if errorlevel 1 (
  echo  Falta Node.js. Instálalo desde https://nodejs.org/ ^(versión LTS^) y vuelve a abrir este archivo.
  goto :fin
)

echo  1. Componentes de Python...
%PY% -m pip install --user --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo     No se pudieron instalar. Revisa la conexión a internet y vuelve a intentarlo.
  goto :fin
)

echo  2. Carpeta de arranque, permisos y accesos directos...
%PY% -m postulador arranque
if errorlevel 1 goto :fin

echo.
echo  3. Revisión:
%PY% -m postulador doctor

echo.
echo  Listo. En el Escritorio quedaron dos accesos directos:
echo    - «Panel de Postulador»: tu tablero, sin abrir Claude.
echo    - «Cómo abrir Postulador con Claude»: qué carpeta elegir al crear la sesión.
echo.
echo  Falta, una sola vez:
echo    - en claude.ai, Configuración, Conectores: desactivar todos los conectores;
echo    - abrir el navegador del asistente e iniciar sesión en tus portales de empleo:
echo      %PY% -m postulador abrir
:fin
echo.
rem Con /sinpausa (cuando lo ejecuta el asistente) termina sin esperar una tecla.
if /i not "%~1"=="/sinpausa" pause
