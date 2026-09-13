@echo off
chcp 65001 > nul
echo =======================================================
echo         Compilation de BennyBets (.exe autonome)
echo =======================================================
echo.

:: Verification de uv
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] L'outil 'uv' n'est pas installe.
    pause
    exit /b 1
)

echo [1/3] Synchronisation de l'environnement...
call uv sync
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] Echec uv sync.
    pause
    exit /b 1
)

echo [2/3] Creation du dossier dist...
if not exist "dist" mkdir "dist"

echo [3/3] Compilation avec PyInstaller via uv...
call uv run pyinstaller --noconfirm --onefile --windowed --name "BennyBets" --clean main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERREUR] La compilation a echoue.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo  SUCCES : Executable autonome genere dans dist\BennyBets.exe
echo =======================================================
dir dist\BennyBets.exe
pause
