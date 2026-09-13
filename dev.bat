@echo off
chcp 65001 > nul
echo =======================================================
echo          Lancement de BennyBets (Mode Dev)
echo =======================================================
echo.

:: Verification de uv
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] L'outil 'uv' n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer uv via https://astral.sh/uv
    pause
    exit /b 1
)

:: Synchronisation des dependances
echo [1/2] Synchronisation des dependances avec uv...
call uv sync
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] Echec de synchronisation des dependances.
    pause
    exit /b 1
)

:: Lancement de l'application
echo [2/2] Lancement de l'application BennyBets...
echo.
call uv run python -m bennybets
pause
