@echo off
cd /d "%~dp0"
echo.
echo ============================================================
echo   Tangerino Auto v3.0  ^|  Build Portavel
echo ============================================================
echo.

echo [1/3] Instalando PyInstaller...
python -m pip install pyinstaller --quiet --upgrade
if errorlevel 1 ( echo ERRO: pip falhou. && pause && exit /b 1 )

echo [2/3] Compilando executavel...
pyinstaller --noconfirm --clean ^
  --name TangerinoV3PRO ^
  --onedir ^
  --windowed ^
  --icon "tangerino.ico" ^
  --add-data "tangerino.ico;." ^
  --add-data "tangerino.png;." ^
  --collect-all customtkinter ^
  --collect-all tkcalendar ^
  --collect-all playwright ^
  --collect-all pdfplumber ^
  --collect-all docx ^
  --hidden-import requests ^
  --hidden-import websocket ^
  --hidden-import pdfminer ^
  --hidden-import pdfminer.high_level ^
  --hidden-import pdfminer.layout ^
  tangerino_v3.py

if errorlevel 1 ( echo ERRO: PyInstaller falhou. && pause && exit /b 1 )

echo [3/3] Limpando arquivos temporarios de build...
rmdir /s /q build 2>nul
del /q TangerinoV3PRO.spec 2>nul

echo.
echo ============================================================
echo   Pronto! Pasta portavel em:
echo   %~dp0dist\TangerinoV3PRO\
echo.
echo   Compacte essa pasta em .zip e compartilhe.
echo   Na 1a abertura, o Chromium sera baixado automaticamente.
echo ============================================================
echo.
pause
