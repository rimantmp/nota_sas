@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo .venv belum ada. Jalankan install.bat terlebih dahulu.
  echo.
  pause
  exit /b 1
)
echo Menjalankan Sistem Nota ...
echo Browser akan terbuka otomatis. Jangan tutup jendela ini selama memakai aplikasi.
".venv\Scripts\python.exe" run.py
pause
