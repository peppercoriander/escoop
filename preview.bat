@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 goto failed

set "PREVIEW_PYTHON="
call :try_python "%SystemDrive%\msys64\mingw64\bin\python.exe"
for /f "delims=" %%P in ('where python.exe 2^>nul') do call :try_python "%%P"
if not defined PREVIEW_PYTHON (
    echo A working Python 3.10 or newer was not found.
    echo The Windows Store python.exe shortcut is not a Python installation.
    goto failed
)
echo Using Python: "%PREVIEW_PYTHON%"
set "PREVIEW_NODE="
for /f "delims=" %%N in ('where node.exe 2^>nul') do if not defined PREVIEW_NODE set "PREVIEW_NODE=%%N"
if not defined PREVIEW_NODE if exist "%ProgramFiles%\nodejs\node.exe" set "PREVIEW_NODE=%ProgramFiles%\nodejs\node.exe"
if not defined PREVIEW_NODE if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" set "PREVIEW_NODE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if not defined PREVIEW_NODE (
    echo Node.js was not found in PATH or the local Codex runtime.
    echo Please install Node.js and try again.
    goto failed
)
"%PREVIEW_NODE%" --version
if errorlevel 1 goto failed
if not exist "node_modules\vite\bin\vite.js" (
    echo Project dependencies are missing. Run npm ci in this folder first.
    goto failed
)

echo Updating website data from maintenance.xlsx and song_placements.csv...
"%PREVIEW_PYTHON%" -u scripts/prepare_data.py
set "PREVIEW_EXIT=%ERRORLEVEL%"
if not "%PREVIEW_EXIT%"=="0" (
    echo Data generation failed with exit code %PREVIEW_EXIT%.
    goto failed
)

echo.
echo Starting local preview: http://127.0.0.1:4175
echo Your browser will open automatically. Keep this window open.
echo To stop, press Q then Enter, or close this window.
echo After saving maintenance.xlsx or song_placements.csv, run preview.bat again.
echo.
"%PREVIEW_NODE%" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 4175 --strictPort --open
if errorlevel 1 (
    echo The web server could not start.
    echo If port 4175 is busy, close the previous preview window and try again.
    goto failed
)
exit /b 0

:try_python
if defined PREVIEW_PYTHON exit /b 0
if not exist "%~1" exit /b 0
echo "%~1" | findstr /i /l /c:"\Microsoft\WindowsApps\" >nul
if not errorlevel 1 exit /b 0
"%~1" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if not errorlevel 1 set "PREVIEW_PYTHON=%~1"
exit /b 0

:failed
echo.
echo Preview could not start. Please check the error above.
pause
exit /b 1
